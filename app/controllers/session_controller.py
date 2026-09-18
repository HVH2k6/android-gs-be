"""
Session Controller
Handles learning session management
"""
from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional

from app.database import prisma
from app.schemas.sessions import (
    SessionStart,
    SessionResponse,
    SessionStatusUpdate,
    SessionProgress,
)


class SessionController:
    """Learning session business logic"""

    @staticmethod
    async def start_session(session_data: SessionStart, student_id: str) -> SessionResponse:
        """Start a new learning session"""
        # Verify assignment exists
        assignment = await prisma.assignment.find_unique(where={"id": session_data.assignment_id})
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )

        # Check if student is enrolled in the course
        enrollment = await prisma.enrollment.find_first(
            where={
                "studentId": student_id,
                "courseId": assignment.courseId,
                "status": "ACTIVE"
            }
        )
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student not enrolled in this course"
            )

        # Check if there's an active session for this assignment
        active_session = await prisma.learningsession.find_first(
            where={
                "studentId": student_id,
                "assignmentId": session_data.assignment_id,
                "status": {"in": ["ACTIVE", "PAUSED"]}
            }
        )

        if active_session:
            # Return existing session
            return SessionResponse.model_validate(active_session)

        # Create new session
        create_data = {
            "studentId": student_id,
            "assignmentId": session_data.assignment_id,
            "status": "ACTIVE",
        }

        # Only set deviceId if it exists in Device table
        if session_data.device_id:
            device = await prisma.device.find_unique(where={"id": session_data.device_id})
            if device:
                create_data["deviceId"] = session_data.device_id

        session = await prisma.learningsession.create(data=create_data)

        # Create project placeholder
        await prisma.project.create(
            data={
                "sessionId": session.id,
                "name": f"Assignment_{assignment.id[:8]}",
                "rootPath": "/",
            }
        )

        return SessionResponse.model_validate(session)

    @staticmethod
    async def get_session(session_id: str, student_id: Optional[str] = None) -> SessionResponse:
        """Get session by ID"""
        session = await prisma.learningsession.find_unique(where={"id": session_id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Check ownership if student_id provided
        if student_id and session.studentId != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return SessionResponse.model_validate(session)

    @staticmethod
    async def update_session_status(
        session_id: str,
        status_update: SessionStatusUpdate,
        student_id: Optional[str] = None
    ) -> SessionResponse:
        """Update session status"""
        session = await prisma.learningsession.find_unique(where={"id": session_id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Check ownership
        if student_id and session.studentId != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Update session
        update_data = {
            "status": status_update.status,
            "lastActiveAt": datetime.utcnow(),
        }

        if status_update.status == "COMPLETED":
            update_data["completedAt"] = datetime.utcnow()

        updated_session = await prisma.learningsession.update(
            where={"id": session_id},
            data=update_data
        )

        return SessionResponse.model_validate(updated_session)

    @staticmethod
    async def get_session_progress(session_id: str) -> SessionProgress:
        """Get session progress statistics"""
        session = await prisma.learningsession.find_unique(
            where={"id": session_id},
            include={
                "assignment": {
                    "include": {"requirements": True}
                }
            }
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Get requirement evaluations
        evaluations = await prisma.requirementevaluation.find_many(
            where={"sessionId": session_id}
        )

        total_requirements = len(session.assignment.requirements)
        completed_requirements = sum(1 for e in evaluations if e.passed)
        progress_percentage = (completed_requirements / total_requirements * 100) if total_requirements > 0 else 0

        # Get issues statistics
        issues = await prisma.codeissue.find_many(
            where={"sessionId": session_id}
        )

        total_issues = len(issues)
        resolved_issues = sum(1 for i in issues if i.status == "RESOLVED")
        open_issues = sum(1 for i in issues if i.status == "OPEN")

        # Calculate time spent
        time_spent = (datetime.utcnow() - session.startedAt).total_seconds()

        return SessionProgress(
            session_id=session_id,
            total_requirements=total_requirements,
            completed_requirements=completed_requirements,
            progress_percentage=progress_percentage,
            total_issues=total_issues,
            resolved_issues=resolved_issues,
            open_issues=open_issues,
            time_spent_seconds=int(time_spent),
        )
