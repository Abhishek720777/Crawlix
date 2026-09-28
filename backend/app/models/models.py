from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    jobs = relationship("CrawlJob", back_populates="owner", cascade="all, delete-orphan")


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    target_urls = Column(JSON, nullable=False)  # List of URLs
    crawler_type = Column(String(50), default="generic")  # generic, ecommerce, news, schema
    priority = Column(String(20), default="normal")  # low, normal, high
    max_depth = Column(Integer, default=1)
    max_pages = Column(Integer, default=50)
    rate_limit_rps = Column(Float, default=2.0)
    css_selectors = Column(JSON, nullable=True)  # Custom CSS selector mapping { "title": "h1", "price": ".price" }
    status = Column(String(30), default="pending")  # pending, running, paused, completed, failed, cancelled
    
    pages_crawled = Column(Integer, default=0)
    records_extracted = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    pending_tasks = Column(Integer, default=0)  # Tracks live Celery subtasks; 0 = all done
    
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="jobs")
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    records = relationship("ScrapedRecord", back_populates="job", cascade="all, delete-orphan")
    intelligence_reports = relationship("IntelligenceReport", back_populates="job", cascade="all, delete-orphan")


class ScrapedRecord(Base):
    __tablename__ = "scraped_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("crawl_jobs.id"), nullable=False)
    url = Column(Text, nullable=False)
    http_status = Column(Integer, default=200)
    response_time_ms = Column(Float, default=0.0)
    
    # Payload
    page_title = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)  # Extracted fields
    raw_html_snippet = Column(Text, nullable=True)
    worker_node = Column(String(100), default="worker-1")
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    job = relationship("CrawlJob", back_populates="records")


class IntelligenceReport(Base):
    __tablename__ = "intelligence_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("crawl_jobs.id"), nullable=False)
    report_type = Column(String(50), nullable=False)  # pricing_trends, sentiment_analysis, topic_distribution
    metrics = Column(JSON, nullable=False)  # Aggregated insights
    summary_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    job = relationship("CrawlJob", back_populates="intelligence_reports")


class WorkerNode(Base):
    __tablename__ = "worker_nodes"

    id = Column(String(100), primary_key=True)  # e.g., worker-node-us-east-1
    hostname = Column(String(200), nullable=True)
    ip_address = Column(String(100), nullable=True)
    status = Column(String(30), default="active")  # active, idle, offline
    concurrency = Column(Integer, default=4)
    active_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    last_heartbeat = Column(DateTime(timezone=True), default=utc_now)
