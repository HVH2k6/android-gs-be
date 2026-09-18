"""
Project and File sync schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FileSync(BaseModel):
    path: str
    content: str
    language: Optional[str] = None


class ProjectSyncInitial(BaseModel):
    project_name: str
    package_name: Optional[str] = None
    root_path: str
    files: List[FileSync]


class ProjectSyncIncremental(BaseModel):
    files: List[FileSync]


class ProjectFileResponse(BaseModel):
    id: str
    project_id: str
    path: str
    version: int
    content_hash: str
    size_bytes: int
    language: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: str
    session_id: str
    name: str
    package_name: Optional[str] = None
    root_path: str
    last_sync_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectStateResponse(BaseModel):
    project: ProjectResponse
    files_count: int
    total_size_bytes: int
    last_sync_at: datetime
