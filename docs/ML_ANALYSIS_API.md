# API ML Analysis - Tích hợp Android Studio

API thuật toán Machine Learning để phát hiện lỗi, sửa lỗi và báo lỗi cho Android Studio.

## 🚀 Endpoints

Base URL: `http://localhost:8000/api/ml-analysis`

### 1. Phát hiện lỗi (Detect Errors)

**Endpoint:** `POST /api/ml-analysis/detect`

Phân tích code và phát hiện các lỗi/vấn đề sử dụng ML + rule-based analysis.

**Request Body:**
```json
{
  "code": "class MainActivity : AppCompatActivity() {\n    companion object {\n        var context: Context? = null\n    }\n}",
  "file_path": "app/src/main/java/com/example/MainActivity.kt",
  "language": "kotlin"
}
```

**Response:**
```json
{
  "success": true,
  "file_path": "app/src/main/java/com/example/MainActivity.kt",
  "language": "kotlin",
  "issues": [
    {
      "id": "uuid-123",
      "category": "PERFORMANCE",
      "severity": "HIGH",
      "title": "Giữ Context trong static/companion field có thể gây memory leak",
      "message": "Một field kiểu Context/Activity được giữ trong companion object...",
      "line_start": 2,
      "line_end": 4,
      "rule_id": "ANDROID_CONTEXT_LEAK",
      "confidence": 1.0,
      "doc_reference": "https://developer.android.com/topic/performance/memory#leaks"
    }
  ],
  "quality_score": "POOR",
  "quality_confidence": 0.85,
  "metrics": {
    "lines_of_code": 50,
    "num_classes": 1,
    "num_methods": 3,
    "cyclomatic_complexity": 8,
    "max_nesting_depth": 3,
    "comment_ratio": 0.05
  },
  "analyzed_at": "2024-01-20T10:30:00Z"
}
```

### 2. Sửa lỗi (Fix Errors)

**Endpoint:** `POST /api/ml-analysis/fix`

Tạo đề xuất sửa lỗi cho các issue đã phát hiện.

**Request Body:**
```json
{
  "code": "class MainActivity : AppCompatActivity() {...}",
  "file_path": "app/src/main/java/com/example/MainActivity.kt",
  "language": "kotlin",
  "issue_ids": ["uuid-123"],
  "auto_apply": false
}
```

**Response:**
```json
{
  "success": true,
  "file_path": "app/src/main/java/com/example/MainActivity.kt",
  "original_code": "class MainActivity...",
  "fixed_code": "// Code đã được sửa (nếu auto_apply=true)",
  "suggestions": [
    {
      "issue_id": "uuid-123",
      "fix_type": "REPLACE",
      "original_code": "var context: Context? = null",
      "fixed_code": "// TODO: Replace with WeakReference<Context>",
      "explanation": "Sử dụng WeakReference hoặc Application Context...",
      "confidence": 0.8,
      "line_start": 3,
      "line_end": 3
    }
  ],
  "issues_fixed": 1,
  "issues_remaining": 2
}
```

### 3. Tạo thông báo (Create Notification)

**Endpoint:** `POST /api/ml-analysis/notify`

Tạo notification để hiển thị trong Android Studio.

**Query Parameters:**
- `notification_type`: ERROR | WARNING | INFO | SUCCESS
- `title`: Tiêu đề thông báo
- `message`: Nội dung thông báo
- `file_path` (optional): Đường dẫn file
- `line_number` (optional): Số dòng

**Example:**
```
POST /api/ml-analysis/notify?notification_type=ERROR&title=Memory%20Leak&message=Context%20leak%20detected&file_path=MainActivity.kt&line_number=5
```

