# Hướng dẫn sử dụng Back-end MVC

## Tổng quan

Backend đã được xây dựng theo mô hình **Model-View-Controller (MVC)** với FastAPI:

- **Model**: Prisma ORM (định nghĩa trong `prisma/schema.prisma`)
- **Controller**: Business logic (`app/controllers/`)
- **Routes**: API endpoints (`app/routes/`) - tương đương View layer trong MVC truyền thống

## Cấu trúc đã tạo

```
✅ 32 files đã được tạo thành công

📁 app/
├── config.py                    # Cấu hình ứng dụng
├── database.py                  # Kết nối Prisma
├── 📁 models/                   # Models (auto-generated từ Prisma)
├── 📁 schemas/                  # 6 schemas (auth, courses, sessions, projects, analysis)
├── 📁 controllers/              # 5 controllers (auth, course, session, project, analysis)
├── 📁 routes/                   # 6 routes (auth, courses, assignments, sessions, projects, analysis)
├── 📁 tasks/                    # Celery background tasks
├── 📁 websocket/                # WebSocket manager
├── 📁 utils/                    # Helper functions
├── 📁 analysis/                 # Analysis pipeline (placeholder)
└── 📁 middleware/               # Middleware (placeholder)
```

## Các bước tiếp theo

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình Database

```bash
# Tạo file .env
cp .env.example .env

# Chỉnh sửa DATABASE_URL trong .env
# Ví dụ: DATABASE_URL="postgresql://user:password@localhost:5432/gs_android_learning"
```

### 3. Generate Prisma Client và Push Schema

```bash
# Generate Python client từ schema
prisma generate

# Push schema lên database (development)
prisma db push

# Hoặc tạo migration (production)
prisma migrate dev --name init
```

### 4. Chạy Backend

```bash
# Development mode với auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 5. Chạy Celery Worker (cho background tasks)

```bash
# Terminal riêng
celery -A app.tasks.celery worker --loglevel=info
```

### 6. Test API

Truy cập Swagger UI để test API:
```
http://localhost:8000/docs
```

## Cách sử dụng

### Ví dụ 1: Đăng ký và đăng nhập

```python
# POST /api/auth/register
{
  "email": "student@example.com",
  "password": "password123",
  "name": "Nguyen Van A",
  "role": "STUDENT"
}

# Response: access_token và refresh_token
```

### Ví dụ 2: Tạo Course (Instructor)

```python
# POST /api/courses
# Header: Authorization: Bearer {access_token}
{
  "code": "CS101",
  "title": "Android Development Basics",
  "description": "Learn Android fundamentals",
  "is_published": true
}
```

### Ví dụ 3: Start Learning Session (Student)

```python
# POST /api/sessions/start
# Header: Authorization: Bearer {access_token}
{
  "assignment_id": "clx...",
  "device_id": "device_abc123"  # Optional
}
```

### Ví dụ 4: Sync Project Files

```python
# POST /api/projects/{session_id}/sync/initial
{
  "project_name": "MyAndroidApp",
  "package_name": "com.example.myapp",
  "root_path": "/path/to/project",
  "files": [
    {
      "path": "app/src/main/java/com/example/MainActivity.kt",
      "content": "package com.example\n\nclass MainActivity {...}",
      "language": "kotlin"
    }
  ]
}
```

### Ví dụ 5: WebSocket Connection

```javascript
// JavaScript client
const ws = new WebSocket('ws://localhost:8000/ws/session_id_here');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  // Handle events: CODE_FEEDBACK, ISSUE_DETECTED, etc.
};

ws.send(JSON.stringify({
  type: 'ping',
  message: 'Hello from client'
}));
```

## Cấu trúc code pattern

### Controller Pattern

```python
# app/controllers/example_controller.py
class ExampleController:
    @staticmethod
    async def create_item(data: ItemCreate) -> ItemResponse:
        # 1. Validate business rules
        # 2. Call database operations
        # 3. Return response
        item = await prisma.item.create(data={...})
        return ItemResponse.model_validate(item)
```

### Route Pattern

```python
# app/routes/example.py
@router.post("/items", response_model=ItemResponse)
async def create_item(
    data: ItemCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    # 1. Get data from request (validated by Pydantic)
    # 2. Call controller
    # 3. Return response
    return await ExampleController.create_item(data)
```

### Schema Pattern

```python
# app/schemas/example.py
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    category: str

class ItemResponse(ItemBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # For Prisma model conversion
```

## Testing

```bash
# Chạy tests (khi đã viết)
pytest

# Với coverage
pytest --cov=app --cov-report=html
```

## Troubleshooting

### Lỗi: "Prisma client not generated"
```bash
prisma generate
```

### Lỗi: "Database connection failed"
```bash
# Kiểm tra DATABASE_URL trong .env
# Đảm bảo PostgreSQL đang chạy
```

### Lỗi: "Module not found"
```bash
# Đảm bảo đang ở đúng virtual environment
pip install -r requirements.txt
```

## Tài liệu tham khảo

- FastAPI: https://fastapi.tiangolo.com/
- Prisma Python: https://prisma-client-py.readthedocs.io/
- Pydantic: https://docs.pydantic.dev/
- Celery: https://docs.celeryproject.org/

---

**Backend đã sẵn sàng để phát triển thêm các tính năng phân tích code!** 🚀
