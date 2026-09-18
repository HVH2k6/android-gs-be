"""
ML Analysis Routes for Android Studio Integration
API endpoints for error detection, fixing, and notifications
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from app.controllers.ml_analysis_controller import MLAnalysisController
from app.schemas.ml_analysis import (
    CodeAnalysisRequest,
    ErrorDetectionResponse,
    ErrorFixRequest,
    ErrorFixResponse,
    AndroidStudioNotification,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BuildErrorReportRequest,
    BuildErrorReportResponse,
)

router = APIRouter()


@router.post("/detect", response_model=ErrorDetectionResponse)
async def detect_errors(request: CodeAnalysisRequest):
    """
    Detect errors and issues in code using ML + rule-based analysis

    This endpoint analyzes Android code (Kotlin/Java) and returns:
    - List of detected issues with severity and category
    - Overall quality score (EXCELLENT/GOOD/FAIR/POOR)
    - Code metrics (LOC, complexity, etc.)

    Example:
    ```json
    {
      "code": "class MainActivity : AppCompatActivity() { ... }",
      "file_path": "app/src/main/java/com/example/MainActivity.kt",
      "language": "kotlin"
    }
    ```
    """
    return await MLAnalysisController.detect_errors(request)


@router.post("/fix", response_model=ErrorFixResponse)
async def fix_errors(request: ErrorFixRequest):
    """
    Generate fix suggestions for detected errors

    This endpoint:
    1. Analyzes the code to detect issues
    2. Generates fix suggestions for each issue
    3. Optionally applies fixes automatically (if auto_apply=true)

    Example:
    ```json
    {
      "code": "class MainActivity : AppCompatActivity() { ... }",
      "file_path": "app/src/main/java/com/example/MainActivity.kt",
      "language": "kotlin",
      "issue_ids": ["uuid-1", "uuid-2"],
      "auto_apply": false
    }
    ```
    """
    return await MLAnalysisController.fix_errors(request)


@router.post("/notify", response_model=AndroidStudioNotification)
async def create_notification(
    notification_type: str,
    title: str,
    message: str,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
):
    """
    Create a notification for Android Studio

    Types: ERROR, WARNING, INFO, SUCCESS

    Example:
    ```
    POST /api/ml-analysis/notify?notification_type=ERROR&title=Memory+Leak&message=Context+leak+detected
    ```
    """
    return await MLAnalysisController.create_notification(
        notification_type=notification_type,
        title=title,
        message=message,
        file_path=file_path,
        line_number=line_number,
    )


@router.post("/batch", response_model=BatchAnalysisResponse)
async def batch_analyze(request: BatchAnalysisRequest):
    """
    Analyze multiple files in a single request

    Useful for analyzing entire modules or packages at once.

    Example:
    ```json
    {
      "files": [
        {
          "file_path": "MainActivity.kt",
          "code": "...",
          "language": "kotlin"
        },
        {
          "file_path": "UserViewModel.kt",
          "code": "...",
          "language": "kotlin"
        }
      ],
      "project_name": "MyAndroidApp"
    }
    ```
    """
    return await MLAnalysisController.batch_analyze(request)


@router.post("/report-build-error", response_model=BuildErrorReportResponse)
async def report_build_error(request: BuildErrorReportRequest):
    """
    Report a raw Gradle/Kotlin/Java compile error from Android Studio and
    get back a friendly message + concrete fix suggestion.

    The desktop agent should debounce: wait ~5s after the last keystroke,
    and only call this endpoint if the error is still present at that point
    (skip it if the student fixed it before the 5s window elapsed). The
    same error is deduplicated server-side by fingerprint, so calling this
    repeatedly while the error persists won't create duplicate issues.

    Example:
    ```json
    {
      "session_id": "clx1234567890",
      "raw_error": "e: MainActivity.kt: (12, 5): Unresolved reference: findViewByld",
      "file_path": "app/src/main/java/com/example/MainActivity.kt",
      "line_number": 12
    }
    ```
    """
    return await MLAnalysisController.report_build_error(request)


@router.get("/health")
async def health_check():
    """Check if ML analysis service is ready"""
    return {
        "status": "healthy",
        "service": "ml-analysis",
        "features": [
            "error_detection",
            "error_fixing",
            "batch_analysis",
            "notifications"
        ]
    }
