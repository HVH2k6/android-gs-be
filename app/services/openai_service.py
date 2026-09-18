"""OpenAI service for analyzing build errors when rules don't match."""
import httpx
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

OPENAI_MODEL = "gpt-4o-mini"

# Must stay in sync with the IssueCategory / IssueSeverity enums in schema.prisma.
VALID_CATEGORIES = {
    "SYNTAX_ERROR", "BUILD_ERROR", "LOGIC_ERROR", "STYLE_WARNING",
    "SECURITY_ISSUE", "PERFORMANCE", "BEST_PRACTICE", "REQUIREMENT_VIOLATION",
}
VALID_SEVERITIES = {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}

SYSTEM_PROMPT = """Bạn là trợ lý lập trình Android chuyên phân tích lỗi compile.

Nhiệm vụ: Phân tích lỗi compile Java/Kotlin và trả về JSON với format:
{
  "category": "SYNTAX_ERROR" | "BUILD_ERROR" | "LOGIC_ERROR" | "STYLE_WARNING" | "SECURITY_ISSUE" | "PERFORMANCE" | "BEST_PRACTICE",
  "severity": "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "title": "Tiêu đề ngắn gọn (< 60 ký tự)",
  "message": "Giải thích nguyên nhân lỗi bằng tiếng Việt",
  "suggestion": "Hướng dẫn fix cụ thể, từng bước",
  "doc_reference": "Link tài liệu chính thức (nếu có)"
}

Lưu ý:
- Dùng tiếng Việt thân thiện, dễ hiểu cho sinh viên
- Suggestion phải cụ thể, không chung chung
- Nếu không chắc chắn doc_reference thì để null"""


async def analyze_build_error_with_openai(raw_error: str, file_path: str) -> Optional[dict]:
    """
    Call OpenAI API to analyze build error.

    Returns:
        dict with keys: category, severity, title, message, suggestion, doc_reference
        None if API call fails
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("openai_api_key_missing")
        return None

    try:
        user_prompt = f"""Lỗi compile:
```
{raw_error}
```

File: {file_path}

Phân tích lỗi này và trả về JSON theo format đã định."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"}
                }
            )

            if response.status_code != 200:
                logger.error("openai_api_error", status=response.status_code, body=response.text[:200])
                return None

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            import json
            parsed = json.loads(content)

            # The values go straight into Prisma enum columns, so anything the
            # model invents outside the enum would fail the insert.
            if parsed.get("category") not in VALID_CATEGORIES:
                parsed["category"] = "BUILD_ERROR"
            if parsed.get("severity") not in VALID_SEVERITIES:
                parsed["severity"] = "MEDIUM"

            for field in ("title", "message", "suggestion"):
                if not parsed.get(field):
                    logger.warning("openai_missing_field", field=field)
                    return None

            logger.info("openai_analysis_success",
                       category=parsed.get("category"),
                       title=parsed.get("title"))

            return parsed

    except Exception as e:
        logger.error("openai_service_exception", error=str(e), error_type=type(e).__name__)
        return None
