# AI Android Learning Monitoring System - Backend

Python FastAPI backend cho hệ thống giám sát học tập Android với AI.

## Tổng quan Kiến trúc

```
Student (Android App) ←→ WebSocket ←→ Python Backend ←→ PostgreSQL + pgvector
                                          ↓
                                    Analysis Pipeline
                                          ↓
                              ┌──────────────────────┐
                              │ Tree-sitter (AST)    │
                              │ Android Lint/Detekt  │
                              │ Gradle Build (Docker)│
                              │ Rule Engine          │
                              │ ML Models            │
                              │ RAG (pgvector)       │
                              │ LLM (GPT/Claude)     │
                              └──────────────────────┘
                                          ↓
                              Feedback + Progress
                                          ↓
                              WebSocket → Android App
```

## Yêu cầu Hệ thống

- Python 3.11+
- PostgreSQL 15+ với pgvector extension
- Redis 7+ (cho Celery task queue và cache)
- Docker (cho sandbox execution của Gradle/Lint)

## Cài đặt

### 1. Clone và Setup Environment

```bash
cd back-end
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Cấu hình Database

```bash
# Tạo database
createdb gs_android_learning

# Enable pgvector extension
psql gs_android_learning -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Environment Variables

```bash
cp .env.example .env
# Chỉnh sửa .env với thông tin database, API keys
```

### 4. Prisma Migration

```bash
# Generate Python client
prisma generate

# Push schema (development)
prisma db push

# Or migrate (production)
prisma migrate dev --name init
```

### 5. Khởi động Services

```bash
# Terminal 1: FastAPI Server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery Worker (background tasks)
celery -A app.tasks.celery worker --loglevel=info

# Terminal 3: Redis (nếu chưa chạy)
redis-server
```

## Cấu trúc Thư mục

```
back-end/
├── app/
│   ├── auth/              # Authentication & JWT
│   ├── api/               # API endpoints
│   │   ├── students/
│   │   ├── courses/
│   │   ├── assignments/
│   │   ├── sessions/
│   │   ├── projects/
│   │   └── analysis/
│   ├── analysis/          # Core analysis pipeline
│   │   ├── parser/        # Tree-sitter AST parsing
│   │   ├── static/        # Static analysis rules
│   │   ├── lint/          # Lint/Detekt integration
│   │   ├── sandbox/       # Docker sandbox execution
│   │   ├── rules/         # Assignment rule engine
│   │   ├── ml/            # ML models
│   │   ├── rag/           # RAG with pgvector
│   │   ├── llm/           # LLM integration
│   │   └── decision/      # Decision engine
│   ├── models/            # Prisma models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── tasks/             # Celery background tasks
│   ├── websocket/         # WebSocket handlers
│   ├── utils/             # Utilities
│   └── config.py          # Configuration
├── prisma/
│   ├── schema.prisma      # Database schema
│   ├── prisma.config.ts   # Prisma 7 config
│   └── README.md          # Schema documentation
├── tests/
├── logs/
├── .env.example
├── requirements.txt
└── main.py
```

## API Endpoints

### Authentication

```
POST   /api/auth/login
POST   /api/auth/register
POST   /api/auth/refresh
GET    /api/auth/me
```

### Courses & Assignments

```
GET    /api/courses
GET    /api/courses/{id}
GET    /api/courses/{id}/assignments
GET    /api/assignments/{id}
GET    /api/assignments/{id}/requirements
```

### Learning Sessions

```
POST   /api/sessions/start
GET    /api/sessions/{id}
PATCH  /api/sessions/{id}/status
GET    /api/sessions/{id}/progress
```

### Projects & Sync

```
POST   /api/projects/{id}/sync/initial
POST   /api/projects/{id}/sync/incremental
GET    /api/projects/{id}/files
GET    /api/projects/{id}/state
```

### Analysis

```
POST   /api/analysis/run
GET    /api/analysis/{run_id}
GET    /api/analysis/{run_id}/issues
GET    /api/analysis/{run_id}/feedback
```

### WebSocket

```
WS     /ws/{session_id}
```

Events:
- `CODE_FEEDBACK`
- `ISSUE_DETECTED`
- `ISSUE_RESOLVED`
- `REQUIREMENT_COMPLETED`
- `PROGRESS_UPDATED`
- `ANALYSIS_STARTED`
- `ANALYSIS_COMPLETED`

## Tính năng Chính

