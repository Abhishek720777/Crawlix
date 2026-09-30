from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import async_engine, Base
import app.models.models  # Crucial: Import models so SQLAlchemy Base knows about table definitions
from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.data import router as data_router
from app.api.v1.nodes import router as nodes_router
from app.api.v1.websockets import router as ws_router

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry connecting to PostgreSQL on startup until ready
    for attempt in range(10):
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Idempotent migration: add pending_tasks if not already present
                await conn.execute(text(
                    "ALTER TABLE crawl_jobs ADD COLUMN IF NOT EXISTS pending_tasks INTEGER DEFAULT 0"
                ))
            logger.info("Successfully connected to PostgreSQL and applied schema migrations.")
            break
        except Exception as e:
            logger.warning(f"Waiting for database connection... (Attempt {attempt+1}/10): {e}")
            await asyncio.sleep(2)
    yield

app = FastAPI(
    title="Crawlix API Gateway",
    description="Distributed Web Scraping & Intelligence Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https:\/\/.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware (skip OPTIONS preflight)
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    if request.method != "OPTIONS":
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Register API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(data_router, prefix="/api/v1")
app.include_router(nodes_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Crawlix API Gateway",
        "environment": settings.ENVIRONMENT
    }
