"""
AST-based feature extraction for Kotlin/Java source files.

Uses tree-sitter (a deterministic parser generator, not an ML/AI model) to
build a real syntax tree and derive numeric features from it. These
features feed both the rule engine (app/analysis/rules/android_rules.py)
and the from-scratch ML classifiers (app/analysis/ml/).
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from tree_sitter import Language, Node, Parser
import tree_sitter_java as tsjava
import tree_sitter_kotlin as tskotlin

# Fixed column order shared by every consumer of the feature vector
# (KNN, Decision Tree, CodeQualityPredictor). Keep this list stable.
FEATURE_NAMES = [
    "lines_of_code",
    "num_classes",
    "num_methods",
    "max_nesting_depth",
    "cyclomatic_complexity",
    "comment_ratio",
    "uses_viewmodel",
    "uses_recyclerview",
    "uses_findviewbyid",
    "uses_livedata",
    "has_context_leak_risk",
]

_LANGUAGES = {
    "kotlin": Language(tskotlin.language()),
    "java": Language(tsjava.language()),
}

_CLASS_NODE_TYPES = {
    "kotlin": {"class_declaration", "object_declaration"},
    "java": {"class_declaration", "interface_declaration", "enum_declaration"},
}

_METHOD_NODE_TYPES = {
    "kotlin": {"function_declaration"},
    "java": {"method_declaration", "constructor_declaration"},
}

_BLOCK_NODE_TYPES = {
    "kotlin": {
        "if_expression",
        "for_statement",
        "while_statement",
        "do_while_statement",
        "when_expression",
        "try_expression",
        "function_declaration",
        "class_body",
    },
    "java": {
        "if_statement",
        "for_statement",
        "while_statement",
        "do_statement",
        "switch_expression",
        "try_statement",
        "method_declaration",
        "class_body",
    },
}

_DECISION_NODE_TYPES = {
    "kotlin": {
        "if_expression",
        "for_statement",
        "while_statement",
        "do_while_statement",
        "when_entry",
        "catch_block",
    },
    "java": {
        "if_statement",
        "for_statement",
        "while_statement",
        "do_statement",
        "switch_block_statement_group",
        "catch_clause",
    },
}

_COMMENT_NODE_TYPES = {"line_comment", "block_comment", "comment"}

# Identifier names that mark Android-specific patterns. Sourced manually
# from developer.android.com (App Architecture guide, View binding guide,
# Memory leaks guide) rather than any crawler/model.
_VIEWMODEL_NAMES = {"ViewModel", "ViewModelProvider", "viewModels", "AndroidViewModel"}
_RECYCLERVIEW_NAMES = {"RecyclerView", "RecyclerViewAdapter", "LinearLayoutManager", "ListAdapter"}
_FINDVIEWBYID_NAMES = {"findViewById"}
_LIVEDATA_NAMES = {"LiveData", "MutableLiveData", "observe"}
_CONTEXT_LEAK_TYPE_NAMES = {"Context", "Activity", "AppCompatActivity"}


@dataclass
class ParsedFile:
    language: str
    source: bytes
    tree: object


def parse_source(source: str, language: str) -> Optional[ParsedFile]:
    """Parse source code into a tree-sitter tree. Returns None for unsupported languages."""
    lang = _LANGUAGES.get(language)
    if lang is None:
        return None

    parser = Parser(lang)
    source_bytes = source.encode("utf-8")
    tree = parser.parse(source_bytes)
    return ParsedFile(language=language, source=source_bytes, tree=tree)


def _iter_nodes(node: Node):
    yield node
    for child in node.children:
        yield from _iter_nodes(child)


def _node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")


def _collect_identifiers(node: Node, source: bytes) -> Set[str]:
    return {
        _node_text(n, source)
        for n in _iter_nodes(node)
        if n.type == "identifier"
    }


def _max_nesting_depth(node: Node, block_types: Set[str], depth: int = 0) -> int:
    is_block = node.type in block_types
    current_depth = depth + 1 if is_block else depth

    if not node.children:
        return current_depth

    return max(
        (_max_nesting_depth(child, block_types, current_depth) for child in node.children),
        default=current_depth,
    )


def _has_context_field_leak(root: Node, language: str, source: bytes) -> bool:
    """
    Heuristic for the "static Context leak" mistake documented at
    developer.android.com/topic/performance/memory#leaks:
    a class holds a Context/Activity-typed field inside a `companion object`
    (Kotlin) or a `static` field (Java) instead of using ApplicationContext.
    """
    for node in _iter_nodes(root):
        if language == "kotlin" and node.type == "companion_object":
            field_types = _collect_identifiers(node, source)
            if field_types & _CONTEXT_LEAK_TYPE_NAMES:
                return True

        if language == "java" and node.type == "field_declaration":
            text = _node_text(node, source)
            if "static" in text:
                field_types = _collect_identifiers(node, source)
                if field_types & _CONTEXT_LEAK_TYPE_NAMES:
                    return True

    return False


def extract(source: str, language: str) -> Dict[str, float]:
    """
    Extract a fixed-order feature vector from a Kotlin/Java source string.

    Returns zeroed-out features (not random) when the language is
    unsupported or the source fails to parse into any recognizable node.
    """
    parsed = parse_source(source, language)
    lines_of_code = source.count("\n") + 1 if source else 0

    if parsed is None:
        return {name: 0.0 for name in FEATURE_NAMES} | {"lines_of_code": float(lines_of_code)}

    root = parsed.tree.root_node
    all_nodes = list(_iter_nodes(root))

    class_types = _CLASS_NODE_TYPES[language]
    method_types = _METHOD_NODE_TYPES[language]
    block_types = _BLOCK_NODE_TYPES[language]
    decision_types = _DECISION_NODE_TYPES[language]

    num_classes = sum(1 for n in all_nodes if n.type in class_types)
    num_methods = sum(1 for n in all_nodes if n.type in method_types)
    max_nesting_depth = _max_nesting_depth(root, block_types)
    cyclomatic_complexity = 1 + sum(1 for n in all_nodes if n.type in decision_types)

    comment_lines = sum(
        _node_text(n, parsed.source).count("\n") + 1
        for n in all_nodes
        if n.type in _COMMENT_NODE_TYPES
    )
    comment_ratio = comment_lines / lines_of_code if lines_of_code else 0.0

    identifiers = _collect_identifiers(root, parsed.source)

    return {
        "lines_of_code": float(lines_of_code),
        "num_classes": float(num_classes),
        "num_methods": float(num_methods),
        "max_nesting_depth": float(max_nesting_depth),
        "cyclomatic_complexity": float(cyclomatic_complexity),
        "comment_ratio": float(comment_ratio),
        "uses_viewmodel": float(bool(identifiers & _VIEWMODEL_NAMES)),
        "uses_recyclerview": float(bool(identifiers & _RECYCLERVIEW_NAMES)),
        "uses_findviewbyid": float(bool(identifiers & _FINDVIEWBYID_NAMES)),
        "uses_livedata": float(bool(identifiers & _LIVEDATA_NAMES)),
        "has_context_leak_risk": float(_has_context_field_leak(root, language, parsed.source)),
    }


def to_vector(features: Dict[str, float]) -> List[float]:
    """Convert a feature dict into the fixed-order vector used by ML models."""
    return [features.get(name, 0.0) for name in FEATURE_NAMES]
