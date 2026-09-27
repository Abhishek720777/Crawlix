import socket
import datetime
import psutil
from celery.utils.log import get_task_logger
from app.workers.celery_app import celery_app
from app.core.database import SyncSessionLocal
from app.models.models import WorkerNode

logger = get_task_logger(__name__)

@celery_app.task(name="app.workers.tasks_telemetry.report_worker_heartbeat")
def report_worker_heartbeat():
    """Periodic worker heartbeat recording CPU, RAM, and concurrency metrics in DB"""
    hostname = socket.gethostname()
    node_id = f"node-{hostname}"
    
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent

    session = SyncSessionLocal()
    try:
        node = session.query(WorkerNode).filter(WorkerNode.id == node_id).first()
        if not node:
            node = WorkerNode(
                id=node_id,
                hostname=hostname,
                ip_address=socket.gethostbyname(hostname) if hasattr(socket, 'gethostbyname') else "127.0.0.1",
                status="active",
                concurrency=psutil.cpu_count() or 4,
                cpu_usage=cpu,
                memory_usage=mem,
                last_heartbeat=datetime.datetime.now(datetime.timezone.utc)
            )
            session.add(node)
        else:
            node.status = "active"
            node.cpu_usage = cpu
            node.memory_usage = mem
            node.last_heartbeat = datetime.datetime.now(datetime.timezone.utc)

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to record node heartbeat: {e}")
    finally:
        session.close()
