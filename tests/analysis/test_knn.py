from app.analysis.ml.knn import KNNClassifier


def _two_clusters():
    X = [
        [0.0, 0.0], [0.1, 0.1], [0.2, 0.0], [0.0, 0.2],
        [10.0, 10.0], [10.1, 10.1], [10.2, 10.0], [10.0, 10.2],
    ]
    y = ["A", "A", "A", "A", "B", "B", "B", "B"]
    return X, y


def test_predicts_nearest_cluster():
    X, y = _two_clusters()
    knn = KNNClassifier(k=3, metric="euclidean")
    knn.fit(X, y)

    label, confidence = knn.predict_one([0.05, 0.05])
    assert label == "A"
    assert confidence > 0.5

    label, confidence = knn.predict_one([10.05, 10.05])
    assert label == "B"
    assert confidence > 0.5


def test_not_fitted_returns_unknown():
    knn = KNNClassifier()
    assert knn.is_fitted is False
    label, confidence = knn.predict_one([1.0, 2.0])
    assert label == "UNKNOWN"
    assert confidence == 0.0


def test_cosine_metric_neighbors_ordering():
    X = [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]]
    y = ["A", "A", "B"]
    knn = KNNClassifier(k=2, metric="cosine")
    knn.fit(X, y)

    neighbors = knn.neighbors([1.0, 0.0], k=2)
    assert [label for _, label in neighbors] == ["A", "A"]
