import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.models import User, CrawlJob, ScrapedRecord, IntelligenceReport
from app.schemas.schemas import CrawlJobCreate, CrawlJobResponse, CrawlJobUpdate
from app.workers.tasks_scrape import orchestrate_job

router = APIRouter(prefix="/jobs", tags=["Crawl Jobs"])

@router.post("", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: CrawlJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_job = CrawlJob(
        name=job_in.name,
        target_urls=job_in.target_urls,
        crawler_type=job_in.crawler_type,
        priority=job_in.priority,
        max_depth=job_in.max_depth,
        max_pages=job_in.max_pages,
        rate_limit_rps=job_in.rate_limit_rps,
        css_selectors=job_in.css_selectors,
        status="pending",
        owner_id=current_user.id
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # Dispatch Celery Orchestrator
    try:
        orchestrate_job.delay(job_id=new_job.id)
    except Exception:
        # Fallback if Celery/Redis is running in dry-run/local mode
        pass

    return new_job


@router.get("", response_model=List[CrawlJobResponse])
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(CrawlJob).where(CrawlJob.owner_id == current_user.id).order_by(CrawlJob.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{job_id}", response_model=CrawlJobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(CrawlJob).where(CrawlJob.id == job_id, CrawlJob.owner_id == current_user.id)
    result = await db.execute(query)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/action")
async def control_job(
    job_id: str,
    action: str,  # pause, resume, cancel, retry
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(CrawlJob).where(CrawlJob.id == job_id, CrawlJob.owner_id == current_user.id)
    result = await db.execute(query)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if action == "pause":
        job.status = "paused"
    elif action == "resume":
        job.status = "running"
    elif action == "cancel":
        job.status = "cancelled"
    elif action == "retry":
        job.status = "pending"
        job.pages_crawled = 0
        job.records_extracted = 0
        job.errors_count = 0
        job.started_at = None
        job.completed_at = None
        try:
            orchestrate_job.delay(job_id=job.id)
        except Exception:
            pass
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    await db.commit()
    await db.refresh(job)
    return {"message": f"Job {job_id} status set to {job.status}", "status": job.status}
