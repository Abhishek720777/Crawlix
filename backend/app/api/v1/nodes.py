import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.models import User, WorkerNode
from app.schemas.schemas import WorkerNodeResponse

router = APIRouter(prefix="/nodes", tags=["Worker Mesh Telemetry"])

@router.get("", response_model=List[WorkerNodeResponse])
async def list_worker_nodes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(WorkerNode).order_by(WorkerNode.last_heartbeat.desc())
    result = await db.execute(query)
    nodes = result.scalars().all()
    return nodes
