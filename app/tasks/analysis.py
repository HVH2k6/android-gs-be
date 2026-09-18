"""
Analysis Pipeline Background Tasks
"""
from datetime import datetime
from app.tasks.celery import celery
from app.database import prisma
import structlog

logger = structlog.get_logger()


@celery.task(name="run_analysis_pipeline")
async def run_analysis_pipeline(analysis_run_id: str):
    """
    Run the complete analysis pipeline for a session

    Pipeline stages:
    1. Syntax Check (tree-sitter)
    2. Static Analysis (custom rules)
    3. Build Check (Gradle in Docker)
    4. Lint Check (Android Lint/Detekt)
    5. Requirement Evaluation
    6. RAG Search (if needed)
    7. LLM Analysis (if needed)
    """
    logger.info("Starting analysis pipeline", analysis_run_id=analysis_run_id)

    try:
        # Update status to RUNNING
        await prisma.analysisrun.update(
            where={"id": analysis_run_id},
            data={
                "status": "RUNNING",
                "currentStage": "SYNTAX_CHECK",
            }
        )

        # TODO: Implement actual analysis stages
        # Stage 1: Syntax Check
        # Stage 2: Static Analysis
        # Stage 3: Build Check
        # Stage 4: Lint Check
        # Stage 5: Requirement Evaluation
        # Stage 6: RAG Search
        # Stage 7: LLM Analysis

        # For now, mark as completed
        await prisma.analysisrun.update(
            where={"id": analysis_run_id},
            data={
                "status": "COMPLETED",
                "completedAt": datetime.utcnow(),
            }
        )

        logger.info("Analysis pipeline completed", analysis_run_id=analysis_run_id)

    except Exception as e:
        logger.error("Analysis pipeline failed", analysis_run_id=analysis_run_id, error=str(e))
        await prisma.analysisrun.update(
            where={"id": analysis_run_id},
            data={
                "status": "FAILED",
                "errorMessage": str(e),
                "completedAt": datetime.utcnow(),
            }
        )
        raise


@celery.task(name="process_file_change")
async def process_file_change(session_id: str, file_path: str):
    """
    Process a file change event (debounced)
    Creates an analysis run for the changed file
    """
    logger.info("Processing file change", session_id=session_id, file_path=file_path)

    # Create analysis run
    analysis_run = await prisma.analysisrun.create(
        data={
            "sessionId": session_id,
            "triggeredBy": "file_change",
            "status": "PENDING",
        }
    )

    # Queue analysis pipeline
    run_analysis_pipeline.delay(analysis_run.id)
