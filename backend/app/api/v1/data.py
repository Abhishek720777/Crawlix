import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.models import User, CrawlJob, ScrapedRecord, IntelligenceReport
from app.schemas.schemas import ScrapedRecordResponse, IntelligenceReportResponse

router = APIRouter(prefix="/data", tags=["Data & Intelligence Explorer"])

@router.get("/records", response_model=List[ScrapedRecordResponse])
async def list_records(
    job_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(ScrapedRecord).join(CrawlJob).where(CrawlJob.owner_id == current_user.id)
    if job_id:
        query = query.where(ScrapedRecord.job_id == job_id)
    query = query.order_by(ScrapedRecord.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/intelligence/{job_id}", response_model=List[IntelligenceReportResponse])
async def get_job_intelligence(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(IntelligenceReport).join(CrawlJob).where(
        CrawlJob.id == job_id, CrawlJob.owner_id == current_user.id
    ).order_by(IntelligenceReport.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/export")
async def export_data(
    job_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    job_query = select(CrawlJob).where(CrawlJob.id == job_id, CrawlJob.owner_id == current_user.id)
    job_res = await db.execute(job_query)
    job = job_res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    records_query = select(ScrapedRecord).where(ScrapedRecord.job_id == job_id).order_by(ScrapedRecord.created_at.asc())
    records_res = await db.execute(records_query)
    records = records_res.scalars().all()

    if format == "json":
        data = [
            {
                "id": r.id,
                "url": r.url,
                "http_status": r.http_status,
                "response_time_ms": r.response_time_ms,
                "page_title": r.page_title,
                "structured_data": r.structured_data,
                "worker_node": r.worker_node,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
        json_str = json.dumps(data, indent=2)
        return StreamingResponse(
            io.StringIO(json_str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=crawlix_job_{job_id}.json"}
        )

    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "URL", "HTTP_Status", "Response_Time_MS", "Page_Title", "Structured_Data_JSON", "Worker_Node", "Created_At"])
        for r in records:
            writer.writerow([
                r.id,
                r.url,
                r.http_status,
                r.response_time_ms,
                r.page_title or "",
                json.dumps(r.structured_data or {}),
                r.worker_node,
                r.created_at.isoformat() if r.created_at else ""
            ])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=crawlix_job_{job_id}.csv"}
        )
