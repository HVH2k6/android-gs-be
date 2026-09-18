"""
Course and Assignment schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CourseBase(BaseModel):
    code: str
    title: str
    description: Optional[str] = None


class CourseCreate(CourseBase):
    is_published: bool = False


class CourseResponse(CourseBase):
    id: str
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentBase(BaseModel):
    title: str
    description: str
    difficulty: str = "BEGINNER"
    time_estimate: Optional[int] = None


class AssignmentCreate(AssignmentBase):
    course_id: str
    order: int
    is_published: bool = False


class AssignmentResponse(AssignmentBase):
    id: str
    course_id: str
    order: int
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementBase(BaseModel):
    type: str
    title: str
    description: str
    eval_method: str
    eval_config: Optional[dict] = None
    points: int = 1


class RequirementCreate(RequirementBase):
    assignment_id: str
    order: int


class RequirementResponse(RequirementBase):
    id: str
    assignment_id: str
    order: int
    created_at: datetime

    class Config:
        from_attributes = True
