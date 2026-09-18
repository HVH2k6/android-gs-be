"""
Course Routes
Handles course and assignment endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List

from app.controllers.course_controller import CourseController, AssignmentController
from app.schemas.courses import (
    CourseCreate,
    CourseResponse,
    AssignmentCreate,
    AssignmentResponse,
    RequirementCreate,
    RequirementResponse,
)
from app.routes.auth import get_current_user
from app.schemas.auth import UserResponse

router = APIRouter()


@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new course (Instructor/Admin only)"""
    if not current_user.role or current_user.role.name not in ["INSTRUCTOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return await CourseController.create_course(course_data)


@router.get("/", response_model=List[CourseResponse])
async def get_courses(
    published_only: bool = Query(True),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all courses"""
    return await CourseController.get_courses(published_only)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get course by ID"""
    return await CourseController.get_course(course_id)


@router.get("/{course_id}/assignments", response_model=List[AssignmentResponse])
async def get_course_assignments(
    course_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all assignments for a course"""
    return await CourseController.get_course_assignments(course_id)
