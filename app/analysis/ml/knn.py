"""
K-Nearest Neighbors implemented from scratch (no scikit-learn).

Trade-off documented in ML_ANALYSIS.md: prediction is O(n * d) per query
because it compares against every stored training vector. Acceptable for
the dataset sizes expected in early MVP phases (hundreds of samples).
"""
import math
from collections import Counter
from typing import List, Sequence, Tuple


Vector = Sequence[float]


def _euclidean(a: Vector, b: Vector) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _cosine_distance(a: Vector, b: Vector) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    similarity = dot / (norm_a * norm_b)
    similarity = max(-1.0, min(1.0, similarity))
    return 1.0 - similarity


_METRICS = {
    "euclidean": _euclidean,
    "cosine": _cosine_distance,
}


class KNNClassifier:
    """Classic K-NN classifier: no training phase, just stores the data."""

    def __init__(self, k: int = 5, metric: str = "cosine"):
        if metric not in _METRICS:
            raise ValueError(f"Unsupported metric: {metric}. Use one of {list(_METRICS)}")
        self.k = k
        self.metric = metric
        self._distance = _METRICS[metric]
        self._X: List[Vector] = []
        self._y: List[str] = []

    def fit(self, X: List[Vector], y: List[str]) -> None:
        if len(X) != len(y):
            raise ValueError("X and y must have the same length")
        self._X = list(X)
        self._y = list(y)

    @property
    def is_fitted(self) -> bool:
        return len(self._X) > 0

    def neighbors(self, x: Vector, k: int = None) -> List[Tuple[float, str]]:
        """Return the k closest (distance, label) pairs, sorted ascending."""
        k = k or self.k
        distances = [(self._distance(x, xi), yi) for xi, yi in zip(self._X, self._y)]
        distances.sort(key=lambda pair: pair[0])
        return distances[:k]

    def predict_one(self, x: Vector) -> Tuple[str, float]:
        """Predict a single sample. Returns (label, confidence).

        confidence = weighted vote share of the winning label among the
        k nearest neighbors (closer neighbors count more).
        """
        if not self.is_fitted:
            return "UNKNOWN", 0.0

        neighbors = self.neighbors(x)
        weights = Counter()
        for dist, label in neighbors:
            weight = 1.0 / (dist + 1e-9)
            weights[label] += weight

        total_weight = sum(weights.values())
        if total_weight == 0:
            return "UNKNOWN", 0.0

        winner, winner_weight = weights.most_common(1)[0]
        confidence = winner_weight / total_weight
        return winner, confidence

    def predict(self, X: List[Vector]) -> List[Tuple[str, float]]:
        return [self.predict_one(x) for x in X]
