"""
AI Android Learning Monitoring System - FastAPI Backend
Entry point for the application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.config import settings
from app.database import prisma
from app.routes import (
    auth_router,
    courses_router,
    assignments_router,
    sessions_router,
    projects_router,
    analysis_router,
    roles_router,
    ml_analysis_router,
    ml_training_router,
)
from app.websocket.manager import router as websocket_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting application", env=settings.ENVIRONMENT)
    await prisma.connect()
    logger.info("Database connected")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await prisma.disconnect()
    logger.info("Database disconnected")


# Initialize FastAPI app
app = FastAPI(
    title="AI Android Learning Monitoring System",
    description="Backend API for Android learning with AI-powered feedback",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected" if prisma.is_connected() else "disconnected",
    }

# API routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(courses_router, prefix="/api/courses", tags=["Courses"])
app.include_router(assignments_router, prefix="/api/assignments", tags=["Assignments"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["Learning Sessions"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["Code Analysis"])
app.include_router(roles_router, prefix="/api/roles", tags=["Roles"])
app.include_router(ml_analysis_router, prefix="/api/ml-analysis", tags=["ML Analysis for Android Studio"])
app.include_router(ml_training_router, prefix="/api/ml-training", tags=["ML Training Dashboard"])

# WebSocket
app.include_router(websocket_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Android Learning Monitoring System API",
        "version": "1.0.0",
        "docs": "/docs",
        "author":"devtheworld"
    }
