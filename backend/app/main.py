from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from contextlib import asynccontextmanager
import redis.asyncio as redis

from app.api.routes import router
from app.api.triangulation_routes import router as triangulation_router
from app.api.metadata_routes import router as metadata_router
from app.api.osint_framework_routes import router as osint_framework_router
from app.routers.scan import router as scan_router
from app.routers.websocket import router as websocket_router
from app.routers.history import router as history_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes FastAPILimiter with Redis and creates database tables.
    """
    # Startup: Initialize Redis rate limiter
    redis_connection = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)
    
    # Startup: Initialize database tables
    init_db()
    
    print("✓ Rate limiter initialized with Redis")
    print("✓ Database tables created/verified")
    
    yield
    
    # Shutdown: Close Redis connection
    await redis_connection.close()
    print("✓ Rate limiter shutdown complete")


app = FastAPI(
    title="OSINT Platform API",
    description="API for OSINT data collection and analysis with Identity Triangulation, Async Task Queue, Real-time WebSocket Notifications, Credits-based Rate Limiting, and Complete Audit Trail",
    version="2.4.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(triangulation_router, prefix="/api/v1")
app.include_router(metadata_router, prefix="/api/v1/metadata", tags=["metadata"])
app.include_router(osint_framework_router, prefix="/api/v1/osint-framework", tags=["osint-framework"])
app.include_router(scan_router, prefix="/api/v1", tags=["async-scans"])
app.include_router(websocket_router, tags=["websockets"])
app.include_router(history_router, prefix="/api/v1", tags=["history"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "osint-platform", "version": "2.3.0"}
