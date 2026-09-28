import asyncio
import socket
import datetime
from celery.utils.log import get_task_logger
from sqlalchemy import update, func, select
from app.workers.celery_app import celery_app
from app.core.database import SyncSessionLocal
from app.models.models import CrawlJob, ScrapedRecord
from app.services.crawler_engine import crawler_engine
from app.workers.tasks_intelligence import generate_job_intelligence

logger = get_task_logger(__name__)


@celery_app.task(name="app.workers.tasks_scrape.orchestrate_job", bind=True)
def orchestrate_job(self, job_id: str):
    """Entrypoint orchestrator: reads job URLs and dispatches distributed subtasks"""
    logger.info(f"[Orchestrator] Starting crawl job {job_id}")
    session = SyncSessionLocal()
    try:
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Mark job as running
        session.execute(
            update(CrawlJob).where(CrawlJob.id == job_id).values(
                status="running",
                started_at=datetime.datetime.now(datetime.timezone.utc)
            )
        )
        session.commit()

        total_urls = len(job.target_urls or [])
        logger.info(f"[Orchestrator] Dispatching {total_urls} seed URLs for job {job_id}")

        # Dispatch all seed URLs as parallel subtasks
        for target_url in (job.target_urls or []):
            execute_crawl_page.delay(
                job_id=job.id,
                url=target_url,
                crawler_type=job.crawler_type,
                custom_selectors=job.css_selectors,
                depth=1,
                max_depth=job.max_depth,
                max_pages=job.max_pages,
                total_seed_urls=total_urls
            )

    except Exception as e:
        logger.exception(f"Error orchestrating job {job_id}: {e}")
        try:
            session.execute(
                update(CrawlJob).where(CrawlJob.id == job_id).values(status="failed")
            )
            session.commit()
        except Exception:
            pass
    finally:
        session.close()


@celery_app.task(name="app.workers.tasks_scrape.execute_crawl_page", bind=True, max_retries=2, default_retry_delay=5)
def execute_crawl_page(self, job_id: str, url: str, crawler_type: str,
                        custom_selectors: dict = None, depth: int = 1,
                        max_depth: int = 1, max_pages: int = 50, total_seed_urls: int = 1):
    """Executes single URL scrape on a distributed node"""
    worker_hostname = socket.gethostname()
    logger.info(f"[{worker_hostname}] Scraping: {url} (depth {depth}/{max_depth})")

    # Run async fetch in a new event loop (Celery tasks are sync)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        fetch_res = loop.run_until_complete(crawler_engine.fetch_page(url))
    except Exception as e:
        logger.exception(f"Failed to fetch {url}: {e}")
        fetch_res = {"url": url, "status_code": 0, "html": "", "response_time_ms": 0.0, "error": str(e)}
    finally:
        loop.close()

    session = SyncSessionLocal()
    try:
        # Check if job is still in a runnable state
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job or job.status in ("cancelled", "paused", "failed", "completed"):
            logger.info(f"Job {job_id} is in status '{job.status if job else 'not found'}' – skipping {url}")
            return

        if fetch_res.get("error"):
            # Atomically increment errors_count
            session.execute(
                update(CrawlJob).where(CrawlJob.id == job_id).values(
                    errors_count=CrawlJob.errors_count + 1
                )
            )
            session.commit()
            logger.warning(f"Failed to fetch {url}: {fetch_res['error']}")
            _maybe_complete_job(job_id, session)
            return

        # Parse extracted intelligence
        parsed = crawler_engine.parse_page(
            url=fetch_res["url"],
            html=fetch_res["html"],
            crawler_type=crawler_type,
            custom_selectors=custom_selectors
        )

        # Save scraped record
        record = ScrapedRecord(
            job_id=job_id,
            url=fetch_res["url"],
            http_status=fetch_res["status_code"],
            response_time_ms=fetch_res["response_time_ms"],
            page_title=parsed["title"],
            structured_data=parsed["data"],
            worker_node=worker_hostname
        )
        session.add(record)

        # Atomically increment pages_crawled and records_extracted
        session.execute(
            update(CrawlJob).where(CrawlJob.id == job_id).values(
                pages_crawled=CrawlJob.pages_crawled + 1,
                records_extracted=CrawlJob.records_extracted + 1
            )
        )
        session.commit()

        # Refresh job to get latest counts
        session.refresh(job)
        logger.info(f"[{worker_hostname}] Saved record for {url} (job pages: {job.pages_crawled}/{job.max_pages})")

        # Spawn child links if depth allows and page limit not reached
        if depth < max_depth and job.pages_crawled < max_pages:
            discovered = parsed.get("discovered_links", [])[:3]
            for next_link in discovered:
                execute_crawl_page.delay(
                    job_id=job_id,
                    url=next_link,
                    crawler_type=crawler_type,
                    custom_selectors=custom_selectors,
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_pages=max_pages,
                    total_seed_urls=total_seed_urls
                )

        # Check completion after each page is processed
        _maybe_complete_job(job_id, session)

    except Exception as e:
        try:
            session.rollback()
        except Exception:
            pass
        logger.exception(f"Error processing {url} for job {job_id}: {e}")
    finally:
        session.close()


def _maybe_complete_job(job_id: str, session):
    """Check if a job should be marked as completed based on actual DB record count"""
    try:
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job or job.status != "running":
            return

        # Count actual records stored in DB for this job
        actual_count = session.query(func.count(ScrapedRecord.id)).filter(
            ScrapedRecord.job_id == job_id
        ).scalar() or 0

        # Complete when we've hit the max pages limit
        if actual_count >= job.max_pages:
            session.execute(
                update(CrawlJob).where(CrawlJob.id == job_id).values(
                    status="completed",
                    completed_at=datetime.datetime.now(datetime.timezone.utc),
                    records_extracted=actual_count,
                    pages_crawled=actual_count
                )
            )
            session.commit()
            logger.info(f"[Completion] Job {job_id} completed with {actual_count} records.")
            generate_job_intelligence.delay(job_id=job_id)

    except Exception as e:
        logger.error(f"Error checking job completion for {job_id}: {e}")
