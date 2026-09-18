"""
ML Training Controller for Admin Dashboard
Handles dataset management, training jobs, and code samples
"""
from fastapi import HTTPException, status
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import structlog
import math

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
from app.analysis.ml_models import ml_models
from app.analysis.parser import ast_features

logger = structlog.get_logger()

# In-memory storage (replace with database in production)
_datasets: Dict[str, Dict] = {}
_code_samples: Dict[str, List[Dict]] = {}  # dataset_id -> [samples]
_training_jobs: Dict[str, Dict] = {}


class MLTrainingController:
    """ML Training management for admin dashboard"""

    @staticmethod
    async def get_datasets() -> List[TrainingDatasetResponse]:
        """Get all training datasets"""
        datasets = []
        for dataset_id, dataset in _datasets.items():
            samples = _code_samples.get(dataset_id, [])
            quality_dist = {}
            for sample in samples:
                label = sample['quality_label']
                quality_dist[label] = quality_dist.get(label, 0) + 1

            datasets.append(TrainingDatasetResponse(
                id=dataset['id'],
                name=dataset['name'],
                description=dataset['description'],
                total_samples=len(samples),
                quality_distribution=quality_dist,
                created_at=dataset['created_at'],
                updated_at=dataset['updated_at'],
            ))

        return sorted(datasets, key=lambda x: x.created_at, reverse=True)

    @staticmethod
    async def create_dataset(data: TrainingDatasetCreate) -> TrainingDatasetResponse:
        """Create a new training dataset"""
        dataset_id = str(uuid.uuid4())
        now = datetime.utcnow()

        dataset = {
            'id': dataset_id,
            'name': data.name,
            'description': data.description,
            'created_at': now,
            'updated_at': now,
        }

        _datasets[dataset_id] = dataset
        _code_samples[dataset_id] = []

        logger.info("Dataset created", dataset_id=dataset_id, name=data.name)

        return TrainingDatasetResponse(
            **dataset,
            total_samples=0,
            quality_distribution={}
        )

    @staticmethod
    async def delete_dataset(dataset_id: str) -> None:
        """Delete a training dataset"""
        if dataset_id not in _datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        del _datasets[dataset_id]
        if dataset_id in _code_samples:
            del _code_samples[dataset_id]

        logger.info("Dataset deleted", dataset_id=dataset_id)

    @staticmethod
    async def get_code_samples(
        dataset_id: str,
        page: int = 1,
        limit: int = 20
    ) -> PaginatedCodeSamples:
        """Get code samples with pagination"""
        if dataset_id not in _datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        samples = _code_samples.get(dataset_id, [])
        total = len(samples)
        pages = math.ceil(total / limit) if total > 0 else 1

        start = (page - 1) * limit
        end = start + limit
        paginated_samples = samples[start:end]

        return PaginatedCodeSamples(
            samples=[CodeSampleResponse(**s) for s in paginated_samples],
            total=total,
            page=page,
            pages=pages
        )

    @staticmethod
    async def add_code_sample(
        dataset_id: str,
        data: CodeSampleCreate
    ) -> CodeSampleResponse:
        """Add a code sample to dataset"""
        if dataset_id not in _datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        # Extract features from code
        try:
            features = ast_features.extract(data.code, data.language)
        except Exception as e:
            logger.error("Feature extraction failed", error=str(e))
            features = {
                'lines_of_code': len(data.code.split('\n')),
                'cyclomatic_complexity': 0,
                'num_methods': 0,
                'num_classes': 0,
            }

        sample_id = str(uuid.uuid4())
        sample = {
            'id': sample_id,
            'code': data.code,
            'language': data.language,
            'quality_label': data.quality_label,
            'issue_category': None,
            'file_path': data.file_path,
            'metrics': {
                'lines_of_code': features.get('lines_of_code', 0),
                'cyclomatic_complexity': features.get('cyclomatic_complexity', 0),
                'num_methods': features.get('num_methods', 0),
                'num_classes': features.get('num_classes', 0),
            },
            'created_at': datetime.utcnow(),
        }

        if dataset_id not in _code_samples:
            _code_samples[dataset_id] = []

        _code_samples[dataset_id].append(sample)
        _datasets[dataset_id]['updated_at'] = datetime.utcnow()

        logger.info(
            "Code sample added",
            dataset_id=dataset_id,
            sample_id=sample_id,
            file_path=data.file_path
        )

        return CodeSampleResponse(**sample)

    @staticmethod
    async def delete_code_sample(dataset_id: str, sample_id: str) -> None:
        """Delete a code sample"""
        if dataset_id not in _datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        samples = _code_samples.get(dataset_id, [])
        _code_samples[dataset_id] = [s for s in samples if s['id'] != sample_id]
        _datasets[dataset_id]['updated_at'] = datetime.utcnow()

        logger.info("Code sample deleted", dataset_id=dataset_id, sample_id=sample_id)

    @staticmethod
    async def get_training_jobs() -> List[TrainingJobResponse]:
        """Get all training jobs"""
        jobs = [TrainingJobResponse(**job) for job in _training_jobs.values()]
        return sorted(jobs, key=lambda x: x.started_at or datetime.min, reverse=True)

    @staticmethod
    async def start_training(data: TrainingJobCreate) -> TrainingJobResponse:
        """Start a new training job"""
        if data.dataset_id not in _datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        samples = _code_samples.get(data.dataset_id, [])
        if len(samples) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset must have at least 10 samples to train"
            )

        job_id = str(uuid.uuid4())
        job = {
            'id': job_id,
            'dataset_id': data.dataset_id,
            'model_type': data.model_type,
            'status': 'PENDING',
            'accuracy': None,
            'precision': None,
            'recall': None,
            'f1_score': None,
            'started_at': datetime.utcnow(),
            'completed_at': None,
            'error_message': None,
        }

        _training_jobs[job_id] = job

        # Simulate training (in production, this would be a background task)
        try:
            await MLTrainingController._run_training(job_id, data.dataset_id, data.model_type)
        except Exception as e:
            job['status'] = 'FAILED'
            job['error_message'] = str(e)
            job['completed_at'] = datetime.utcnow()

        logger.info(
            "Training job started",
            job_id=job_id,
            dataset_id=data.dataset_id,
            model_type=data.model_type
        )

        return TrainingJobResponse(**job)

    @staticmethod
    async def _run_training(job_id: str, dataset_id: str, model_type: str) -> None:
        """Run the actual training (simplified version)"""
        job = _training_jobs[job_id]
        job['status'] = 'RUNNING'

        samples = _code_samples.get(dataset_id, [])

        # Prepare training data
        X_train = []
        y_train = []

        for sample in samples:
            features = ast_features.extract(sample['code'], sample['language'])
            X_train.append(ast_features.to_vector(features))
            y_train.append(sample['quality_label'])

        # Train model
        if model_type == 'quality_predictor':
            ml_models.quality_predictor.train(X_train, y_train)
            # Simulate metrics (in production, use actual train/test split)
            job['accuracy'] = 0.85 + (len(samples) / 1000) * 0.1  # Mock
            job['precision'] = 0.83
            job['recall'] = 0.82
            job['f1_score'] = 0.825

        job['status'] = 'COMPLETED'
        job['completed_at'] = datetime.utcnow()

        logger.info("Training completed", job_id=job_id, accuracy=job['accuracy'])

    @staticmethod
    async def get_metrics() -> TrainingMetricsResponse:
        """Get training metrics overview"""
        total_samples = sum(len(samples) for samples in _code_samples.values())
        active_jobs = sum(1 for job in _training_jobs.values() if job['status'] in ['PENDING', 'RUNNING'])
        completed_jobs = [job for job in _training_jobs.values() if job['status'] == 'COMPLETED']

        avg_accuracy = 0.0
        if completed_jobs:
            accuracies = [job['accuracy'] for job in completed_jobs if job['accuracy']]
            avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

        return TrainingMetricsResponse(
            total_datasets=len(_datasets),
            total_samples=total_samples,
            total_training_jobs=len(_training_jobs),
            active_jobs=active_jobs,
            models_trained=len(completed_jobs),
            average_accuracy=avg_accuracy
        )
