"""
Manually curated rule/pattern set derived from developer.android.com
(App Architecture guide, Memory leaks guide, Common mistakes, Lint rules
documentation, Permissions guide). This is NOT scraped automatically and
NOT an ML model — each rule below is a deterministic check against the
feature vector produced by app.analysis.parser.ast_features.

Rules are used for two purposes:
1. Run directly as a deterministic rule-based analysis layer (flow.md
   Rule 6: prefer deterministic analysis before ML).
2. Derive real training labels for the from-scratch ML classifiers,
   replacing the previous np.random dummy labels.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List


Features = Dict[str, float]


@dataclass(frozen=True)
class Rule:
    id: str
    category: str      # must match IssueCategory enum in prisma/schema.prisma
    severity: str       # must match IssueSeverity enum in prisma/schema.prisma
    title: str
    message: str
    suggestion: str      # concrete fix suggestion, one or two sentences, no lecturing
    doc_reference: str
    match: Callable[[Features], bool]


@dataclass(frozen=True)
class MatchedRule:
    rule: Rule


# --------------------------------------------------------------------------
# Rule definitions
# --------------------------------------------------------------------------
# Each `match` predicate reads only the feature dict produced by
# ast_features.extract(), so rules stay independent from parser internals.

RULES: List[Rule] = [
    Rule(
        id="ANDROID_CONTEXT_LEAK",
        category="PERFORMANCE",
        severity="HIGH",
        title="Giữ Context trong static/companion field có thể gây memory leak",
        message=(
            "Một field kiểu Context/Activity được giữ trong companion object "
            "(static-like) sẽ sống lâu hơn Activity, gây rò rỉ bộ nhớ khi "
            "Activity bị destroy."
        ),
        suggestion=(
            "Đổi field sang applicationContext, hoặc bọc trong WeakReference<Context> "
            "nếu vẫn cần tham chiếu tới Activity."
        ),
        doc_reference="https://developer.android.com/topic/performance/memory#leaks",
        match=lambda f: f.get("has_context_leak_risk", 0.0) > 0,
    ),
    Rule(
        id="ANDROID_FINDVIEWBYID_WITHOUT_VIEWMODEL",
        category="BEST_PRACTICE",
        severity="MEDIUM",
        title="Dùng findViewById trực tiếp thay vì kiến trúc ViewModel/View Binding",
        message=(
            "findViewById() được dùng nhưng không thấy ViewModel trong file. "
            "Theo App Architecture guide, nên tách state/logic khỏi View bằng "
            "ViewModel để tránh logic nghiệp vụ nằm trong Activity/Fragment."
        ),
        suggestion=(
            "Chuyển state và logic xử lý sang một ViewModel, dùng LiveData hoặc "
            "StateFlow để Activity/Fragment chỉ còn nhiệm vụ hiển thị."
        ),
        doc_reference="https://developer.android.com/topic/architecture#recommended-app-arch",
        match=lambda f: f.get("uses_findviewbyid", 0.0) > 0 and f.get("uses_viewmodel", 0.0) == 0,
    ),
    Rule(
        id="ANDROID_RECYCLERVIEW_WITHOUT_ADAPTER_PATTERN",
        category="PERFORMANCE",
        severity="MEDIUM",
        title="RecyclerView được dùng nhưng không rõ Adapter/ViewHolder pattern",
        message=(
            "Không tìm thấy dấu hiệu Adapter/ViewHolder cho RecyclerView. "
            "Việc bind view sai cách (ví dụ tạo lại view thay vì recycle) "
            "gây tốn hiệu năng khi danh sách dài."
        ),
        suggestion=(
            "Tạo một Adapter kế thừa RecyclerView.Adapter với ViewHolder riêng, "
            "bind dữ liệu trong onBindViewHolder() thay vì xử lý trực tiếp trong Activity."
        ),
        doc_reference="https://developer.android.com/develop/ui/views/layout/recyclerview",
        match=lambda f: f.get("uses_recyclerview", 0.0) > 0 and f.get("num_methods", 0.0) < 2,
    ),
    Rule(
        id="ANDROID_HIGH_CYCLOMATIC_COMPLEXITY",
        category="STYLE_WARNING",
        severity="MEDIUM",
        title="Hàm/lớp có độ phức tạp điều kiện cao",
        message=(
            "Cyclomatic complexity vượt ngưỡng khuyến nghị (>10). Nên tách "
            "nhỏ hàm để dễ kiểm thử và giảm khả năng phát sinh lỗi logic."
        ),
        suggestion=(
            "Tách các nhánh điều kiện lớn thành hàm con có tên rõ nghĩa, "
            "mỗi hàm chỉ nên xử lý một luồng logic."
        ),
        doc_reference="https://developer.android.com/studio/write/lint",
        match=lambda f: f.get("cyclomatic_complexity", 0.0) > 10,
    ),
    Rule(
        id="ANDROID_DEEP_NESTING",
        category="STYLE_WARNING",
        severity="LOW",
        title="Code lồng nhau quá sâu",
        message=(
            "Độ sâu lồng nhau của block (if/for/when/try) vượt quá 5 cấp, "
            "làm giảm khả năng đọc hiểu code."
        ),
        suggestion=(
            "Đảo điều kiện để return sớm (early return/guard clause), hoặc "
            "trích phần lồng sâu ra một hàm riêng."
        ),
        doc_reference="https://developer.android.com/kotlin/style-guide",
        match=lambda f: f.get("max_nesting_depth", 0.0) > 5,
    ),
    Rule(
        id="ANDROID_LOW_COMMENT_RATIO_LARGE_FILE",
        category="STYLE_WARNING",
        severity="LOW",
        title="File lớn nhưng thiếu comment giải thích",
        message=(
            "File có trên 100 dòng code nhưng tỉ lệ comment dưới 5%. Nên bổ "
            "sung giải thích cho các đoạn logic quan trọng."
        ),
        suggestion=(
            "Thêm vài dòng comment ngắn ở những đoạn logic không hiển nhiên, "
            "không cần comment cho code đã tự giải thích qua tên biến/hàm."
        ),
        doc_reference="https://developer.android.com/kotlin/style-guide",
        match=lambda f: f.get("lines_of_code", 0.0) > 100 and f.get("comment_ratio", 0.0) < 0.05,
    ),
    Rule(
        id="ANDROID_NO_CLASS_STRUCTURE",
        category="BEST_PRACTICE",
        severity="LOW",
        title="File không chứa class/object nào",
        message=(
            "Không phát hiện class/object nào trong file .kt/.java. Đảm bảo "
            "file thuộc đúng cấu trúc project Android (mỗi file nguồn nên "
            "chứa ít nhất một class/object)."
        ),
        suggestion=(
            "Kiểm tra lại file có đúng là file nguồn Kotlin/Java hợp lệ không, "
            "hoặc bọc code trong một class/object nếu đang để rời."
        ),
        doc_reference="https://developer.android.com/kotlin/style-guide",
        match=lambda f: f.get("lines_of_code", 0.0) > 5 and f.get("num_classes", 0.0) == 0,
    ),
]


def evaluate(features: Features) -> List[MatchedRule]:
    """Run every rule against a feature vector, return the ones that match."""
    return [MatchedRule(rule=rule) for rule in RULES if rule.match(features)]


_SEVERITY_WEIGHT = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "INFO": 0,
}


def worst_severity(matches: List[MatchedRule]) -> str:
    if not matches:
        return "INFO"
    return max(matches, key=lambda m: _SEVERITY_WEIGHT.get(m.rule.severity, 0)).rule.severity


def derive_quality_label(features: Features, matches: List[MatchedRule]) -> str:
    """
    Deterministic quality label used as ML training target, replacing the
    previous np.random placeholder in scripts/train_ml_models.py.

    Rationale: severity of the worst matched rule dominates; complexity is
    used as a tie-breaker among "no issue found" samples so the dataset
    isn't just two extreme buckets.
    """
    if not matches:
        complexity = features.get("cyclomatic_complexity", 0.0)
        return "EXCELLENT" if complexity <= 5 else "GOOD"

    severity = worst_severity(matches)
    if severity in ("CRITICAL", "HIGH"):
        return "POOR"
    if severity == "MEDIUM":
        return "FAIR"
    return "GOOD"
