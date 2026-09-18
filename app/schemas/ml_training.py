"""
ML Training schemas for admin dashboard
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class TrainingDatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)


class TrainingDatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    total_samples: int
    quality_distribution: Dict[str, int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CodeSampleCreate(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(default="kotlin", pattern="^(kotlin|java)$")
    quality_label: str = Field(..., pattern="^(EXCELLENT|GOOD|FAIR|POOR)$")
    file_path: str = Field(..., min_length=1)


class CodeSampleResponse(BaseModel):
    id: str
    code: str
    language: str
    quality_label: str
    issue_category: Optional[str] = None
    file_path: str
    metrics: Dict[str, float]
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingJobCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    dataset_id: str
    model_type: str = Field(..., pattern="^(quality_predictor|issue_classifier|similarity_detector)$")


class TrainingJobResponse(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}

    id: str
    dataset_id: str
    model_type: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TrainingMetricsResponse(BaseModel):
    total_datasets: int
    total_samples: int
    total_training_jobs: int
    active_jobs: int
    models_trained: int
    average_accuracy: float


class PaginatedCodeSamples(BaseModel):
    samples: List[CodeSampleResponse]
    total: int
    page: int
    pages: int
