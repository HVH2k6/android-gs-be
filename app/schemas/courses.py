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
    isPublished: bool = Field(False, alias="is_published")


class CourseResponse(CourseBase):
    id: str
    isPublished: bool = Field(..., alias="is_published")
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class AssignmentBase(BaseModel):
    title: str
    description: str
    difficulty: str = "BEGINNER"
    timeEstimate: Optional[int] = Field(None, alias="time_estimate")


class AssignmentCreate(AssignmentBase):
    courseId: str = Field(..., alias="course_id")
    order: int
    isPublished: bool = Field(False, alias="is_published")


class AssignmentResponse(AssignmentBase):
    id: str
    courseId: str
    order: int
    isPublished: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class RequirementBase(BaseModel):
    type: str
    title: str
    description: str
    evalMethod: str = Field(..., alias="eval_method")
    evalConfig: Optional[dict] = Field(None, alias="eval_config")
    points: int = 1


class RequirementCreate(RequirementBase):
    assignmentId: str = Field(..., alias="assignment_id")
    order: int


class RequirementResponse(RequirementBase):
    id: str
    assignmentId: str
    order: int
    createdAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
