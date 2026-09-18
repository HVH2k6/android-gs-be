"""
Machine Learning Models for Code Analysis
Implements ML-based code quality prediction and issue detection using
from-scratch K-NN and Decision Tree implementations (no scikit-learn,
no pretrained/embedding models such as CodeBERT or an LLM).
"""
from typing import Any, Dict, List, Optional

import joblib
import structlog

from app.analysis.ml.decision_tree import DecisionTreeClassifier
from app.analysis.ml.knn import KNNClassifier
from app.analysis.parser import ast_features

logger = structlog.get_logger()


class CodeQualityPredictor:
    """
    Predict code quality using a from-scratch Decision Tree.
    Features: complexity, LOC, method count, etc.
    Output: EXCELLENT, GOOD, FAIR, POOR
    """

    def __init__(self):
        self.model = DecisionTreeClassifier(max_depth=15, min_samples_split=10)
        self.is_trained = False

    def extract_features(self, code_metrics: Dict) -> List[float]:
        """
        Extract a feature vector from code metrics, in the same fixed
        column order used by app.analysis.parser.ast_features.

        Args:
            code_metrics: {
                'cyclomatic_complexity': int,
                'lines_of_code': int,
                'num_methods': int,
                'num_classes': int,
                'max_nesting_depth': int,
                'comment_ratio': float,
                'duplicate_ratio': float,
            }
        """
        return [
            code_metrics.get('lines_of_code', 0),
            code_metrics.get('num_classes', 0),
            code_metrics.get('num_methods', 0),
            code_metrics.get('max_nesting_depth', 0),
            code_metrics.get('cyclomatic_complexity', 0),
            code_metrics.get('comment_ratio', 0.0),
            code_metrics.get('uses_viewmodel', 0.0),
            code_metrics.get('uses_recyclerview', 0.0),
            code_metrics.get('uses_findviewbyid', 0.0),
            code_metrics.get('uses_livedata', 0.0),
            code_metrics.get('has_context_leak_risk', 0.0),
        ]

    def train(self, X_train: List[List[float]], y_train: List[str]):
        """Train the model"""
        self.model.fit(X_train, y_train)
        self.is_trained = True
        logger.info("Quality predictor trained", samples=len(X_train))

    def predict(self, code_metrics: Dict) -> Dict[str, Any]:
        """
        Predict code quality

        Returns:
            {
                'quality': 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR',
                'confidence': float,
                'feature_importance': Dict[str, float]
            }
        """
        if not self.is_trained:
            logger.warning("Model not trained, returning default")
            return {'quality': 'FAIR', 'confidence': 0.0}

        features = self.extract_features(code_metrics)
        prediction, confidence = self.model.predict_one(features)

        return {
            'quality': prediction,
            'confidence': confidence,
            'feature_importance': self._get_feature_importance()
        }

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores (sum of information gain per feature)"""
        return self.model.feature_importances(ast_features.FEATURE_NAMES)

    def save(self, path: str):
        """Save model to disk"""
        joblib.dump(self.model, path)
        logger.info("Model saved", path=path)

    def load(self, path: str):
        """Load model from disk"""
        self.model = joblib.load(path)
        self.is_trained = True
        logger.info("Model loaded", path=path)


class IssueClassifier:
    """
    Classify code issues using a from-scratch Decision Tree.
    Output: BUG, CODE_SMELL, PERFORMANCE, SECURITY
    """

    def __init__(self):
        self.model = DecisionTreeClassifier(max_depth=10, min_samples_split=5)
        self.is_trained = False

    def train(self, X_train: List[List[float]], y_train: List[str]):
        """Train the classifier"""
        self.model.fit(X_train, y_train)
        self.is_trained = True

    def predict(self, features: List[float]) -> Dict[str, Any]:
        """Predict issue type"""
        if not self.is_trained:
            return {'type': 'UNKNOWN', 'confidence': 0.0}

        prediction, confidence = self.model.predict_one(features)

        return {
            'type': prediction,
            'confidence': confidence
        }


class CodeSimilarityDetector:
    """
    Find similar code using a from-scratch K-NN over AST-derived feature
    vectors (no CodeBERT / sentence-transformers / any pretrained model).
    """

    def __init__(self, k: int = 5):
        self.knn = KNNClassifier(k=k, metric="cosine")
        self.code_database: List[Dict] = []
        self._vectors: List[List[float]] = []

    def add_code_samples(self, code_samples: List[str], metadata: List[Dict], languages: Optional[List[str]] = None):
        """
        Add code samples to the database.

        Args:
            code_samples: List of code strings
            metadata: List of dicts with {id, student_id, assignment_id, ...}
            languages: Optional per-sample language ("kotlin"/"java"); if
                omitted, each metadata entry's "language" key is used, or
                "kotlin" as a last resort.
        """
        for i, code in enumerate(code_samples):
            language = (
                languages[i] if languages else metadata[i].get("language", "kotlin")
            )
            features = ast_features.extract(code, language)
            self._vectors.append(ast_features.to_vector(features))
            self.code_database.append(metadata[i])

        # A KNNClassifier needs a "label" per sample for its API; we reuse
        # the database index as a placeholder label since similarity search
        # doesn't classify anything, it only ranks neighbors.
        labels = [str(i) for i in range(len(self._vectors))]
        self.knn.fit(self._vectors, labels)
        logger.info("Code database updated", total_samples=len(self.code_database))

    def find_similar(self, query_code: str, k: int = 5, language: str = "kotlin") -> List[Dict[str, Any]]:
        """
        Find k most similar code samples

        Returns:
            List of {
                'metadata': Dict,
                'similarity_score': float,
                'distance': float
            }
        """
        if not self.knn.is_fitted:
            logger.warning("Similarity search not available, no samples indexed")
            return []

        features = ast_features.extract(query_code, language)
        query_vector = ast_features.to_vector(features)

        neighbors = self.knn.neighbors(query_vector, k=k)

        results = []
        for dist, label in neighbors:
            idx = int(label)
            results.append({
                'metadata': self.code_database[idx],
                'similarity_score': 1 - dist,
                'distance': dist,
            })

        return results

    def detect_plagiarism(self,
                         student_code: str,
                         threshold: float = 0.85,
                         language: str = "kotlin") -> Optional[Dict]:
        """
        Detect potential plagiarism

        Args:
            student_code: Code to check
            threshold: Similarity threshold (0.85 = 85% similar)

        Returns:
            None if no plagiarism detected, otherwise metadata of similar code
        """
        similar_codes = self.find_similar(student_code, k=3, language=language)

        for result in similar_codes:
            if result['similarity_score'] >= threshold:
                return {
                    'plagiarism_detected': True,
                    'similar_submission': result['metadata'],
                    'similarity_score': result['similarity_score']
                }

        return None


class MLModelManager:
    """
    Centralized manager for all ML models
    """

    def __init__(self):
        self.quality_predictor = CodeQualityPredictor()
        self.issue_classifier = IssueClassifier()
        self.similarity_detector = CodeSimilarityDetector()

    async def predict_quality(self, code_metrics: Dict) -> Dict[str, Any]:
        """Predict code quality"""
        return self.quality_predictor.predict(code_metrics)

    async def classify_issue(self, features: List[float]) -> Dict[str, Any]:
        """Classify code issue"""
        return self.issue_classifier.predict(features)

    async def find_similar_code(self, code: str, k: int = 5) -> List[Dict]:
        """Find similar code"""
        return self.similarity_detector.find_similar(code, k)

    async def detect_plagiarism(self, code: str, threshold: float = 0.85) -> Optional[Dict]:
        """Detect plagiarism"""
        return self.similarity_detector.detect_plagiarism(code, threshold)

    def load_models(self, models_dir: str):
        """Load pre-trained models"""
        try:
            self.quality_predictor.load(f"{models_dir}/quality_predictor.joblib")
            logger.info("ML models loaded successfully")
        except Exception as e:
            logger.warning("Failed to load models", error=str(e))


# Global instance
ml_models = MLModelManager()
