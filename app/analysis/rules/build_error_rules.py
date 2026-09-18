"""
Pattern rules for Gradle/Kotlin/Java compile & build error messages.

Unlike android_rules.py (which runs against an AST feature vector), these
rules match directly against the raw compiler/Gradle error text reported by
Android Studio, since a compile error never reaches AST parsing.
"""
import re
from dataclasses import dataclass
from typing import Optional, Pattern


@dataclass(frozen=True)
class BuildErrorRule:
    id: str
    category: str        # SYNTAX_ERROR, BUILD_ERROR, LOGIC_ERROR (must match IssueCategory enum)
    severity: str         # must match IssueSeverity enum
    title: str
    pattern: Pattern
    message_template: str    # may reference {0}, {1}... from regex groups
    suggestion: str
    doc_reference: str


RULES: list[BuildErrorRule] = [
    BuildErrorRule(
        id="UNRESOLVED_REFERENCE",
        category="SYNTAX_ERROR",
        severity="HIGH",
        title="Không tìm thấy tham chiếu (Unresolved reference)",
        pattern=re.compile(r"[Uu]nresolved reference:?\s*'?([\w.]+)'?"),
        message_template="Không tìm thấy '{0}'. Có thể do chưa import, đặt tên sai, hoặc biến/hàm chưa được khai báo.",
        suggestion="Kiểm tra lại tên '{0}' có đúng chính tả không, đã import đúng package chưa, hoặc đã khai báo biến/hàm đó chưa.",
        doc_reference="https://kotlinlang.org/docs/packages.html#imports",
    ),
    BuildErrorRule(
        id="TYPE_MISMATCH",
        category="SYNTAX_ERROR",
        severity="HIGH",
        title="Sai kiểu dữ liệu (Type mismatch)",
        pattern=re.compile(r"[Tt]ype mismatch:\s*inferred type is\s*([\w.<>?]+)\s*but\s*([\w.<>?]+)\s*was expected"),
        message_template="Đang truyền kiểu {0} nhưng nơi nhận cần kiểu {1}.",
        suggestion="Ép kiểu hoặc chuyển đổi giá trị sang {1} trước khi dùng, hoặc sửa lại khai báo cho khớp kiểu.",
        doc_reference="https://kotlinlang.org/docs/basic-types.html",
    ),
    BuildErrorRule(
        id="INCOMPATIBLE_TYPES_JAVA",
        category="SYNTAX_ERROR",
        severity="HIGH",
        title="Sai kiểu dữ liệu (Java incompatible types)",
        pattern=re.compile(r"incompatible types:\s*([\w.<>?\[\]]+)\s*cannot be converted to\s*([\w.<>?\[\]]+)"),
        message_template="Kiểu {0} không thể chuyển đổi sang {1}.",
        suggestion="Kiểm tra lại kiểu trả về của method hoặc biến, đảm bảo khớp với kiểu được khai báo. Nếu method trả void thì không thể gán vào biến.",
        doc_reference="https://docs.oracle.com/javase/tutorial/java/nutsandbolts/datatypes.html",
    ),
    BuildErrorRule(
        id="CANNOT_FIND_SYMBOL",
        category="SYNTAX_ERROR",
        severity="HIGH",
        title="Không tìm thấy symbol (Java)",
        pattern=re.compile(r"cannot find symbol[\s\S]*?symbol:\s*\w+\s+([\w.]+)"),
        message_template="Không tìm thấy symbol '{0}'. Thường do thiếu import, sai tên class/method, hoặc chưa build lại sau khi đổi tên.",
        suggestion="Kiểm tra import và tên '{0}', hoặc chạy lại Gradle sync nếu vừa đổi tên class/method.",
        doc_reference="https://developer.android.com/studio/build",
    ),
    BuildErrorRule(
        id="MISSING_CLOSING_BRACKET",
        category="SYNTAX_ERROR",
        severity="MEDIUM",
        title="Thiếu dấu đóng (bracket/parenthesis)",
        pattern=re.compile(r"[Ee]xpecting\s*'([)\}\]])'"),
        message_template="Thiếu dấu '{0}' ở đâu đó trong file, compiler dừng lại vì cấu trúc code chưa khép kín.",
        suggestion="Rà lại các cặp dấu ( ), { }, [ ] gần vị trí lỗi báo, thường lỗi nằm ở dòng ngay phía trên.",
        doc_reference="https://kotlinlang.org/docs/basic-syntax.html",
    ),
    BuildErrorRule(
        id="MISSING_SEMICOLON",
        category="SYNTAX_ERROR",
        severity="MEDIUM",
        title="Thiếu dấu chấm phẩy (Java)",
        pattern=re.compile(r"';'\s*expected"),
        message_template="Thiếu dấu ';' ở cuối câu lệnh Java.",
        suggestion="Thêm dấu ';' vào cuối dòng lệnh. Lưu ý Kotlin không cần dấu ';' nhưng Java bắt buộc phải có.",
        doc_reference="https://docs.oracle.com/javase/tutorial/java/nutsandbolts/expressions.html",
    ),
    BuildErrorRule(
        id="DUPLICATE_CLASS",
        category="BUILD_ERROR",
        severity="CRITICAL",
        title="Trùng khai báo class (Duplicate class)",
        pattern=re.compile(r"[Dd]uplicate class\s*([\w.]+)"),
        message_template="Class '{0}' được khai báo nhiều hơn một lần trong project, có thể do trùng file hoặc trùng dependency.",
        suggestion="Kiểm tra có 2 file cùng khai báo class '{0}' không, hoặc có dependency trùng nhau trong build.gradle.",
        doc_reference="https://developer.android.com/studio/build/dependencies",
    ),
    BuildErrorRule(
        id="MANIFEST_MERGER_FAILED",
        category="BUILD_ERROR",
        severity="CRITICAL",
        title="Lỗi merge AndroidManifest.xml",
        pattern=re.compile(r"[Mm]anifest merger failed"),
        message_template="AndroidManifest.xml từ project và một thư viện đang xung đột thuộc tính (thường là attribute trùng nhau).",
        suggestion="Mở AndroidManifest.xml, thêm tools:replace hoặc tools:node vào tag bị xung đột theo gợi ý chi tiết trong log Gradle.",
        doc_reference="https://developer.android.com/studio/build/manifest-merge",
    ),
    BuildErrorRule(
        id="GRADLE_DEPENDENCY_RESOLUTION_FAILED",
        category="BUILD_ERROR",
        severity="CRITICAL",
        title="Không resolve được dependency Gradle",
        pattern=re.compile(r"[Cc]ould not (?:resolve|find)\s*([\w.:\-]+)"),
        message_template="Gradle không tải được dependency '{0}', có thể do sai version, thiếu repository, hoặc mất mạng.",
        suggestion="Kiểm tra tên/version của '{0}' trong build.gradle, đảm bảo repository (google()/mavenCentral()) đã khai báo đúng.",
        doc_reference="https://developer.android.com/studio/build/dependencies",
    ),
    BuildErrorRule(
        id="NULL_POINTER_COMPILE_HINT",
        category="LOGIC_ERROR",
        severity="MEDIUM",
        title="Có khả năng null (Kotlin nullability)",
        pattern=re.compile(r"[Oo]nly safe \(\?\.\) or non-null asserted \(!!\.\) calls are allowed"),
        message_template="Biến đang được dùng có thể null nhưng bạn đang gọi trực tiếp mà không kiểm tra.",
        suggestion="Dùng safe call (?.) kèm xử lý null, hoặc kiểm tra null trước bằng if/let thay vì dùng !! nếu không chắc chắn giá trị luôn tồn tại.",
        doc_reference="https://kotlinlang.org/docs/null-safety.html",
    ),
]


def match_error(raw_error: str) -> Optional[tuple[BuildErrorRule, tuple]]:
    """Return the first matching rule and its regex groups, or None."""
    for rule in RULES:
        m = rule.pattern.search(raw_error)
        if m:
            return rule, m.groups()
    return None


def format_with_groups(template: str, groups: tuple) -> str:
    """Fill {0}, {1}... placeholders, tolerating fewer groups than placeholders."""
    try:
        return template.format(*groups)
    except (IndexError, KeyError):
        return template
