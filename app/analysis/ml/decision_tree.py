"""
Decision Tree classifier implemented from scratch (no scikit-learn).

CART-style binary tree using Shannon entropy / information gain to choose
splits, matching the algorithm described in thuattoan.jpg / ML_ANALYSIS.md.
"""
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

Vector = Sequence[float]


def _entropy(labels: List[str]) -> float:
    if not labels:
        return 0.0
    counts = Counter(labels)
    total = len(labels)
    return -sum(
        (count / total) * math.log2(count / total)
        for count in counts.values()
        if count > 0
    )


def _majority_label(labels: List[str]) -> Tuple[str, float]:
    counts = Counter(labels)
    label, count = counts.most_common(1)[0]
    return label, count / len(labels)


@dataclass
class _Node:
    is_leaf: bool
    label: Optional[str] = None
    confidence: float = 0.0
    feature_index: Optional[int] = None
    threshold: Optional[float] = None
    gain: float = 0.0
    left: Optional["_Node"] = None
    right: Optional["_Node"] = None


class DecisionTreeClassifier:
    """Binary decision tree trained with information gain (entropy)."""

    def __init__(self, max_depth: int = 10, min_samples_split: int = 10):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self._root: Optional[_Node] = None
        self._num_features: int = 0
        self._feature_gain: Dict[int, float] = {}

    @property
    def is_fitted(self) -> bool:
        return self._root is not None

    def fit(self, X: List[Vector], y: List[str]) -> None:
        if len(X) != len(y):
            raise ValueError("X and y must have the same length")
        if not X:
            raise ValueError("Cannot fit on empty dataset")

        self._num_features = len(X[0])
        self._feature_gain = {i: 0.0 for i in range(self._num_features)}
        self._root = self._build(list(X), list(y), depth=0)

    def _build(self, X: List[Vector], y: List[str], depth: int) -> _Node:
        label, confidence = _majority_label(y)

        if (
            len(set(y)) == 1
            or len(y) < self.min_samples_split
            or depth >= self.max_depth
        ):
            return _Node(is_leaf=True, label=label, confidence=confidence)

        split = self._best_split(X, y)
        if split is None:
            return _Node(is_leaf=True, label=label, confidence=confidence)

        feature_index, threshold, gain, left_idx, right_idx = split
        self._feature_gain[feature_index] += gain

        left_X = [X[i] for i in left_idx]
        left_y = [y[i] for i in left_idx]
        right_X = [X[i] for i in right_idx]
        right_y = [y[i] for i in right_idx]

        return _Node(
            is_leaf=False,
            feature_index=feature_index,
            threshold=threshold,
            gain=gain,
            left=self._build(left_X, left_y, depth + 1),
            right=self._build(right_X, right_y, depth + 1),
        )

    def _best_split(self, X: List[Vector], y: List[str]):
        base_entropy = _entropy(y)
        if base_entropy == 0.0:
            return None

        n = len(y)
        best_gain = 0.0
        best = None

        for feature_index in range(self._num_features):
            values = sorted(set(x[feature_index] for x in X))
            if len(values) < 2:
                continue

            thresholds = [
                (values[i] + values[i + 1]) / 2.0 for i in range(len(values) - 1)
            ]

            for threshold in thresholds:
                left_idx = [i for i in range(n) if X[i][feature_index] <= threshold]
                right_idx = [i for i in range(n) if X[i][feature_index] > threshold]

                if not left_idx or not right_idx:
                    continue

                left_y = [y[i] for i in left_idx]
                right_y = [y[i] for i in right_idx]

                weighted_entropy = (
                    len(left_y) / n * _entropy(left_y)
                    + len(right_y) / n * _entropy(right_y)
                )
                gain = base_entropy - weighted_entropy

                if gain > best_gain:
                    best_gain = gain
                    best = (feature_index, threshold, gain, left_idx, right_idx)

        return best

    def predict_one(self, x: Vector) -> Tuple[str, float]:
        if not self.is_fitted:
            return "UNKNOWN", 0.0

        node = self._root
        while not node.is_leaf:
            if x[node.feature_index] <= node.threshold:
                node = node.left
            else:
                node = node.right

        return node.label, node.confidence

    def predict(self, X: List[Vector]) -> List[Tuple[str, float]]:
        return [self.predict_one(x) for x in X]

    def feature_importances(self, feature_names: List[str]) -> Dict[str, float]:
        """Sum of information gain contributed by each feature, normalized to 1."""
        total_gain = sum(self._feature_gain.values())
        if total_gain == 0:
            return {name: 0.0 for name in feature_names}

        return {
            feature_names[i]: self._feature_gain.get(i, 0.0) / total_gain
            for i in range(len(feature_names))
        }
