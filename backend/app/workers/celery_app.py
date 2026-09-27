from celery import Celery
from kombu import Queue, Exchange
from app.core.config import settings

celery_app = Celery(
    "crawlix_worker_mesh",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks_scrape",
        "app.workers.tasks_intelligence",
        "app.workers.tasks_telemetry"
    ]
)

# Distributed Task Routing configuration
default_exchange = Exchange("crawlix_exchange", type="direct")

celery_app.conf.task_queues = (
    Queue("high_priority", default_exchange, routing_key="high_priority"),
    Queue("scraping_pool", default_exchange, routing_key="scraping_pool"),
    Queue("ai_analysis", default_exchange, routing_key="ai_analysis"),
)

celery_app.conf.task_default_queue = "scraping_pool"
celery_app.conf.task_default_exchange = "crawlix_exchange"
celery_app.conf.task_default_routing_key = "scraping_pool"

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,  # Fair task distribution
    task_acks_late=True,          # Ensure tasks are re-assigned if a worker crashes
    task_routes={
        "app.workers.tasks_scrape.execute_crawl_page": {"queue": "scraping_pool"},
        "app.workers.tasks_scrape.orchestrate_job": {"queue": "high_priority"},
        "app.workers.tasks_intelligence.generate_job_intelligence": {"queue": "ai_analysis"},
        "app.workers.tasks_telemetry.report_worker_heartbeat": {"queue": "high_priority"},
    },
    beat_schedule={
        "worker-heartbeat-every-30-seconds": {
            "task": "app.workers.tasks_telemetry.report_worker_heartbeat",
            "schedule": 30.0,
        },
    }
)
