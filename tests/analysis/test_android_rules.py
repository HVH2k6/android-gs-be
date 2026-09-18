from app.analysis.parser import ast_features
from app.analysis.rules import android_rules


def test_context_leak_rule_matches():
    source = """
class LoginActivity {
    companion object {
        var appContext: Context? = null
    }
}
"""
    features = ast_features.extract(source, "kotlin")
    matches = android_rules.evaluate(features)

    matched_ids = {m.rule.id for m in matches}
    assert "ANDROID_CONTEXT_LEAK" in matched_ids


def test_clean_code_matches_no_rules():
    source = """
package com.example

class CurrencyFormatter {
    fun format(amount: Double): String {
        return "$" + amount.toString()
    }
}
"""
    features = ast_features.extract(source, "kotlin")
    matches = android_rules.evaluate(features)

    assert matches == []


def test_derive_quality_label_poor_on_high_severity():
    source = """
class LoginActivity {
    companion object {
        var appContext: Context? = null
    }
}
"""
    features = ast_features.extract(source, "kotlin")
    matches = android_rules.evaluate(features)
    label = android_rules.derive_quality_label(features, matches)

    assert label == "POOR"


def test_derive_quality_label_excellent_with_no_matches():
    source = """
package com.example

class CurrencyFormatter {
    fun format(amount: Double): String {
        return "$" + amount.toString()
    }
}
"""
    features = ast_features.extract(source, "kotlin")
    matches = android_rules.evaluate(features)
    label = android_rules.derive_quality_label(features, matches)

    assert label == "EXCELLENT"


def test_worst_severity_with_no_matches_is_info():
    assert android_rules.worst_severity([]) == "INFO"
