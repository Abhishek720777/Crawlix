from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import async_engine, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.data import router as data_router
from app.api.v1.nodes import router as nodes_router
from app.api.v1.websockets import router as ws_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Crawlix API Gateway",
    description="Distributed Web Scraping & Intelligence Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
