"""
Learning Session Routes
Handles learning session endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.database import prisma

from app.controllers.session_controller import SessionController
from app.schemas.sessions import (
    SessionStart,
    SessionResponse,
    SessionStatusUpdate,
    SessionProgress,
)
from app.routes.auth import get_current_user
from app.schemas.auth import UserResponse

router = APIRouter()


async def get_student_id(current_user: UserResponse = Depends(get_current_user)) -> str:
    """Get student ID from current user"""
    if not current_user.role or current_user.role.name != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    student = await prisma.student.find_unique(where={"userId": current_user.id})
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    return student.id


@router.post("/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionStart,
    student_id: str = Depends(get_student_id)
):
    """Start a new learning session"""
    try:
        return await SessionController.start_session(session_data, student_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


@router.get("/active", response_model=Optional[SessionResponse])
async def get_active_session(student_id: str = Depends(get_student_id)):
    """Newest ACTIVE session of the logged-in student, or null if none."""
    session = await prisma.learningsession.find_first(
        where={"studentId": student_id, "status": "ACTIVE"},
        order={"lastActiveAt": "desc"},
    )
    if not session:
        return None
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    student_id: str = Depends(get_student_id)
):
    """Get session details"""
    return await SessionController.get_session(session_id, student_id)


@router.patch("/{session_id}/status", response_model=SessionResponse)
async def update_session_status(
    session_id: str,
    status_update: SessionStatusUpdate,
    student_id: str = Depends(get_student_id)
):
    """Update session status"""
    return await SessionController.update_session_status(session_id, status_update, student_id)


@router.get("/{session_id}/progress", response_model=SessionProgress)
async def get_session_progress(
    session_id: str,
    student_id: str = Depends(get_student_id)
):
    """Get session progress"""
    # Verify ownership
    await SessionController.get_session(session_id, student_id)
    return await SessionController.get_session_progress(session_id)
