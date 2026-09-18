"""
Project Controller
Handles project file synchronization and management
"""
from fastapi import HTTPException, status
from typing import List
import xxhash
from datetime import datetime

from app.database import prisma
from app.schemas.projects import (
    ProjectSyncInitial,
    ProjectSyncIncremental,
    ProjectResponse,
    ProjectFileResponse,
    ProjectStateResponse,
    FileSync,
)
from app.config import settings


class ProjectController:
    """Project and file management business logic"""

    @staticmethod
    def calculate_file_hash(content: str) -> str:
        """Calculate xxHash64 for file content"""
        return xxhash.xxh64(content.encode()).hexdigest()

    @staticmethod
    def detect_language(file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = file_path.split('.')[-1].lower()
        lang_map = {
            'kt': 'kotlin',
            'java': 'java',
            'xml': 'xml',
            'gradle': 'gradle',
            'kts': 'kotlin',
            'json': 'json',
        }
        return lang_map.get(ext, 'unknown')

    @staticmethod
    async def sync_initial(session_id: str, sync_data: ProjectSyncInitial) -> ProjectResponse:
        """Initial project sync"""
        # Verify session exists
        session = await prisma.learningsession.find_unique(where={"id": session_id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Check if project already exists
        existing_project = await prisma.project.find_unique(where={"sessionId": session_id})
        if existing_project:
            # Delete existing project and files
            await prisma.projectfile.delete_many(where={"projectId": existing_project.id})
            await prisma.project.delete(where={"id": existing_project.id})

        # Calculate total size
        total_size = sum(len(f.content.encode()) for f in sync_data.files)
        max_size = settings.MAX_PROJECT_SIZE_MB * 1024 * 1024

        if total_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Project size exceeds {settings.MAX_PROJECT_SIZE_MB}MB limit"
            )

        # Create project
        project = await prisma.project.create(
            data={
                "sessionId": session_id,
                "name": sync_data.project_name,
                "packageName": sync_data.package_name,
                "rootPath": sync_data.root_path,
            }
        )

        # Create files
        for file_data in sync_data.files:
            content_hash = ProjectController.calculate_file_hash(file_data.content)
            size_bytes = len(file_data.content.encode())

            # Check file size
            max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if size_bytes > max_file_size:
                continue  # Skip oversized files

            language = file_data.language or ProjectController.detect_language(file_data.path)

            await prisma.projectfile.create(
                data={
                    "projectId": project.id,
                    "path": file_data.path,
                    "content": file_data.content,
                    "contentHash": content_hash,
                    "sizeBytes": size_bytes,
                    "language": language,
                }
            )

        return ProjectResponse.model_validate(project)

    @staticmethod
    async def sync_incremental(session_id: str, sync_data: ProjectSyncIncremental) -> dict:
        """Incremental project sync (update changed files)"""
        # Get project
        project = await prisma.project.find_unique(where={"sessionId": session_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found. Please perform initial sync first."
            )

        updated_files = []
        new_files = []

        for file_data in sync_data.files:
            content_hash = ProjectController.calculate_file_hash(file_data.content)
            size_bytes = len(file_data.content.encode())

            # Check file size
            max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if size_bytes > max_file_size:
                continue

            # Check if file exists
            existing_file = await prisma.projectfile.find_first(
                where={
                    "projectId": project.id,
                    "path": file_data.path,
                    "status": "ACTIVE"
                }
            )

            language = file_data.language or ProjectController.detect_language(file_data.path)

            if existing_file:
                # Check if content changed
                if existing_file.contentHash != content_hash:
                    # Create new version
                    new_file = await prisma.projectfile.create(
                        data={
                            "projectId": project.id,
                            "path": file_data.path,
                            "version": existing_file.version + 1,
                            "content": file_data.content,
                            "contentHash": content_hash,
                            "sizeBytes": size_bytes,
                            "language": language,
                        }
                    )
                    updated_files.append(new_file.path)
            else:
                # Create new file
                new_file = await prisma.projectfile.create(
                    data={
                        "projectId": project.id,
                        "path": file_data.path,
                        "content": file_data.content,
                        "contentHash": content_hash,
                        "sizeBytes": size_bytes,
                        "language": language,
                    }
                )
                new_files.append(new_file.path)

        # Update project last sync time
        await prisma.project.update(
            where={"id": project.id},
            data={"lastSyncAt": datetime.utcnow()}
        )

        return {
            "updated_files": updated_files,
            "new_files": new_files,
            "total_synced": len(updated_files) + len(new_files),
        }

    @staticmethod
    async def get_project_files(session_id: str) -> List[ProjectFileResponse]:
        """Get all files in a project"""
        project = await prisma.project.find_unique(where={"sessionId": session_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        files = await prisma.projectfile.find_many(
            where={
                "projectId": project.id,
                "status": "ACTIVE"
            },
            order={"path": "asc"}
        )

        return [ProjectFileResponse.model_validate(f) for f in files]

    @staticmethod
    async def get_project_state(session_id: str) -> ProjectStateResponse:
        """Get project state summary"""
        project = await prisma.project.find_unique(where={"sessionId": session_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        files = await prisma.projectfile.find_many(
            where={
                "projectId": project.id,
                "status": "ACTIVE"
            }
        )

        files_count = len(files)
        total_size_bytes = sum(f.sizeBytes for f in files)

        return ProjectStateResponse(
            project=ProjectResponse.model_validate(project),
            files_count=files_count,
            total_size_bytes=total_size_bytes,
            last_sync_at=project.lastSyncAt,
        )
