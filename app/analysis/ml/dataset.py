"""
Builds real training data (features + labels) for the from-scratch ML
classifiers, replacing the np.random placeholders that used to live in
scripts/train_ml_models.py.

Two sources feed the dataset:
1. Seed examples: a handful of Kotlin/Java snippets written by hand to
   demonstrate each rule in app/analysis/rules/android_rules.py (both the
   violating and the clean version). This lets training start on day one
   without a single real student submission, and unlike random data the
   labels are derived deterministically from the rule engine.
2. Real project files (once available from the database): same feature
   extraction + rule evaluation pipeline, no synthetic data involved.
"""
import random
from typing import Dict, List, Tuple

from app.analysis.parser import ast_features
from app.analysis.rules import android_rules

Vector = List[float]


# --------------------------------------------------------------------------
# Seed examples — hand-written, not scraped, not random.
# --------------------------------------------------------------------------

SEED_SNIPPETS: List[Tuple[str, str]] = [
    # (language, source)
    ("kotlin", """
class LoginActivity {
    companion object {
        var appContext: Context? = null
    }
}
"""),  # violates ANDROID_CONTEXT_LEAK

    ("kotlin", """
package com.example

import android.app.Application

class MyApplication : Application() {
    fun init() {
        val appContext = this.applicationContext
    }
}
"""),  # clean: uses applicationContext, no leak

    ("kotlin", """
class LoginActivity {
    fun onCreate() {
        val btn = findViewById<Button>(R.id.btn)
        val input = findViewById<EditText>(R.id.input)
    }
}
"""),  # violates ANDROID_FINDVIEWBYID_WITHOUT_VIEWMODEL

    ("kotlin", """
package com.example

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModels

class LoginActivity {
    private val viewModel: LoginViewModel by viewModels()

    fun onCreate() {
        val btn = findViewById<Button>(R.id.btn)
    }
}

class LoginViewModel : ViewModel() {
    fun login(password: String) {
        if (password.isEmpty()) {
            return
        }
    }
}
"""),  # clean: ViewModel used alongside findViewById

    ("kotlin", """
class MessageAdapter {
    fun bindAll(recyclerView: RecyclerView) {
        recyclerView.toString()
    }
}
"""),  # violates ANDROID_RECYCLERVIEW_WITHOUT_ADAPTER_PATTERN (too few methods)

    ("kotlin", """
package com.example

import androidx.recyclerview.widget.RecyclerView

class MessageAdapter : RecyclerView.Adapter<MessageAdapter.ViewHolder>() {
    class ViewHolder(view: View) : RecyclerView.ViewHolder(view)

    fun onCreateViewHolder() {}
    fun onBindViewHolder() {}
    fun getItemCount(): Int = 0
    fun setupLayoutManager() {}
}
"""),  # clean: adapter pattern with multiple methods

    ("kotlin", """
class OrderProcessor {
    fun process(a: Int, b: Int, c: Int, d: Int) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    if (d > 0) {
                        while (a > b) {
                            when (c) {
                                1 -> println(1)
                                2 -> println(2)
                                else -> println(0)
                            }
                            a -= 1
                        }
                    }
                }
            }
        }
    }
}
"""),  # violates ANDROID_HIGH_CYCLOMATIC_COMPLEXITY / ANDROID_DEEP_NESTING

    ("kotlin", """
package com.example

/**
 * Simple utility class that formats currency values for display.
 * Kept intentionally small and well documented.
 */
class CurrencyFormatter {
    // Formats a raw amount into a localized currency string
    fun format(amount: Double): String {
        return "$" + amount.toString()
    }
}
"""),  # clean: low complexity, documented

    ("java", """
public class LoginActivity {
    public static Context appContext;

    public void onCreate() {
        appContext = this;
    }
}
"""),  # violates ANDROID_CONTEXT_LEAK (java static field)

    ("java", """
public class UserRepository {
    public User findUser(String id) {
        return database.query(id);
    }
}
"""),  # clean java example
]


def build_seed_dataset() -> Tuple[List[Vector], List[str]]:
    """Extract features + derive labels for every hand-written seed snippet."""
    X: List[Vector] = []
    y: List[str] = []

    for language, source in SEED_SNIPPETS:
        features = ast_features.extract(source, language)
        matches = android_rules.evaluate(features)
        label = android_rules.derive_quality_label(features, matches)

        X.append(ast_features.to_vector(features))
        y.append(label)

    return X, y


def build_dataset_from_files(files: List[Dict[str, str]]) -> Tuple[List[Vector], List[str]]:
    """
    Build a dataset from real project files.

    Args:
        files: list of {"content": str, "language": "kotlin" | "java"}
    """
    X: List[Vector] = []
    y: List[str] = []

    for file in files:
        language = file.get("language")
        content = file.get("content", "")
        if language not in ("kotlin", "java") or not content.strip():
            continue

        features = ast_features.extract(content, language)
        matches = android_rules.evaluate(features)
        label = android_rules.derive_quality_label(features, matches)

        X.append(ast_features.to_vector(features))
        y.append(label)

    return X, y


def train_test_split(
    X: List[Vector], y: List[str], test_size: float = 0.2, seed: int = 42
) -> Tuple[List[Vector], List[Vector], List[str], List[str]]:
    """Shuffle + split into train/test sets without depending on scikit-learn."""
    if len(X) != len(y):
        raise ValueError("X and y must have the same length")

    indices = list(range(len(X)))
    random.Random(seed).shuffle(indices)

    split_point = max(1, int(len(indices) * (1 - test_size))) if len(indices) > 1 else len(indices)

    train_idx = indices[:split_point]
    test_idx = indices[split_point:]

    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]

    return X_train, X_test, y_train, y_test


def accuracy(y_true: List[str], y_pred: List[str]) -> float:
    """Simple accuracy metric (correct / total) without scikit-learn."""
    if not y_true:
        return 0.0
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)
