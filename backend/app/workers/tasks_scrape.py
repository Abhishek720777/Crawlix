import asyncio
import socket
import datetime
from celery.utils.log import get_task_logger
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

        job.status = "running"
        job.started_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()

        # Dispatch parallel tasks to worker pool
        for target_url in job.target_urls:
            execute_crawl_page.delay(
                job_id=job.id,
                url=target_url,
                crawler_type=job.crawler_type,
                custom_selectors=job.css_selectors,
                depth=1,
                max_depth=job.max_depth
            )
            
    except Exception as e:
        logger.exception(f"Error orchestrating job {job_id}: {e}")
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job:
            job.status = "failed"
            session.commit()
    finally:
        session.close()


@celery_app.task(name="app.workers.tasks_scrape.execute_crawl_page", bind=True, max_retries=3)
def execute_crawl_page(self, job_id: str, url: str, crawler_type: str, custom_selectors: dict = None, depth: int = 1, max_depth: int = 1):
    """Executes single URL scrape asynchronously on distributed node"""
    worker_hostname = socket.gethostname()
    logger.info(f"[{worker_hostname}] Scraping {url} (Depth: {depth}/{max_depth})")

    # Async runner inside sync Celery task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        fetch_res = loop.run_until_complete(crawler_engine.fetch_page(url))
    finally:
        loop.close()

    session = SyncSessionLocal()
    try:
        job = session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job or job.status in ("cancelled", "paused"):
            return

        if fetch_res.get("error"):
            job.errors_count += 1
            session.commit()
            logger.warning(f"Failed to fetch {url}: {fetch_res['error']}")
            return

        # Parse data
        parsed = crawler_engine.parse_page(
            url=fetch_res["url"],
            html=fetch_res["html"],
            crawler_type=crawler_type,
            custom_selectors=custom_selectors
        )

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

        job.pages_crawled += 1
        job.records_extracted += 1
        
        has_spawned_subtasks = False
        # Follow links if depth allows and limit not reached
        if depth < max_depth and job.pages_crawled < job.max_pages:
            discovered = parsed.get("discovered_links", [])[:3]
            for next_link in discovered:
                has_spawned_subtasks = True
                execute_crawl_page.delay(
                    job_id=job_id,
                    url=next_link,
                    crawler_type=crawler_type,
                    custom_selectors=custom_selectors,
                    depth=depth + 1,
                    max_depth=max_depth
                )

        # Trigger completion when max_pages reached OR no more links to crawl at max depth
        if job.pages_crawled >= job.max_pages or (depth >= max_depth and not has_spawned_subtasks):
            job.status = "completed"
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            generate_job_intelligence.delay(job_id=job.id)

        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(f"Error persisting record for {url}: {e}")
    finally:
        session.close()
