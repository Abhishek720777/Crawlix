from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# User Schemas
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserRegister":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Job Schemas
class CrawlJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target_urls: List[str] = Field(..., min_items=1)
    crawler_type: str = Field(default="generic", description="generic | ecommerce | news | schema")
    priority: str = Field(default="normal", description="low | normal | high")
    max_depth: int = Field(default=1, ge=1, le=5)
    max_pages: int = Field(default=50, ge=1, le=1000)
    rate_limit_rps: float = Field(default=2.0, ge=0.1, le=20.0)
    css_selectors: Optional[Dict[str, str]] = None

class CrawlJobUpdate(BaseModel):
    status: Optional[str] = None
    rate_limit_rps: Optional[float] = None

class CrawlJobResponse(BaseModel):
    id: str
    name: str
    target_urls: List[str]
    crawler_type: str
    priority: str
    max_depth: int
    max_pages: int
    rate_limit_rps: float
    css_selectors: Optional[Dict[str, str]]
    status: str
    pages_crawled: int
    records_extracted: int
    errors_count: int
    owner_id: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Record Schemas
class ScrapedRecordResponse(BaseModel):
    id: str
    job_id: str
    url: str
    http_status: int
    response_time_ms: float
    page_title: Optional[str]
    structured_data: Optional[Dict[str, Any]]
    worker_node: str
    created_at: datetime

    class Config:
        from_attributes = True


# Intelligence Schemas
class IntelligenceReportResponse(BaseModel):
    id: str
    job_id: str
    report_type: str
    metrics: Dict[str, Any]
    summary_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Worker Node Schemas
class WorkerNodeResponse(BaseModel):
    id: str
    hostname: Optional[str]
    ip_address: Optional[str]
    status: str
    concurrency: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    cpu_usage: float
    memory_usage: float
    last_heartbeat: datetime

    class Config:
        from_attributes = True
