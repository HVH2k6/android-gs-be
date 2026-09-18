"""
ML Analysis schemas for Android Studio integration
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CodeAnalysisRequest(BaseModel):
    """Request to analyze code for errors"""
    code: str = Field(..., description="Source code to analyze (Kotlin/Java)")
    file_path: str = Field(..., description="File path in project")
    language: str = Field(default="kotlin", description="Programming language (kotlin/java)")
    project_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional project context")


class DetectedIssue(BaseModel):
    """Single detected issue/error"""
    id: str
    category: str  # BUG, PERFORMANCE, SECURITY, BEST_PRACTICE, STYLE_WARNING
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str
    message: str
    suggestion: Optional[str] = None
    line_start: int
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    rule_id: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    doc_reference: Optional[str] = None


class CodeFixSuggestion(BaseModel):
    """Suggested fix for an issue"""
    issue_id: str
    fix_type: str  # REPLACE, INSERT, DELETE
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    line_start: int
    line_end: int


class ErrorDetectionResponse(BaseModel):
    """Response from error detection"""
    success: bool
    file_path: str
    language: str
    issues: List[DetectedIssue]
    quality_score: str  # EXCELLENT, GOOD, FAIR, POOR
    quality_confidence: float
    metrics: Dict[str, Any]
    analyzed_at: datetime


class ErrorFixRequest(BaseModel):
    """Request to fix specific errors"""
    code: str = Field(..., description="Original source code")
    file_path: str
    language: str = Field(default="kotlin")
    issue_ids: Optional[List[str]] = Field(default=None, description="Specific issues to fix, or None for all")
    auto_apply: bool = Field(default=False, description="Apply fixes automatically")


class ErrorFixResponse(BaseModel):
    """Response with suggested fixes"""
    success: bool
    file_path: str
    original_code: str
    fixed_code: Optional[str] = None
    suggestions: List[CodeFixSuggestion]
    issues_fixed: int
    issues_remaining: int


class AndroidStudioNotification(BaseModel):
    """Notification payload for Android Studio"""
    notification_type: str  # ERROR, WARNING, INFO, SUCCESS
    title: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    actions: Optional[List[Dict[str, str]]] = None  # [{"label": "Fix", "action": "apply_fix"}]
    timestamp: datetime


class BatchAnalysisRequest(BaseModel):
    """Analyze multiple files at once"""
    files: List[Dict[str, str]] = Field(..., description="List of {file_path, code, language}")
    project_name: Optional[str] = None


class BatchAnalysisResponse(BaseModel):
    """Batch analysis results"""
    success: bool
    total_files: int
    files_analyzed: int
    total_issues: int
    results: List[ErrorDetectionResponse]


class BuildErrorReportRequest(BaseModel):
    """
    Raw compile/build error reported from Android Studio, after the desktop
    agent has debounced edits (error still present ~5s after the last
    keystroke) so we don't get spammed with errors from half-typed code.
    """
    session_id: str = Field(..., description="Learning session this error belongs to")
    raw_error: str = Field(..., description="Raw error text from Gradle/Kotlin/Java compiler")
    file_path: Optional[str] = Field(default=None, description="File path where the error occurred")
    line_number: Optional[int] = Field(default=None, description="Line number reported by the compiler")


class BuildErrorReportResponse(BaseModel):
    """Friendly explanation + fix suggestion for a reported build error"""
    matched: bool
    is_new: bool = Field(description="False if this exact issue (by fingerprint) was already open")
    issue_id: Optional[str] = None
    rule_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    suggestion: Optional[str] = None
    doc_reference: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
