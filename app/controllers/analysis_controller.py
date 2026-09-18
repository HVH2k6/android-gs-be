"""
Analysis Controller
Handles code analysis orchestration
"""
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import prisma
from app.schemas.analysis import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    CodeIssueResponse,
    CodeFeedbackResponse,
    RecentIssueResponse,
)


class AnalysisController:
    """Code analysis orchestration business logic"""

    @staticmethod
    async def create_analysis_run(analysis_data: AnalysisRunRequest) -> AnalysisRunResponse:
        """Create and queue a new analysis run"""
        # Verify session exists
        session = await prisma.learningsession.find_unique(where={"id": analysis_data.session_id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Create analysis run
        analysis_run = await prisma.analysisrun.create(
            data={
                "sessionId": analysis_data.session_id,
                "triggeredBy": analysis_data.triggered_by,
                "status": "PENDING",
            }
        )

        # TODO: Enqueue background task for analysis pipeline
        # from app.tasks.analysis import run_analysis_pipeline
        # run_analysis_pipeline.delay(analysis_run.id)

        return AnalysisRunResponse.model_validate(analysis_run)

    @staticmethod
    async def get_analysis_run(run_id: str) -> AnalysisRunResponse:
        """Get analysis run by ID"""
        analysis_run = await prisma.analysisrun.find_unique(where={"id": run_id})
        if not analysis_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis run not found"
            )

        return AnalysisRunResponse.model_validate(analysis_run)

    @staticmethod
    async def get_analysis_issues(run_id: str) -> List[CodeIssueResponse]:
        """Get all issues detected in an analysis run"""
        # Verify analysis run exists
        analysis_run = await prisma.analysisrun.find_unique(where={"id": run_id})
        if not analysis_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis run not found"
            )

        issues = await prisma.codeissue.find_many(
            where={"analysisRunId": run_id},
            order={"detectedAt": "desc"}
        )

        return [CodeIssueResponse.model_validate(i) for i in issues]

    @staticmethod
    async def get_analysis_feedback(run_id: str) -> List[CodeFeedbackResponse]:
        """Get all feedback generated in an analysis run"""
        # Verify analysis run exists
        analysis_run = await prisma.analysisrun.find_unique(where={"id": run_id})
        if not analysis_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis run not found"
            )

        feedback = await prisma.codefeedback.find_many(
            where={"analysisRunId": run_id},
            order={"createdAt": "desc"}
        )

        return [CodeFeedbackResponse.model_validate(f) for f in feedback]

    @staticmethod
    async def get_session_issues(
        session_id: str,
        status_filter: Optional[str] = None
    ) -> List[CodeIssueResponse]:
        """Get all issues for a session"""
        where_clause = {"sessionId": session_id}
        if status_filter:
            where_clause["status"] = status_filter

        issues = await prisma.codeissue.find_many(
            where=where_clause,
            order={"detectedAt": "desc"}
        )

        return [CodeIssueResponse.model_validate(i) for i in issues]

    @staticmethod
    async def get_recent_student_issues(
        student_id: str,
        limit: int = 5
    ) -> List[RecentIssueResponse]:
        """Most recent issues across all of a student's sessions, with fix suggestion."""
        issues = await prisma.codeissue.find_many(
            where={"session": {"is": {"studentId": student_id}}},
            order={"detectedAt": "desc"},
            take=limit,
            include={"feedback": {"order_by": {"createdAt": "desc"}, "take": 1}},
        )

        results = []
        for issue in issues:
            latest = issue.feedback[0] if issue.feedback else None
            results.append(RecentIssueResponse(
                id=issue.id,
                session_id=issue.sessionId,
                file_path=issue.filePath,
                line_start=issue.lineStart,
                category=issue.category,
                severity=issue.severity,
                status=issue.status,
                title=issue.title,
                message=issue.message,
                rule_id=issue.ruleId,
                attempt_count=issue.attemptCount,
                detected_at=issue.detectedAt,
                suggested_fix=latest.suggestedFix if latest else None,
                explanation=latest.explanation if latest else None,
            ))
        return results
