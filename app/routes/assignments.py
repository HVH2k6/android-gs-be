"""
Assignment Routes
Handles assignment endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.controllers.course_controller import AssignmentController
from app.schemas.courses import (
    AssignmentCreate,
    AssignmentResponse,
    RequirementCreate,
    RequirementResponse,
)
from app.routes.auth import get_current_user
from app.schemas.auth import UserResponse

router = APIRouter()


@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new assignment (Instructor/Admin only)"""
    if not current_user.role or current_user.role.name not in ["INSTRUCTOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return await AssignmentController.create_assignment(assignment_data)


@router.get("/", response_model=List[AssignmentResponse])
async def list_assignments(
    current_user: UserResponse = Depends(get_current_user)
):
    """Published assignments, ordered — lets a client pick one without hardcoding an id."""
    return await AssignmentController.list_published_assignments()


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get assignment by ID"""
    return await AssignmentController.get_assignment(assignment_id)


@router.get("/{assignment_id}/requirements", response_model=List[RequirementResponse])
async def get_assignment_requirements(
    assignment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all requirements for an assignment"""
    return await AssignmentController.get_assignment_requirements(assignment_id)


@router.post("/{assignment_id}/requirements", response_model=RequirementResponse)
async def create_requirement(
    assignment_id: str,
    requirement_data: RequirementCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new requirement for an assignment (Instructor/Admin only)"""
    if not current_user.role or current_user.role.name not in ["INSTRUCTOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Ensure assignment_id matches
    requirement_data.assignment_id = assignment_id
    return await AssignmentController.create_requirement(requirement_data)
