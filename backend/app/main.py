from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.triangulation_routes import router as triangulation_router
from app.api.metadata_routes import router as metadata_router


app = FastAPI(
    title="OSINT Platform API",
    description="API for OSINT data collection and analysis with Identity Triangulation",
    version="2.0.0"
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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "osint-platform"}
