"""
Project Routes
Handles project file synchronization endpoints
"""
from fastapi import APIRouter, Depends
from typing import List

from app.controllers.project_controller import ProjectController
from app.schemas.projects import (
    ProjectSyncInitial,
    ProjectSyncIncremental,
    ProjectResponse,
    ProjectFileResponse,
    ProjectStateResponse,
)
from app.routes.sessions import get_student_id
from app.controllers.session_controller import SessionController

router = APIRouter()


@router.post("/{session_id}/sync/initial", response_model=ProjectResponse)
async def sync_initial(
    session_id: str,
    sync_data: ProjectSyncInitial,
    student_id: str = Depends(get_student_id)
):
    """Initial project sync"""
    # Verify session ownership
    await SessionController.get_session(session_id, student_id)
    return await ProjectController.sync_initial(session_id, sync_data)


@router.post("/{session_id}/sync/incremental")
async def sync_incremental(
    session_id: str,
    sync_data: ProjectSyncIncremental,
    student_id: str = Depends(get_student_id)
):
    """Incremental project sync"""
    # Verify session ownership
    await SessionController.get_session(session_id, student_id)
    return await ProjectController.sync_incremental(session_id, sync_data)


@router.get("/{session_id}/files", response_model=List[ProjectFileResponse])
async def get_project_files(
    session_id: str,
    student_id: str = Depends(get_student_id)
):
    """Get all files in a project"""
    # Verify session ownership
    await SessionController.get_session(session_id, student_id)
    return await ProjectController.get_project_files(session_id)


@router.get("/{session_id}/state", response_model=ProjectStateResponse)
async def get_project_state(
    session_id: str,
    student_id: str = Depends(get_student_id)
):
    """Get project state summary"""
    # Verify session ownership
    await SessionController.get_session(session_id, student_id)
    return await ProjectController.get_project_state(session_id)
