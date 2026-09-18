"""
ML Analysis Controller for Android Studio Integration
Handles error detection, fixing, and notification
"""
from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import structlog

from app.schemas.ml_analysis import (
    CodeAnalysisRequest,
    ErrorDetectionResponse,
    DetectedIssue,
    ErrorFixRequest,
    ErrorFixResponse,
    CodeFixSuggestion,
    AndroidStudioNotification,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BuildErrorReportRequest,
    BuildErrorReportResponse,
)
import hashlib

from app.database import prisma
from app.analysis.ml_models import ml_models
from app.analysis.parser import ast_features
from app.analysis.rules import android_rules
from app.analysis.rules import build_error_rules

logger = structlog.get_logger()


class MLAnalysisController:
    """ML-based code analysis for Android Studio"""

    @staticmethod
    async def detect_errors(request: CodeAnalysisRequest) -> ErrorDetectionResponse:
        """
        Detect errors and issues in code using ML + rule-based analysis

        Flow:
        1. Extract AST features from code
        2. Run rule-based analysis (deterministic)
        3. Run ML quality prediction
        4. Combine results into DetectedIssue list
        """
        try:
            # Extract features from code
            features = ast_features.extract(request.code, request.language)

            # Run rule-based analysis
            rule_matches = android_rules.evaluate(features)

            # Get quality prediction from ML
            quality_result = await ml_models.predict_quality(features)

            # Convert rule matches to DetectedIssue
            issues = []
            for match in rule_matches:
                rule = match.rule
                issue = DetectedIssue(
                    id=str(uuid.uuid4()),
                    category=rule.category,
                    severity=rule.severity,
                    title=rule.title,
                    message=rule.message,
                    suggestion=rule.suggestion,
                    line_start=1,  # Will be enhanced with actual line detection
                    line_end=None,
                    rule_id=rule.id,
                    confidence=1.0,  # Rule-based = 100% confidence
                    doc_reference=rule.doc_reference,
                )
                issues.append(issue)

            # Sort by severity
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
            issues.sort(key=lambda x: severity_order.get(x.severity, 5))

            return ErrorDetectionResponse(
                success=True,
                file_path=request.file_path,
                language=request.language,
                issues=issues,
                quality_score=quality_result['quality'],
                quality_confidence=quality_result['confidence'],
                metrics={
                    'lines_of_code': features.get('lines_of_code', 0),
                    'num_classes': features.get('num_classes', 0),
                    'num_methods': features.get('num_methods', 0),
                    'cyclomatic_complexity': features.get('cyclomatic_complexity', 0),
                    'max_nesting_depth': features.get('max_nesting_depth', 0),
                    'comment_ratio': features.get('comment_ratio', 0.0),
                },
                analyzed_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error("Error detection failed", error=str(e), file=request.file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error detection failed: {str(e)}"
            )

    @staticmethod
    async def fix_errors(request: ErrorFixRequest) -> ErrorFixResponse:
        """
        Generate fix suggestions for detected errors

        Flow:
        1. Re-analyze code to detect issues
        2. For each issue, generate fix suggestion
        3. If auto_apply, merge all fixes into final code
        """
        try:
            # First detect errors
            analysis_request = CodeAnalysisRequest(
                code=request.code,
                file_path=request.file_path,
                language=request.language,
            )
            detection_result = await MLAnalysisController.detect_errors(analysis_request)

            # Filter issues if specific IDs provided
            issues_to_fix = detection_result.issues
            if request.issue_ids:
                issues_to_fix = [i for i in issues_to_fix if i.id in request.issue_ids]

            # Generate fix suggestions
            suggestions = []
            for issue in issues_to_fix:
                fix = MLAnalysisController._generate_fix_suggestion(
                    issue, request.code, request.language
                )
                if fix:
                    suggestions.append(fix)

            # Apply fixes if requested
            fixed_code = None
            if request.auto_apply and suggestions:
                fixed_code = MLAnalysisController._apply_fixes(
                    request.code, suggestions
                )

            return ErrorFixResponse(
                success=True,
                file_path=request.file_path,
                original_code=request.code,
                fixed_code=fixed_code,
                suggestions=suggestions,
                issues_fixed=len(suggestions),
                issues_remaining=len(detection_result.issues) - len(suggestions),
            )

        except Exception as e:
            logger.error("Error fixing failed", error=str(e), file=request.file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fixing failed: {str(e)}"
            )

    @staticmethod
    def _generate_fix_suggestion(
        issue: DetectedIssue,
        code: str,
        language: str
    ) -> Optional[CodeFixSuggestion]:
        """
        Generate a fix suggestion based on the issue type
        This is a simplified version - can be enhanced with more sophisticated fixes
        """
        fixes_map = {
            "ANDROID_CONTEXT_LEAK": {
                "explanation": "Sử dụng WeakReference hoặc Application Context thay vì Activity Context cho static field",
                "pattern": "companion object",
                "replacement": "// TODO: Replace with WeakReference<Context> or use applicationContext",
            },
            "ANDROID_FINDVIEWBYID_WITHOUT_VIEWMODEL": {
                "explanation": "Refactor để sử dụng ViewModel với LiveData/StateFlow",
                "pattern": "findViewById",
                "replacement": "// TODO: Implement ViewModel pattern - see https://developer.android.com/topic/architecture",
            },
            "ANDROID_HIGH_CYCLOMATIC_COMPLEXITY": {
                "explanation": "Tách hàm phức tạp thành nhiều hàm nhỏ hơn",
                "pattern": None,
                "replacement": "// TODO: Refactor this method into smaller functions",
            },
        }

        fix_info = fixes_map.get(issue.rule_id)
        if not fix_info:
            return None

        # Simple fix generation (can be enhanced)
        return CodeFixSuggestion(
            issue_id=issue.id,
            fix_type="INSERT",
            original_code="",
            fixed_code=fix_info["replacement"],
            explanation=fix_info["explanation"],
            confidence=0.8,
            line_start=issue.line_start,
            line_end=issue.line_end or issue.line_start,
        )

    @staticmethod
    def _apply_fixes(code: str, suggestions: List[CodeFixSuggestion]) -> str:
        """
        Apply fix suggestions to code
        Simple version - insert comments at issue locations
        """
        lines = code.split('\n')

        # Sort by line number (reverse) to avoid line number shifts
        suggestions_sorted = sorted(
            suggestions,
            key=lambda x: x.line_start,
            reverse=True
        )

        for suggestion in suggestions_sorted:
            if suggestion.fix_type == "INSERT":
                # Insert fix comment before the line
                line_idx = max(0, suggestion.line_start - 1)
                if line_idx < len(lines):
                    lines.insert(line_idx, suggestion.fixed_code)

        return '\n'.join(lines)

    @staticmethod
    async def create_notification(
        notification_type: str,
        title: str,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        actions: Optional[List[Dict[str, str]]] = None,
    ) -> AndroidStudioNotification:
        """
        Create a notification for Android Studio
        """
        return AndroidStudioNotification(
            notification_type=notification_type,
            title=title,
            message=message,
            file_path=file_path,
            line_number=line_number,
            actions=actions,
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    async def report_build_error(request: BuildErrorReportRequest) -> BuildErrorReportResponse:
        """
        Match a raw compile/build error message (already debounced client-side:
        the desktop agent waits ~5s after the last keystroke and only calls this
        if the error is still present) against known patterns, persist it as a
        CodeIssue deduplicated by fingerprint, and return a friendly explanation
        + concrete fix suggestion.
        """
        session = await prisma.learningsession.find_unique(where={"id": request.session_id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        matched = build_error_rules.match_error(request.raw_error)

        if not matched:
            logger.warning(
                "build_error_no_rule_matched_trying_openai",
                session_id=request.session_id,
                file_path=request.file_path,
                raw_error=request.raw_error,
            )

            # Fallback to OpenAI analysis
            from app.services.openai_service import analyze_build_error_with_openai
            openai_result = await analyze_build_error_with_openai(
                request.raw_error,
                request.file_path or ""
            )

            if not openai_result:
                logger.warning("openai_analysis_failed", session_id=request.session_id)
                return BuildErrorReportResponse(
                    matched=False,
                    is_new=False,
                    file_path=request.file_path,
                    line_number=request.line_number,
                )

            # Use OpenAI result as if it was a rule match
            fingerprint_source = f"openai:{request.file_path or ''}:{request.raw_error.strip()}"
            fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

            existing = await prisma.codeissue.find_unique(
                where={
                    "sessionId_issueFingerprint": {
                        "sessionId": request.session_id,
                        "issueFingerprint": fingerprint,
                    }
                }
            )

            if existing:
                if existing.status == "RESOLVED":
                    issue = await prisma.codeissue.update(
                        where={"id": existing.id},
                        data={"status": "REOPENED", "attemptCount": existing.attemptCount + 1},
                    )
                else:
                    issue = await prisma.codeissue.update(
                        where={"id": existing.id},
                        data={"attemptCount": existing.attemptCount + 1},
                    )
                is_new = False
            else:
                analysis_run = await prisma.analysisrun.create(
                    data={
                        "sessionId": request.session_id,
                        "triggeredBy": "build_error_watch_openai",
                        "status": "COMPLETED",
                        "completedAt": datetime.utcnow(),
                    }
                )
                issue = await prisma.codeissue.create(
                    data={
                        "sessionId": request.session_id,
                        "analysisRunId": analysis_run.id,
                        "filePath": request.file_path or "",
                        "lineStart": request.line_number or 1,
                        "issueFingerprint": fingerprint,
                        "category": openai_result["category"],
                        "severity": openai_result["severity"],
                        "title": openai_result["title"],
                        "message": openai_result["message"],
                        "ruleId": "openai_fallback",
                    }
                )
                await prisma.codefeedback.create(
                    data={
                        "sessionId": request.session_id,
                        "analysisRunId": analysis_run.id,
                        "issueId": issue.id,
                        "type": "ERROR",
                        "title": openai_result["title"],
                        "message": openai_result["message"],
                        "suggestedFix": openai_result["suggestion"],
                        "source": "openai_gpt4o_mini",
                    }
                )
                is_new = True

                # Send WebSocket notification for new issue (OpenAI fallback)
                from app.websocket.manager import send_event_to_session
                await send_event_to_session(
                    session_id=request.session_id,
                    event_type="NEW_BUILD_ERROR",
                    payload={
                        "issue_id": issue.id,
                        "title": openai_result["title"],
                        "message": openai_result["message"],
                        "suggestion": openai_result["suggestion"],
                        "category": openai_result["category"],
                        "severity": openai_result["severity"],
                        "file_path": request.file_path,
                        "line_number": request.line_number,
                    }
                )

            return BuildErrorReportResponse(
                matched=True,
                is_new=is_new,
                issue_id=issue.id,
                rule_id="openai_fallback",
                category=openai_result["category"],
                severity=openai_result["severity"],
                title=openai_result["title"],
                message=openai_result["message"],
                suggestion=openai_result["suggestion"],
                doc_reference=openai_result.get("doc_reference"),
                file_path=request.file_path,
                line_number=request.line_number,
            )

        rule, groups = matched
        message = build_error_rules.format_with_groups(rule.message_template, groups)
        suggestion = build_error_rules.format_with_groups(rule.suggestion, groups)

        # Fingerprint = rule + file + raw error text, so the same unresolved
        # compile error while the student is still editing doesn't create a
        # new open issue every time the debounce window fires again.
        fingerprint_source = f"{rule.id}:{request.file_path or ''}:{request.raw_error.strip()}"
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

        existing = await prisma.codeissue.find_unique(
            where={
                "sessionId_issueFingerprint": {
                    "sessionId": request.session_id,
                    "issueFingerprint": fingerprint,
                }
            }
        )

        if existing:
            if existing.status == "RESOLVED":
                issue = await prisma.codeissue.update(
                    where={"id": existing.id},
                    data={"status": "REOPENED", "attemptCount": existing.attemptCount + 1},
                )
            else:
                issue = await prisma.codeissue.update(
                    where={"id": existing.id},
                    data={"attemptCount": existing.attemptCount + 1},
                )
            is_new = False
        else:
            analysis_run = await prisma.analysisrun.create(
                data={
                    "sessionId": request.session_id,
                    "triggeredBy": "build_error_watch",
                    "status": "COMPLETED",
                    "completedAt": datetime.utcnow(),
                }
            )
            issue = await prisma.codeissue.create(
                data={
                    "sessionId": request.session_id,
                    "analysisRunId": analysis_run.id,
                    "filePath": request.file_path or "",
                    "lineStart": request.line_number or 1,
                    "issueFingerprint": fingerprint,
                    "category": rule.category,
                    "severity": rule.severity,
                    "title": rule.title,
                    "message": message,
                    "ruleId": rule.id,
                }
            )
            await prisma.codefeedback.create(
                data={
                    "sessionId": request.session_id,
                    "analysisRunId": analysis_run.id,
                    "issueId": issue.id,
                    "type": "ERROR",
                    "title": rule.title,
                    "message": message,
                    "suggestedFix": suggestion,
                    "source": "rule_engine",
                }
            )
            is_new = True

            # Send WebSocket notification for new issue
            from app.websocket.manager import send_event_to_session
            await send_event_to_session(
                session_id=request.session_id,
                event_type="NEW_BUILD_ERROR",
                payload={
                    "issue_id": issue.id,
                    "title": rule.title,
                    "message": message,
                    "suggestion": suggestion,
                    "category": rule.category,
                    "severity": rule.severity,
                    "file_path": request.file_path,
                    "line_number": request.line_number,
                }
            )

        return BuildErrorReportResponse(
            matched=True,
            is_new=is_new,
            issue_id=issue.id,
            rule_id=rule.id,
            category=rule.category,
            severity=rule.severity,
            title=rule.title,
            message=message,
            suggestion=suggestion,
            doc_reference=rule.doc_reference,
            file_path=request.file_path,
            line_number=request.line_number,
        )

    @staticmethod
    async def batch_analyze(request: BatchAnalysisRequest) -> BatchAnalysisResponse:
        """
        Analyze multiple files in batch
        """
        results = []
        total_issues = 0

        for file_data in request.files:
            try:
                analysis_request = CodeAnalysisRequest(
                    code=file_data.get('code', ''),
                    file_path=file_data.get('file_path', ''),
                    language=file_data.get('language', 'kotlin'),
                )

                result = await MLAnalysisController.detect_errors(analysis_request)
                results.append(result)
                total_issues += len(result.issues)

            except Exception as e:
                logger.error(
                    "Batch analysis failed for file",
                    file=file_data.get('file_path'),
                    error=str(e)
                )
                # Continue with other files

        return BatchAnalysisResponse(
            success=True,
            total_files=len(request.files),
            files_analyzed=len(results),
            total_issues=total_issues,
            results=results,
        )
