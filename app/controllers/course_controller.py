"""
Course Controller
Handles course and assignment business logic
"""
from fastapi import HTTPException, status
from typing import List, Optional

from app.database import prisma
from app.schemas.courses import (
    CourseCreate,
    CourseResponse,
    AssignmentCreate,
    AssignmentResponse,
    RequirementCreate,
    RequirementResponse,
)


class CourseController:
    """Course management business logic"""

    @staticmethod
    async def create_course(course_data: CourseCreate) -> CourseResponse:
        """Create new course"""
        # Check if course code already exists
        existing = await prisma.course.find_unique(where={"code": course_data.code})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Course with code {course_data.code} already exists"
            )

        course = await prisma.course.create(
            data={
                "code": course_data.code,
                "title": course_data.title,
                "description": course_data.description,
                "isPublished": course_data.is_published,
            }
        )

        return CourseResponse.model_validate(course)

    @staticmethod
    async def get_courses(published_only: bool = True) -> List[CourseResponse]:
        """Get all courses"""
        where_clause = {"isPublished": True} if published_only else {}
        courses = await prisma.course.find_many(
            where=where_clause,
            order={"createdAt": "desc"}
        )
        return [CourseResponse.model_validate(c) for c in courses]

    @staticmethod
    async def get_course(course_id: str) -> CourseResponse:
        """Get course by ID"""
        course = await prisma.course.find_unique(where={"id": course_id})
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        return CourseResponse.model_validate(course)

    @staticmethod
    async def get_course_assignments(course_id: str) -> List[AssignmentResponse]:
        """Get all assignments for a course"""
        assignments = await prisma.assignment.find_many(
            where={"courseId": course_id, "isPublished": True},
            order={"order": "asc"}
        )
        return [AssignmentResponse.model_validate(a) for a in assignments]


class AssignmentController:
    """Assignment management business logic"""

    @staticmethod
    async def create_assignment(assignment_data: AssignmentCreate) -> AssignmentResponse:
        """Create new assignment"""
        # Verify course exists
        course = await prisma.course.find_unique(where={"id": assignment_data.course_id})
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )

        assignment = await prisma.assignment.create(
            data={
                "courseId": assignment_data.course_id,
                "order": assignment_data.order,
                "title": assignment_data.title,
                "description": assignment_data.description,
                "difficulty": assignment_data.difficulty,
                "timeEstimate": assignment_data.time_estimate,
                "isPublished": assignment_data.is_published,
            }
        )

        return AssignmentResponse.model_validate(assignment)

    @staticmethod
    async def get_assignment(assignment_id: str) -> AssignmentResponse:
        """Get assignment by ID"""
        assignment = await prisma.assignment.find_unique(where={"id": assignment_id})
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        return AssignmentResponse.model_validate(assignment)

    @staticmethod
    async def get_assignment_requirements(assignment_id: str) -> List[RequirementResponse]:
        """Get all requirements for an assignment"""
        requirements = await prisma.assignmentrequirement.find_many(
            where={"assignmentId": assignment_id},
            order={"order": "asc"}
        )
        return [RequirementResponse.model_validate(r) for r in requirements]

    @staticmethod
    async def create_requirement(requirement_data: RequirementCreate) -> RequirementResponse:
        """Create new assignment requirement"""
        # Verify assignment exists
        assignment = await prisma.assignment.find_unique(where={"id": requirement_data.assignment_id})
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )

        requirement = await prisma.assignmentrequirement.create(
            data={
                "assignmentId": requirement_data.assignment_id,
                "order": requirement_data.order,
                "type": requirement_data.type,
                "title": requirement_data.title,
                "description": requirement_data.description,
                "evalMethod": requirement_data.eval_method,
                "evalConfig": requirement_data.eval_config,
                "points": requirement_data.points,
            }
        )

        return RequirementResponse.model_validate(requirement)
