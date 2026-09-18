from app.analysis.ml.decision_tree import DecisionTreeClassifier


def _separable_dataset():
    # Single feature cleanly separates the two classes at threshold ~5.
    X = [[1.0], [2.0], [3.0], [4.0], [6.0], [7.0], [8.0], [9.0]]
    y = ["LOW", "LOW", "LOW", "LOW", "HIGH", "HIGH", "HIGH", "HIGH"]
    return X, y


def test_fits_and_predicts_separable_data():
    X, y = _separable_dataset()
    tree = DecisionTreeClassifier(max_depth=5, min_samples_split=2)
    tree.fit(X, y)

    assert tree.is_fitted

    label, confidence = tree.predict_one([1.5])
    assert label == "LOW"
    assert confidence == 1.0

    label, confidence = tree.predict_one([8.5])
    assert label == "HIGH"
    assert confidence == 1.0


def test_not_fitted_returns_unknown():
    tree = DecisionTreeClassifier()
    assert tree.is_fitted is False
    label, confidence = tree.predict_one([1.0])
    assert label == "UNKNOWN"
    assert confidence == 0.0


def test_feature_importances_sum_to_one():
    X, y = _separable_dataset()
    X = [[x[0], 0.0] for x in X]  # add a useless second feature
    tree = DecisionTreeClassifier(max_depth=5, min_samples_split=2)
    tree.fit(X, y)

    importances = tree.feature_importances(["useful", "useless"])
    assert importances["useless"] == 0.0
    assert importances["useful"] > 0.0
    assert abs(sum(importances.values()) - 1.0) < 1e-9
