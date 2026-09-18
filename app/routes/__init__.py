"""
Routes package initialization
"""
from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.courses import router as courses_router
from app.routes.assignments import router as assignments_router
from app.routes.sessions import router as sessions_router
from app.routes.projects import router as projects_router
from app.routes.analysis import router as analysis_router
from app.routes.roles import router as roles_router
from app.routes.ml_analysis import router as ml_analysis_router
from app.routes.ml_training import router as ml_training_router

__all__ = [
    "auth_router",
    "courses_router",
    "assignments_router",
    "sessions_router",
    "projects_router",
    "analysis_router",
    "roles_router",
    "ml_analysis_router",
    "ml_training_router",
]