**Response:**
```json
{
  "notification_type": "ERROR",
  "title": "Memory Leak",
  "message": "Context leak detected",
  "file_path": "MainActivity.kt",
  "line_number": 5,
  "actions": null,
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 4. Phân tích nhiều file (Batch Analysis)

**Endpoint:** `POST /api/ml-analysis/batch`

Phân tích nhiều file cùng lúc.

**Request Body:**
```json
{
  "files": [
    {
      "file_path": "MainActivity.kt",
      "code": "class MainActivity...",
      "language": "kotlin"
    },
    {
      "file_path": "UserViewModel.kt",
      "code": "class UserViewModel...",
      "language": "kotlin"
    }
  ],
  "project_name": "MyAndroidApp"
}
```

**Response:**
```json
{
  "success": true,
  "total_files": 2,
  "files_analyzed": 2,
  "total_issues": 5,
  "results": [
    {
      "success": true,
      "file_path": "MainActivity.kt",
      "issues": [...],
      "quality_score": "GOOD",
      ...
    }
  ]
}
```

### 5. Health Check

**Endpoint:** `GET /api/ml-analysis/health`

Kiểm tra trạng thái service.

**Response:**
```json
{
  "status": "healthy",
  "service": "ml-analysis",
  "features": [
    "error_detection",
    "error_fixing",
    "batch_analysis",
    "notifications"
  ]
}
```

## 📊 Categories & Severity Levels

### Categories
- `BUG`: Lỗi logic/runtime
- `PERFORMANCE`: Vấn đề hiệu năng
- `SECURITY`: Lỗ hổng bảo mật
- `BEST_PRACTICE`: Vi phạm best practice
- `STYLE_WARNING`: Vấn đề về code style

### Severity Levels
- `CRITICAL`: Lỗi nghiêm trọng, cần sửa ngay
- `HIGH`: Lỗi quan trọng
- `MEDIUM`: Lỗi trung bình
- `LOW`: Lỗi nhỏ
- `INFO`: Thông tin/gợi ý

## 🔧 Tích hợp Android Studio Plugin

### Ví dụ code Kotlin cho plugin:

```kotlin
// 1. Gọi API detect errors
suspend fun analyzeCurrentFile(editor: Editor): ErrorDetectionResponse? {
    val code = editor.document.text
    val filePath = editor.virtualFile.path
    
    val request = CodeAnalysisRequest(
        code = code,
        filePath = filePath,
        language = "kotlin"
    )
    
    return apiClient.post("/api/ml-analysis/detect", request)
}

// 2. Hiển thị issues trong editor
fun showIssuesInEditor(editor: Editor, issues: List<DetectedIssue>) {
    issues.forEach { issue ->
        val highlighter = editor.markupModel.addRangeHighighter(
            /* start */ getOffset(issue.lineStart),
            /* end */ getOffset(issue.lineEnd),
            /* layer */ HighlighterLayer.ERROR,
            /* attributes */ getAttributes(issue.severity),
            /* target */ HighlighterTargetArea.EXACT_RANGE
        )
        
        // Add tooltip
        highlighter.errorStripeTooltip = issue.message
    }
}

// 3. Tạo quick fix actions
fun createQuickFix(issue: DetectedIssue): IntentionAction {
    return object : IntentionAction {
        override fun getText() = "Fix: ${issue.title}"
        
        override fun invoke(project: Project, editor: Editor, file: PsiFile) {
            // Gọi API fix
            val fixResponse = apiClient.post("/api/ml-analysis/fix", 
                ErrorFixRequest(
                    code = editor.document.text,
                    filePath = file.virtualFile.path,
                    issueIds = listOf(issue.id),
                    autoApply = true
                )
            )
            
            // Apply fix
            if (fixResponse.fixedCode != null) {
                editor.document.setText(fixResponse.fixedCode)
            }
        }
    }
}
```

## 🎯 Use Cases

1. **Real-time analysis**: Gọi `/detect` khi user dừng typing (debounce 500ms)
2. **Pre-commit hook**: Gọi `/batch` để check toàn bộ changed files
3. **Code review**: Tích hợp vào CI/CD pipeline
4. **Learning tool**: Hiển thị explanation + doc_reference cho học sinh

## 📝 Notes

- API hoàn toàn stateless, không cần authentication cho demo
- Nếu cần auth: thêm `Authorization: Bearer <token>` header
- Rate limit: Chưa có, có thể thêm nếu cần
- Max file size: Khuyến nghị < 10,000 LOC per request

## 🚀 Chạy Backend

```bash
cd back-end
python -m uvicorn main:app --reload
```

API docs: http://localhost:8000/docs
