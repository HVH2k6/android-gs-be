"""
Code Analysis schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalysisRunRequest(BaseModel):
    session_id: str
    triggered_by: str = "manual"


class CodeIssueResponse(BaseModel):
    id: str
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    category: str
    severity: str
    status: str
    title: str
    message: str
    rule_id: Optional[str] = None
    detected_at: datetime

    class Config:
        from_attributes = True


class CodeFeedbackResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    explanation: Optional[str] = None
    suggested_fix: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence: Optional[float] = None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecentIssueResponse(BaseModel):
    """A code issue plus the newest feedback attached to it, for the mobile app."""
    id: str
    session_id: str
    file_path: str
    line_start: int
    category: str
    severity: str
    status: str
    title: str
    message: str
    rule_id: Optional[str] = None
    attempt_count: int
    detected_at: datetime
    suggested_fix: Optional[str] = None
    explanation: Optional[str] = None

    class Config:
        from_attributes = True


class AnalysisRunResponse(BaseModel):
    id: str
    session_id: str
    triggered_by: str
    status: str
    current_stage: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    stages_completed: List[str]

    class Config:
        from_attributes = True
