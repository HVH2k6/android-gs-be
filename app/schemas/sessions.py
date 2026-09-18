"""
Learning Session schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionStart(BaseModel):
    assignment_id: str
    device_id: Optional[str] = None


class SessionResponse(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}

    id: str
    student_id: str = Field(validation_alias="studentId")
    assignment_id: str = Field(validation_alias="assignmentId")
    device_id: Optional[str] = Field(default=None, validation_alias="deviceId")
    status: str
    started_at: datetime = Field(validation_alias="startedAt")
    completed_at: Optional[datetime] = Field(default=None, validation_alias="completedAt")
    last_active_at: datetime = Field(validation_alias="lastActiveAt")


class SessionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(ACTIVE|PAUSED|COMPLETED|ABANDONED)$")


class SessionProgress(BaseModel):
    session_id: str
    total_requirements: int
    completed_requirements: int
    progress_percentage: float
    total_issues: int
    resolved_issues: int
    open_issues: int
    time_spent_seconds: int

    class Config:
        from_attributes = True
