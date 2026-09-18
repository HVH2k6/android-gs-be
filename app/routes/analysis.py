"""
Code Analysis Routes
Handles code analysis endpoints
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.controllers.analysis_controller import AnalysisController
from app.schemas.analysis import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    CodeIssueResponse,
    CodeFeedbackResponse,
    RecentIssueResponse,
)
from app.routes.sessions import get_student_id
from app.controllers.session_controller import SessionController

router = APIRouter()


@router.post("/run", response_model=AnalysisRunResponse)
async def create_analysis_run(
    analysis_data: AnalysisRunRequest,
    student_id: str = Depends(get_student_id)
):
    """Create and queue a new analysis run"""
    # Verify session ownership
    await SessionController.get_session(analysis_data.session_id, student_id)
    return await AnalysisController.create_analysis_run(analysis_data)


@router.get("/issues/recent", response_model=List[RecentIssueResponse])
async def get_recent_issues(
    limit: int = Query(5, ge=1, le=50),
    student_id: str = Depends(get_student_id)
):
    """Most recent issues for the logged-in student, newest first."""
    return await AnalysisController.get_recent_student_issues(student_id, limit)


@router.get("/{run_id}", response_model=AnalysisRunResponse)
async def get_analysis_run(
    run_id: str,
    student_id: str = Depends(get_student_id)
):
    """Get analysis run details"""
    analysis_run = await AnalysisController.get_analysis_run(run_id)
    # Verify session ownership
    await SessionController.get_session(analysis_run.session_id, student_id)
    return analysis_run


@router.get("/{run_id}/issues", response_model=List[CodeIssueResponse])
async def get_analysis_issues(
    run_id: str,
    student_id: str = Depends(get_student_id)
):
    """Get all issues detected in an analysis run"""
    analysis_run = await AnalysisController.get_analysis_run(run_id)
    # Verify session ownership
    await SessionController.get_session(analysis_run.session_id, student_id)
    return await AnalysisController.get_analysis_issues(run_id)


@router.get("/{run_id}/feedback", response_model=List[CodeFeedbackResponse])
async def get_analysis_feedback(
    run_id: str,
    student_id: str = Depends(get_student_id)
):
    """Get all feedback generated in an analysis run"""
    analysis_run = await AnalysisController.get_analysis_run(run_id)
    # Verify session ownership
    await SessionController.get_session(analysis_run.session_id, student_id)
    return await AnalysisController.get_analysis_feedback(run_id)


@router.get("/sessions/{session_id}/issues", response_model=List[CodeIssueResponse])
async def get_session_issues(
    session_id: str,
    status_filter: Optional[str] = Query(None),
    student_id: str = Depends(get_student_id)
):
    """Get all issues for a session"""
    # Verify session ownership
    await SessionController.get_session(session_id, student_id)
    return await AnalysisController.get_session_issues(session_id, status_filter)