### 1. Device Pairing (Bảo mật)

Ngăn sinh viên A sync vào session của sinh viên B:

```python
# C# Agent scan QR code từ Android app
# QR chứa: pairing_token

# Backend xác thực và pair device
device = await prisma.device.update(
    where={'pairingToken': token},
    data={'isPaired': True}
)
```

### 2. Issue Fingerprinting (AST-based)

Không dùng line numbers (shift khi edit code):

```python
def generate_fingerprint(rule_id: str, scope: str, node: str) -> str:
    """Hash stable identifier không phụ thuộc line number"""
    return hashlib.sha256(
        f"{rule_id}:{scope}:{node}".encode()
    ).hexdigest()[:16]
```

### 3. Sandbox Execution (RCE Prevention)

Không bao giờ chạy code sinh viên trực tiếp trên host:

```python
# Chạy gradle build trong Docker container
result = await run_in_sandbox(
    image="gradle:8.5-jdk17",
    command=["./gradlew", "build"],
    cpu_limit="1.0",
    memory_limit="512m",
    timeout=60
)
```

### 4. Analysis Pipeline

```
File Change Event
    ↓
Debounce (1-3s)
    ↓
Update Project State
    ↓
Enqueue Background Task (Celery)
    ↓
┌─────────────────────────┐
│ 1. Syntax Check         │ ← tree-sitter (fast)
│    ├─ FAIL → Return     │
│    └─ PASS → Continue   │
│                         │
│ 2. Static Rules         │ ← Deterministic checks
│                         │
│ 3. Gradle Build         │ ← Docker sandbox
│                         │
│ 4. Lint/Detekt          │ ← Docker sandbox
│                         │
│ 5. Requirement Eval     │ ← Rule engine
│                         │
│ 6. RAG Search           │ ← pgvector (if needed)
│                         │
│ 7. LLM Analysis         │ ← GPT/Claude (if needed)
└─────────────────────────┘
    ↓
Decision Engine
    ↓
Generate Feedback
    ↓
Store Results
    ↓
Push via WebSocket
```

### 5. Realtime Event Outbox Pattern

Đảm bảo không mất WebSocket events:

```python
# Store event in database first
event = await prisma.realtimeevent.create(data={
    'sessionId': session_id,
    'eventType': 'ISSUE_RESOLVED',
    'payload': feedback_json,
    'status': 'PENDING'
})

# Background worker deliver events
# Retry on failure
# Mark SENT when acknowledged
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_analysis.py -v
```

## Deployment

### Development

```bash
uvicorn main:app --reload --port 8000
```

### Production

```bash
# Sử dụng Gunicorn + Uvicorn workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### Docker

```bash
docker build -t gs-android-backend .
docker run -p 8000:8000 \
  -e DATABASE_URL="..." \
  -e REDIS_URL="..." \
  gs-android-backend
```

## Monitoring

- Logs: `logs/backend.log`
- Metrics endpoint: `GET /metrics`
- Health check: `GET /health`

## Security Checklist

- [x] Device pairing với QR token
- [x] JWT authentication
- [x] File size limit (10MB per file, 100MB per project)
- [x] Sandbox execution cho Gradle/Lint
- [x] Rate limiting
- [x] SQL injection prevention (Prisma ORM)
- [x] CORS configuration
- [x] Input validation (Pydantic)
- [x] Content hash deduplication

## Performance Optimization

1. **Caching**: Redis cache cho Project State, Course list
2. **Connection Pooling**: PostgreSQL connection pool
3. **Background Tasks**: Celery cho heavy analysis
4. **Vector Index**: HNSW index cho pgvector semantic search
5. **File Deduplication**: xxHash64 content hash
6. **Debouncing**: Client-side + server-side debounce

## Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo service postgresql status

# Check connection string in .env
psql $DATABASE_URL
```

### Celery Worker Not Processing

```bash
# Check Redis connection
redis-cli ping

# Check Celery broker
celery -A app.tasks.celery inspect active
```

### Docker Sandbox Timeout

```bash
# Increase timeout in .env
SANDBOX_TIMEOUT_SECONDS=120

# Check Docker daemon
docker ps
```

### pgvector Not Found

```sql
-- Connect to database
\c gs_android_learning

-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify
\dx
```

## Contributing

Xem [../readme.md](../readme.md) để hiểu architecture tổng thể.

## License

Private project - Educational use only.
