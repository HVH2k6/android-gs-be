# AI Android Learning Monitoring System - Backend Architecture

## Cấu trúc MVC đã được triển khai

```
back-end/
├── main.py                      # Entry point - FastAPI app initialization
├── app/
│   ├── __init__.py
│   ├── config.py                # Configuration & settings
│   ├── database.py              # Prisma database connection
│   │
│   ├── models/                  # Models (Prisma auto-generated)
│   │   └── __init__.py          # Re-exports common models
│   │
│   ├── schemas/                 # Pydantic schemas (request/response validation)
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication schemas
│   │   ├── courses.py           # Course & Assignment schemas
│   │   ├── sessions.py          # Learning Session schemas
│   │   ├── projects.py          # Project & File sync schemas
│   │   └── analysis.py          # Code Analysis schemas
│   │
│   ├── controllers/             # Business logic (Controller layer)
│   │   ├── __init__.py
│   │   ├── auth_controller.py   # Authentication logic
│   │   ├── course_controller.py # Course & Assignment logic
│   │   ├── session_controller.py # Learning Session logic
│   │   ├── project_controller.py # Project & File management
│   │   └── analysis_controller.py # Code Analysis orchestration
│   │
│   ├── routes/                  # API Routes (FastAPI routers)
│   │   ├── __init__.py
│   │   ├── auth.py              # /api/auth/*
│   │   ├── courses.py           # /api/courses/*
│   │   ├── assignments.py       # /api/assignments/*
│   │   ├── sessions.py          # /api/sessions/*
│   │   ├── projects.py          # /api/projects/*
│   │   └── analysis.py          # /api/analysis/*
│   │
│   ├── services/                # (TODO) Additional services
│   ├── tasks/                   # Background tasks (Celery)
│   │   ├── __init__.py
│   │   ├── celery.py            # Celery configuration
│   │   └── analysis.py          # Analysis pipeline tasks
│   │
│   ├── websocket/               # WebSocket real-time communication
│   │   ├── __init__.py
│   │   └── manager.py           # WebSocket connection manager
│   │
│   ├── analysis/                # Analysis pipeline components (TODO)
│   │   └── __init__.py
│   │
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   └── helpers.py           # Helper functions
│   │
│   └── middleware/              # Custom middleware (TODO)
│       └── __init__.py
```

## Mô hình MVC

### 1. **Model Layer** (Prisma ORM)
- Định nghĩa trong `prisma/schema.prisma`
- Auto-generated Python models via `prisma-client-py`
- Re-exported trong `app/models/__init__.py` để dễ import

### 2. **Controller Layer** (`app/controllers/`)
Chứa business logic, xử lý dữ liệu:
- **AuthController**: JWT authentication, password hashing, user registration
- **CourseController**: Course management, enrollment logic
- **AssignmentController**: Assignment & requirement management
- **SessionController**: Learning session lifecycle
- **ProjectController**: File sync, versioning, hash deduplication
- **AnalysisController**: Code analysis orchestration

### 3. **Routes Layer** (`app/routes/`)
FastAPI routes - thin layer để nhận request và gọi controllers:
- Validation với Pydantic schemas
- Authentication dependencies
- Authorization checks
- Response formatting

### 4. **Schema Layer** (`app/schemas/`)
Pydantic models cho request/response validation:
- Type safety
- Auto-generated API documentation
- Request validation
- Response serialization

## API Endpoints đã triển khai

### Authentication (`/api/auth`)
```
POST   /api/auth/register    # Register new user
POST   /api/auth/login       # Login & get tokens
POST   /api/auth/refresh     # Refresh access token
GET    /api/auth/me          # Get current user
```

### Courses (`/api/courses`)
```
GET    /api/courses                    # List all courses
GET    /api/courses/{id}               # Get course details
GET    /api/courses/{id}/assignments   # Get course assignments
POST   /api/courses                    # Create course (Instructor/Admin)
```

### Assignments (`/api/assignments`)
```
GET    /api/assignments/{id}                   # Get assignment
GET    /api/assignments/{id}/requirements      # Get requirements
POST   /api/assignments                        # Create (Instructor/Admin)
POST   /api/assignments/{id}/requirements      # Add requirement (Instructor/Admin)
```

### Learning Sessions (`/api/sessions`)
```
POST   /api/sessions/start               # Start new session
GET    /api/sessions/{id}                # Get session details
PATCH  /api/sessions/{id}/status         # Update status
GET    /api/sessions/{id}/progress       # Get progress stats
```

### Projects (`/api/projects`)
```
POST   /api/projects/{session_id}/sync/initial       # Initial project sync
POST   /api/projects/{session_id}/sync/incremental   # Incremental sync
GET    /api/projects/{session_id}/files              # List files
GET    /api/projects/{session_id}/state              # Project state
```

### Analysis (`/api/analysis`)
```
POST   /api/analysis/run                      # Trigger analysis
GET    /api/analysis/{run_id}                 # Get analysis status
GET    /api/analysis/{run_id}/issues          # Get detected issues
GET    /api/analysis/{run_id}/feedback        # Get feedback
GET    /api/analysis/sessions/{id}/issues     # Get session issues
```

### WebSocket
```
WS     /ws/{session_id}                       # Real-time events
```

## Features đã triển khai

### ✅ Authentication & Authorization
- JWT token-based authentication
- Role-based access control (STUDENT, INSTRUCTOR, ADMIN)
- Password hashing with bcrypt
- Token refresh mechanism

### ✅ File Management
- xxHash64 content deduplication
- File versioning system
- Size limit validation (10MB per file, 100MB per project)
- Language detection from file extensions

### ✅ Session Management
- Session lifecycle (ACTIVE, PAUSED, COMPLETED, ABANDONED)
- Progress tracking
- Device pairing support

### ✅ Real-time Communication
- WebSocket connection management
- Session-based message broadcasting
- Event delivery system

### ✅ Background Tasks
- Celery task queue setup
- Analysis pipeline task structure (TODO: implement stages)
- File change processing

## Cách chạy

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
# Generate Prisma client
prisma generate

# Push schema to database
prisma db push
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env với database URL và API keys
```

### 4. Chạy server
```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 5. Chạy Celery worker
```bash
celery -A app.tasks.celery worker --loglevel=info
```

## TODO - Các phần cần triển khai tiếp

### Analysis Pipeline (`app/analysis/`)
- [ ] Tree-sitter parser integration
- [ ] Static analysis rules engine
- [ ] Docker sandbox execution
- [ ] Android Lint/Detekt integration
- [ ] Assignment requirement evaluator
- [ ] ML models integration
- [ ] RAG with pgvector
- [ ] LLM integration (GPT/Claude)

### Services (`app/services/`)
- [ ] Email service
- [ ] Notification service
- [ ] Cache service (Redis)

### Middleware (`app/middleware/`)
- [ ] Rate limiting
- [ ] Request logging
- [ ] Error handling

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] API endpoint tests

## Nguyên tắc thiết kế

1. **Separation of Concerns**: Routes → Controllers → Database
2. **Thin Routes**: Chỉ validate input và gọi controller
3. **Fat Controllers**: Business logic tập trung ở controller
4. **Schema Validation**: Pydantic schemas cho type safety
5. **Async/Await**: Full async support với Prisma và FastAPI
6. **Security First**: JWT auth, role-based access, input validation
7. **Scalability**: Background tasks với Celery, WebSocket cho real-time

## API Documentation

Sau khi chạy server, truy cập:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
