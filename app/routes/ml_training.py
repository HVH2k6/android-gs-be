"""
ML Training Routes for Admin Dashboard
API endpoints for dataset management, training jobs, and code samples
"""
from fastapi import APIRouter, Query, Depends
from typing import List

from app.controllers.ml_training_controller import MLTrainingController
from app.schemas.ml_training import (
    TrainingDatasetCreate,
    TrainingDatasetResponse,
    CodeSampleCreate,
    CodeSampleResponse,
    TrainingJobCreate,
    TrainingJobResponse,
    TrainingMetricsResponse,
    PaginatedCodeSamples,
)

router = APIRouter()


# Datasets
@router.get("/datasets", response_model=List[TrainingDatasetResponse])
async def get_datasets():
    """Get all training datasets"""
    return await MLTrainingController.get_datasets()


@router.post("/datasets", response_model=TrainingDatasetResponse)
async def create_dataset(data: TrainingDatasetCreate):
    """Create a new training dataset"""
    return await MLTrainingController.create_dataset(data)


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Delete a training dataset"""
    await MLTrainingController.delete_dataset(dataset_id)
    return {"message": "Dataset deleted successfully"}


# Code Samples
@router.get("/datasets/{dataset_id}/samples", response_model=PaginatedCodeSamples)
async def get_code_samples(
    dataset_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get code samples from a dataset with pagination"""
    return await MLTrainingController.get_code_samples(dataset_id, page, limit)


@router.post("/datasets/{dataset_id}/samples", response_model=CodeSampleResponse)
async def add_code_sample(dataset_id: str, data: CodeSampleCreate):
    """Add a code sample to dataset"""
    return await MLTrainingController.add_code_sample(dataset_id, data)


@router.delete("/datasets/{dataset_id}/samples/{sample_id}")
async def delete_code_sample(dataset_id: str, sample_id: str):
    """Delete a code sample"""
    await MLTrainingController.delete_code_sample(dataset_id, sample_id)
    return {"message": "Code sample deleted successfully"}


# Training Jobs
@router.get("/jobs", response_model=List[TrainingJobResponse])
async def get_training_jobs():
    """Get all training jobs"""
    return await MLTrainingController.get_training_jobs()


@router.post("/jobs", response_model=TrainingJobResponse)
async def start_training(data: TrainingJobCreate):
    """Start a new training job"""
    return await MLTrainingController.start_training(data)


# Metrics
@router.get("/metrics", response_model=TrainingMetricsResponse)
async def get_metrics():
    """Get training metrics overview"""
    return await MLTrainingController.get_metrics()


# Export/Import (placeholder - to be implemented)
@router.get("/datasets/{dataset_id}/export")
async def export_dataset(dataset_id: str):
    """Export dataset as JSON"""
    # TODO: Implement export functionality
    return {"message": "Export not yet implemented"}


@router.post("/datasets/import")
async def import_dataset():
    """Import dataset from JSON file"""
    # TODO: Implement import functionality
    return {"message": "Import not yet implemented"}
