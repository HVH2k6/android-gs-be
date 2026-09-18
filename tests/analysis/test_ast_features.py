from app.analysis.parser import ast_features


def test_detects_findviewbyid_without_viewmodel():
    source = """
class LoginActivity {
    fun onCreate() {
        val btn = findViewById<Button>(R.id.btn)
    }
}
"""
    features = ast_features.extract(source, "kotlin")

    assert features["uses_findviewbyid"] == 1.0
    assert features["uses_viewmodel"] == 0.0
    assert features["num_classes"] == 1.0


def test_detects_viewmodel_usage():
    source = """
package com.example

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModels

class LoginActivity {
    private val viewModel: LoginViewModel by viewModels()
}

class LoginViewModel : ViewModel()
"""
    features = ast_features.extract(source, "kotlin")

    assert features["uses_viewmodel"] == 1.0
    assert features["num_classes"] == 2.0


def test_detects_context_leak_in_companion_object():
    source = """
class LoginActivity {
    companion object {
        var appContext: Context? = null
    }
}
"""
    features = ast_features.extract(source, "kotlin")

    assert features["has_context_leak_risk"] == 1.0


def test_no_context_leak_when_using_application_context():
    source = """
package com.example

import android.app.Application

class MyApplication : Application() {
    fun init() {
        val appContext = this.applicationContext
    }
}
"""
    features = ast_features.extract(source, "kotlin")

    assert features["has_context_leak_risk"] == 0.0


def test_unsupported_language_returns_zeroed_features():
    features = ast_features.extract("print('hi')", "python")

    assert features["num_classes"] == 0.0
    assert features["uses_viewmodel"] == 0.0
    assert features["lines_of_code"] == 1.0


def test_to_vector_uses_fixed_column_order():
    features = ast_features.extract("class Foo", "kotlin")
    vector = ast_features.to_vector(features)

    assert len(vector) == len(ast_features.FEATURE_NAMES)
    assert vector == [features[name] for name in ast_features.FEATURE_NAMES]
