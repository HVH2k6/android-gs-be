"""
Training scripts for ML models
Run these scripts to train models on historical data.

Uses real AST-derived features (app.analysis.parser.ast_features) and
labels/issue types derived deterministically from the hand-curated Android
rule set (app.analysis.rules.android_rules) — no np.random placeholders,
no scikit-learn, no pretrained models.
"""
import asyncio
from typing import Dict, List

import structlog

from app.analysis.ml import dataset
from app.analysis.ml_models import CodeQualityPredictor, IssueClassifier
from app.analysis.parser import ast_features
from app.analysis.rules import android_rules
from app.database import prisma

logger = structlog.get_logger()

MIN_QUALITY_SAMPLES = 50
MIN_ISSUE_SAMPLES = 100


async def collect_training_data() -> List[Dict]:
    """
    Collect training data from database.

    Returns:
        List of {'session_id', 'features', 'quality_label'}
    """
    logger.info("Collecting training data from database")

    sessions = await prisma.learningsession.find_many(
        where={'status': 'COMPLETED'},
        include={
            'project': {
                'include': {'files': True}
            }
        }
    )

    training_data = []

    for session in sessions:
        if not session.project or not session.project.files:
            continue

        features = extract_project_features(session.project)
        matches = android_rules.evaluate(features)
        quality_label = android_rules.derive_quality_label(features, matches)

        training_data.append({
            'session_id': session.id,
            'features': features,
            'quality_label': quality_label
        })

    logger.info("Training data collected", samples=len(training_data))
    return training_data


def extract_project_features(project) -> Dict[str, float]:
    """
    Extract real AST-based features for a project, aggregated across its
    Kotlin/Java files (max per-file values, since a single bad file should
    dominate the project-level signal).

    Returns a feature dict in the fixed column order defined by
    app.analysis.parser.ast_features.FEATURE_NAMES.
    """
    files = [f for f in project.files if f.language in ('kotlin', 'java') and f.content.strip()]

    if not files:
        return {name: 0.0 for name in ast_features.FEATURE_NAMES}

    per_file = [ast_features.extract(f.content, f.language) for f in files]

    aggregated = {name: 0.0 for name in ast_features.FEATURE_NAMES}
    sum_only = {"lines_of_code", "num_classes", "num_methods"}

    for name in ast_features.FEATURE_NAMES:
        values = [f[name] for f in per_file]
        if name in sum_only:
            aggregated[name] = float(sum(values))
        else:
            aggregated[name] = float(max(values))

    return aggregated


async def train_quality_predictor(save_path: str = "models/quality_predictor.joblib"):
    """
    Train code quality prediction model
    """
    logger.info("Starting quality predictor training")

    training_data = await collect_training_data()

    if len(training_data) < MIN_QUALITY_SAMPLES:
        logger.warning("Not enough training data", samples=len(training_data))
        return None

    X = [ast_features.to_vector(row['features']) for row in training_data]
    y = [row['quality_label'] for row in training_data]

    X_train, X_test, y_train, y_test = dataset.train_test_split(X, y, test_size=0.2, seed=42)

    model = CodeQualityPredictor()
    model.train(X_train, y_train)

    y_pred = [model.model.predict_one(x)[0] for x in X_test]
    acc = dataset.accuracy(y_test, y_pred)

    logger.info("Model trained",
                accuracy=f"{acc:.3f}",
                train_samples=len(X_train),
                test_samples=len(X_test))

    model.save(save_path)
    logger.info("Model saved", path=save_path)

    return model


async def train_issue_classifier(save_path: str = "models/issue_classifier.joblib"):
    """
    Train code issue classification model.

    Issue type here is the matched rule's category (IssueCategory), and
    features come from re-parsing the offending file rather than random
    vectors.
    """
    logger.info("Starting issue classifier training")

    issues = await prisma.codeissue.find_many(
        include={'file': True}
    )

    usable = [issue for issue in issues if issue.file and issue.file.content.strip()
              and issue.file.language in ('kotlin', 'java')]

    if len(usable) < MIN_ISSUE_SAMPLES:
        logger.warning("Not enough issue data", samples=len(usable))
        return None

    X = []
    y = []
    for issue in usable:
        features = ast_features.extract(issue.file.content, issue.file.language)
        X.append(ast_features.to_vector(features))
        y.append(issue.category)

    X_train, X_test, y_train, y_test = dataset.train_test_split(X, y, test_size=0.2, seed=42)

    classifier = IssueClassifier()
    classifier.train(X_train, y_train)

    y_pred = [classifier.predict(x)['type'] for x in X_test]
    acc = dataset.accuracy(y_test, y_pred)

    logger.info("Issue classifier trained", accuracy=f"{acc:.3f}")

    return classifier


async def build_similarity_index():
    """
    Build code similarity index from all student submissions
    """
    logger.info("Building code similarity index")

    from app.analysis.ml_models import ml_models

    files = await prisma.projectfile.find_many(
        where={'language': {'in': ['kotlin', 'java']}},
        include={'project': {'include': {'session': True}}}
    )

    code_samples = []
    metadata = []
    languages = []

    for file in files:
        code_samples.append(file.content)
        languages.append(file.language)
        metadata.append({
            'file_id': file.id,
            'session_id': file.project.sessionId,
            'student_id': file.project.session.studentId,
            'path': file.path
        })

    ml_models.similarity_detector.add_code_samples(code_samples, metadata, languages)

    logger.info("Similarity index built", total_codes=len(code_samples))


async def main():
    """
    Main training script
    Run this periodically (e.g., end of semester) to retrain models
    """
    logger.info("Starting ML model training pipeline")

    await prisma.connect()

    try:
        await train_quality_predictor()
        await train_issue_classifier()
        await build_similarity_index()

        logger.info("ML training pipeline completed successfully")

    except Exception as e:
        logger.error("Training pipeline failed", error=str(e))
        raise
    finally:
        await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
