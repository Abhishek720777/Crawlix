import asyncio
import socket
import datetime
from celery.utils.log import get_task_logger
from sqlalchemy import update, func
from app.workers.celery_app import celery_app
from app.core.database import SyncSessionLocal
from app.models.models import CrawlJob, ScrapedRecord
from app.services.crawler_engine import crawler_engine
from app.workers.tasks_intelligence import generate_job_intelligence

logger = get_task_logger(__name__)


@celery_app.task(name="app.workers.tasks_scrape.orchestrate_job", bind=True)
def orchestrate_job(self, job_id: str):
    """Entrypoint: reads job, marks running, dispatches one subtask per seed URL."""
    logger.info(f"[Orchestrator] Starting crawl job {job_id}")
    session = SyncSessionLocal()
    try:
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            logger.error(f"[Orchestrator] Job {job_id} not found.")
            return

        seed_urls = job.target_urls or []
        total_urls = len(seed_urls)

        if total_urls == 0:
            logger.warning(f"[Orchestrator] Job {job_id} has no target URLs – marking failed.")
            session.execute(
                update(CrawlJob).where(CrawlJob.id == job_id).values(status="failed")
            )
            session.commit()
            return

        # Mark running + set pending_tasks = number of seed URLs being dispatched
        session.execute(
            update(CrawlJob).where(CrawlJob.id == job_id).values(
                status="running",
                started_at=datetime.datetime.now(datetime.timezone.utc),
                pending_tasks=total_urls
            )
        )
        session.commit()

        logger.info(f"[Orchestrator] Dispatching {total_urls} seed URLs for job {job_id}")
        for url in seed_urls:
            execute_crawl_page.delay(
                job_id=job.id,
                url=url,
                crawler_type=job.crawler_type,
                custom_selectors=job.css_selectors,
                depth=0,        # Seeds start at 0; max_depth=1 means follow 1 level of links
                max_depth=job.max_depth,
                max_pages=job.max_pages,
            )

    except Exception as e:
        logger.exception(f"[Orchestrator] Error setting up job {job_id}: {e}")
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
                        custom_selectors: dict = None, depth: int = 0,
                        max_depth: int = 1, max_pages: int = 50):
    """Scrapes a single URL, saves a record, spawns child tasks if depth allows."""
    worker_hostname = socket.gethostname()
    logger.info(f"[{worker_hostname}] Scraping: {url}  (depth {depth}/{max_depth})")

    # -- 1. Fetch page (async inside sync Celery task) --
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        fetch_res = loop.run_until_complete(crawler_engine.fetch_page(url))
    except Exception as e:
        logger.exception(f"Fetch failed for {url}: {e}")
        fetch_res = {"url": url, "status_code": 0, "html": "", "response_time_ms": 0.0, "error": str(e)}
    finally:
        loop.close()

    session = SyncSessionLocal()
    children_spawned = 0
    try:
        # -- 2. Guard: bail out if job was cancelled/paused/completed --
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            logger.warning(f"Job {job_id} not found, aborting task for {url}")
            return
        if job.status in ("cancelled", "paused", "failed", "completed"):
            logger.info(f"Job {job_id} is '{job.status}' — skipping {url}")
            # Still need to decrement pending_tasks even on early exit
            _decrement_and_maybe_complete(job_id, session, max_pages)
            return

        # -- 3. Handle fetch error --
        if fetch_res.get("error"):
            logger.warning(f"[{worker_hostname}] Fetch error for {url}: {fetch_res['error']}")
            session.execute(
                update(CrawlJob).where(CrawlJob.id == job_id).values(
                    errors_count=CrawlJob.errors_count + 1
                )
            )
            session.commit()
            _decrement_and_maybe_complete(job_id, session, max_pages)
            return

        # -- 4. Parse extracted data --
        parsed = crawler_engine.parse_page(
            url=fetch_res["url"],
            html=fetch_res["html"],
            crawler_type=crawler_type,
            custom_selectors=custom_selectors
        )

        # -- 5. Save scraped record --
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

        # Atomic counter increment
        session.execute(
            update(CrawlJob).where(CrawlJob.id == job_id).values(
                pages_crawled=CrawlJob.pages_crawled + 1,
                records_extracted=CrawlJob.records_extracted + 1,
            )
        )
        session.commit()

        # Refresh to get latest pages_crawled after increment
        session.refresh(job)
        logger.info(f"[{worker_hostname}] Saved record for {url} | job pages: {job.pages_crawled}/{max_pages}")

        # -- 6. Spawn child tasks if depth allows and we haven't hit max_pages --
        if depth < max_depth and job.pages_crawled < max_pages:
            # Take up to 5 links but don't exceed remaining page budget
            remaining = max_pages - job.pages_crawled
            discovered = parsed.get("discovered_links", [])[:min(5, remaining)]
            if discovered:
                # Atomically reserve pending_tasks slots for children BEFORE dispatching
                session.execute(
                    update(CrawlJob).where(CrawlJob.id == job_id).values(
                        pending_tasks=CrawlJob.pending_tasks + len(discovered)
                    )
                )
                session.commit()
                children_spawned = len(discovered)
                for child_url in discovered:
                    execute_crawl_page.delay(
                        job_id=job_id,
                        url=child_url,
                        crawler_type=crawler_type,
                        custom_selectors=custom_selectors,
                        depth=depth + 1,
                        max_depth=max_depth,
                        max_pages=max_pages,
                    )
                logger.info(f"[{worker_hostname}] Spawned {children_spawned} children at depth {depth+1} | budget left: {remaining}")

    except Exception as e:
        try:
            session.rollback()
        except Exception:
            pass
        logger.exception(f"[{worker_hostname}] Error processing {url} for job {job_id}: {e}")
    finally:
        session.close()

    # -- 7. Decrement this task from pending_tasks, complete job if all tasks done --
    _decrement_and_maybe_complete(job_id, SyncSessionLocal(), max_pages)


def _decrement_and_maybe_complete(job_id: str, session, max_pages: int):
    """
    Atomically decrement pending_tasks. If it reaches 0 (all tasks done)
    OR if records_extracted >= max_pages, mark the job as completed.
    """
    try:
        # Decrement pending_tasks atomically (floor at 0)
        session.execute(
            update(CrawlJob)
            .where(CrawlJob.id == job_id, CrawlJob.pending_tasks > 0)
            .values(pending_tasks=CrawlJob.pending_tasks - 1)
        )
        session.commit()

        # Read latest state
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job or job.status != "running":
            return

        # Count actual DB records for accuracy
        actual_count = session.query(func.count(ScrapedRecord.id)).filter(
            ScrapedRecord.job_id == job_id
        ).scalar() or 0

        should_complete = (
            actual_count >= max_pages          # Hit page limit
            or job.pending_tasks <= 0           # All dispatched tasks finished
        )

        if should_complete:
            session.execute(
                update(CrawlJob).where(CrawlJob.id == job_id).values(
                    status="completed",
                    completed_at=datetime.datetime.now(datetime.timezone.utc),
                    records_extracted=actual_count,
                    pages_crawled=actual_count,
                    pending_tasks=0
                )
            )
            session.commit()
            logger.info(f"[Completion] Job {job_id} completed — {actual_count} records extracted.")
            # Fire intelligence post-processor
            generate_job_intelligence.delay(job_id=job_id)

    except Exception as e:
        logger.error(f"[_decrement_and_maybe_complete] Error for job {job_id}: {e}")
        try:
            session.rollback()
        except Exception:
            pass
    finally:
        try:
            session.close()
        except Exception:
            pass
