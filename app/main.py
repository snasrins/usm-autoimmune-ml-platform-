"""
USM Autoimmune ML Platform - FastAPI Application Entry Point
Data Engineer: Syarifah Fajriyah
ML Engineer: Iznie Humaiera
"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
from contextlib import asynccontextmanager

# Optional imports for ML features
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from app.core.config import settings
from app.core.database import engine, Base

# Security Middleware (Sprint 3 - Production Readiness)
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.audit_logger import AuditLoggingMiddleware

# Import endpoint modules directly (bypasses __init__.py circular import issue)
import app.api.endpoints.auth as auth
import app.api.endpoints.predict as predict
import app.api.endpoints.inference as inference
import app.api.endpoints.explainability as explainability
import app.api.endpoints.scorecard as scorecard
import app.api.endpoints.upload as upload
import app.api.endpoints.admin as admin
import app.api.endpoints.api_keys as api_keys
import app.api.endpoints.patients as patients
import app.api.endpoints.unstructured as unstructured
import app.api.endpoints.eda as eda
import app.api.endpoints.dataset_versions as dataset_versions
import app.api.endpoints.flexible_preview as flexible_preview
import app.api.endpoints.preview as preview
import app.api.endpoints.labeling as labeling
import app.api.endpoints.training as training
import app.api.endpoints.ml_features as ml_features
import app.api.endpoints.ml_utils as ml_utils
import app.api.endpoints.data_quality as data_quality
import app.api.endpoints.insights as insights
import app.api.endpoints.category_management as category_management
import app.api.endpoints.notifications as notifications

# Ensure OcrJob table is registered with Base before create_all
from app.models.ocr_job import OcrJob as _OcrJob  # noqa: F401

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: kick off Gemma background pre-load
    try:
        from app.services.gemma_conversational_service import start_gemma_preload
        start_gemma_preload()
    except Exception as _e:
        import logging
        logging.getLogger(__name__).warning(f"Could not pre-load Gemma: {_e}")
    yield
    # Shutdown: nothing to clean up


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Hybrid ML Platform for Autoimmune Disease Registry - Universiti Sains Malaysia",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration - Restrict to Tailscale VPN only
allowed_origins = [
    f"http://{settings.TAILSCALE_IP}:8000",
    f"https://{settings.TAILSCALE_IP}:8000",
    f"http://{settings.TAILSCALE_IP}:8001",
    f"https://{settings.TAILSCALE_IP}:8001",
    "http://localhost:8000",  # For development only
    "http://localhost:8001",  # Backend dev server
    "http://localhost:3000",  # Frontend dev server (Vite)
    "http://localhost:3001",  # Frontend dev server (Vite alternative port)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security Middleware (Sprint 3 - Production Readiness)
app.add_middleware(RateLimitMiddleware)  # Rate limiting
app.add_middleware(AuditLoggingMiddleware)  # Audit logging

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(predict.router, prefix=f"{settings.API_V1_STR}/predict", tags=["ML Prediction (Legacy)"])

# ML Training endpoints (NEW)
app.include_router(training.router, prefix=f"{settings.API_V1_STR}/ml", tags=["ML Training"])

# ML Inference endpoints (USMA-46 - Load trained models from MinIO)
app.include_router(inference.router, prefix=f"{settings.API_V1_STR}/ml", tags=["ML Inference"])

# ML Explainability & Conversational AI (USMA-50 - SHAP + Gemma-4-E4B)
app.include_router(explainability.router, prefix=f"{settings.API_V1_STR}/ml", tags=["ML Explainability & AI Assistant"])

# Scorecard & Model Comparison (USMA-47 + USMA-43)
app.include_router(scorecard.router, prefix=f"{settings.API_V1_STR}/ml", tags=["Clinical Scorecard & Model Comparison"])

# Feature Engineering endpoints
app.include_router(ml_features.router, prefix=f"{settings.API_V1_STR}/ml", tags=["Feature Engineering"])

# Phase 3: Data Quality & Insights (NEW)
app.include_router(data_quality.router, prefix=f"{settings.API_V1_STR}/data-quality", tags=["Data Quality"])
app.include_router(insights.router, prefix=f"{settings.API_V1_STR}/ml", tags=["ML Insights"])

# Data Ingestion - NEW flexible workflow (primary)
app.include_router(flexible_preview.router, prefix=f"{settings.API_V1_STR}/flexible", tags=["Flexible Data Pipeline"])

# Layer 5 Preprocessing & ML Validation
app.include_router(preview.router, prefix=f"{settings.API_V1_STR}", tags=["Layer 5 Preprocessing"])

# Label Assignment (Critical for ML Training)
app.include_router(labeling.router, prefix=f"{settings.API_V1_STR}", tags=["Label Assignment"])

# ML Utilities (Schema Validation, Provenance, Bridge Service)
app.include_router(ml_utils.router, prefix=f"{settings.API_V1_STR}", tags=["ML Utilities"])

# Legacy endpoints (keep for backward compatibility)
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["Data Ingestion (Legacy)"])

app.include_router(patients.router, prefix=f"{settings.API_V1_STR}/patients", tags=["Patient Data"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Administration"])

# Security & API Key Management (Sprint 3)
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/admin", tags=["API Key Management"])

# Category Management (Dynamic Disease Categories)
app.include_router(category_management.router, prefix=f"{settings.API_V1_STR}/categories", tags=["Category Management"])

app.include_router(unstructured.router, prefix=f"{settings.API_V1_STR}/unstructured", tags=["Unstructured Pipeline"])
app.include_router(eda.router, prefix=f"{settings.API_V1_STR}/eda", tags=["EDA & Preprocessing"])
app.include_router(dataset_versions.router, prefix=f"{settings.API_V1_STR}/dataset-versions", tags=["Dataset Versioning"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notifications"])


# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for Docker healthcheck and monitoring
    """
    gpu_available = False
    gpu_name = None
    
    if TORCH_AVAILABLE:
        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": "production" if settings.ETHICS_CLEARANCE_RECEIVED else "development",
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "ml_features": TORCH_AVAILABLE
    }


# Root endpoint
@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "USM Autoimmune ML Platform API",
        "project": "Hybrid ML Platform for Autoimmune Disease Registry",
        "client": "Universiti Sains Malaysia (USM)",
        "vendor": "Aras Integrasi",
        "data_engineer": "Syarifah Fajriyah",
        "ml_engineer": "Iznie Humaiera",
        "api_docs": f"http://{settings.TAILSCALE_IP}:8000/docs",
        "health_check": f"http://{settings.TAILSCALE_IP}:8000/health",
        "api_endpoints": {
            "authentication": f"{settings.API_V1_STR}/auth",
            "predictions": f"{settings.API_V1_STR}/predict",
            "uploads": f"{settings.API_V1_STR}/upload",
            "admin": f"{settings.API_V1_STR}/admin"
        },
        "sprint": "Sprint 1 - Complete",
        "status": "Operational - Ready for ML Inference"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Bind to all interfaces inside container (Docker handles Tailscale binding)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
