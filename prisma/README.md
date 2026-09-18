# AI Android Learning Monitoring System - Database Setup

## Prerequisites

```bash
# Install PostgreSQL with pgvector extension
# Ubuntu/Debian:
sudo apt-get install postgresql-15 postgresql-15-pgvector

# macOS:
brew install postgresql@15
brew install pgvector

# Windows: Download from https://www.postgresql.org/download/windows/
```

## Database Initialization

### 1. Create Database

```sql
CREATE DATABASE gs_android_learning;
\c gs_android_learning;

-- Enable pgvector extension for RAG
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Environment Variables

Create `.env` file in `back-end/` directory:

```bash
DATABASE_URL="postgresql://username:password@localhost:5432/gs_android_learning"

# For production with connection pooling:
# DATABASE_URL="postgresql://username:password@localhost:5432/gs_android_learning?schema=public&connection_limit=10&pool_timeout=30"
```

### 3. Install Prisma Client for Python

```bash
cd back-end
pip install prisma prisma-client-py
```

### 4. Generate Prisma Client

```bash
# Generate Python client
prisma generate

# Push schema to database (dev)
prisma db push

# Or use migrations (production)
prisma migrate dev --name init
```

## Schema Overview

### Core Architecture

```
User (Authentication)
  ├── Student
  └── Device (Desktop Agent / Mobile App)
       ├── Device Pairing (QR Code Security)
       └── LearningSession
            ├── Project (File State Management)
            │    └── ProjectFile (Version + Content Hash)
            ├── AnalysisRun (Pipeline Stages)
            │    ├── CodeIssue (AST Fingerprinting)
            │    └── CodeFeedback (AI Explanations)
            ├── RequirementEvaluation
            ├── AIInteraction (LLM Usage Tracking)
            └── RealtimeEvent (WebSocket Outbox)
```

### Key Design Decisions

#### 1. Issue Fingerprinting (flow.md requirement)

Instead of tracking by line numbers (which shift on edit):

```prisma
model CodeIssue {
  issueFingerprint String  // Hash: rule_id + method_scope + node_type
  astNodePath      String  // AST path for stable tracking
  
  // Line numbers for display only:
  lineStart        Int
  lineEnd          Int?
}
```

#### 2. Device Pairing Security (flow.md concern)

```prisma
model Device {
  deviceFingerprint String   @unique  // Hardware UUID
  pairingToken      String?  @unique  // QR code token
  isPaired          Boolean
}
```

Prevents student A from accidentally syncing to student B's session.

#### 3. File Upload Protection (flow.md security)

```prisma
model ProjectFile {
  sizeBytes   Int          // Reject files > 10MB
  contentHash String       // xxHash64 deduplication
}

model FileUploadLog {
  sizeBytes    Int
  isRejected   Boolean
  rejectReason String?
}
```

#### 4. Sandbox Execution Tracking (flow.md RCE prevention)

```prisma
model SandboxExecution {
  containerID   String?       // Docker isolation
  cpuLimit      String        // "1.0"
  memoryLimit   String        // "512m"
  timeoutSeconds Int          @default(60)
}
```

Never execute student code directly on host.

#### 5. Realtime Event Outbox Pattern

```prisma
model RealtimeEvent {
  status       EventStatus  // PENDING → SENT → ACKNOWLEDGED
  retryCount   Int
  targetDeviceType DeviceType?  // Route to Desktop or Mobile
}
```

Ensures reliable WebSocket delivery.

#### 6. Background Task Queue Integration

```prisma
model BackgroundTask {
  taskType   String        // "gradle_build", "llm_analysis"
  priority   TaskPriority
  workerId   String?       // Celery/ARQ worker
  timeoutAt  DateTime?
}
```

Decouples heavy analysis from HTTP request cycle.

## Vector Search Setup (pgvector)

### Create Embedding Index

```sql
-- After migration, create HNSW index for fast semantic search
CREATE INDEX ON knowledge_documents USING hnsw (embedding vector_cosine_ops);

-- Or IVFFlat for larger datasets:
CREATE INDEX ON knowledge_documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Example RAG Query

```python
from prisma import Prisma

async def search_knowledge(query_embedding: list[float], limit: int = 5):
    prisma = Prisma()
    await prisma.connect()
    
    # Raw SQL for vector similarity search
    results = await prisma.query_raw(
        """
        SELECT id, title, content, 
               1 - (embedding <=> $1::vector) as similarity
        FROM knowledge_documents
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector
        LIMIT $2
        """,
        query_embedding,
        limit
    )
    
    return results
```

## Usage Example

### 1. Initialize Session

```python
from prisma import Prisma
from prisma.enums import SessionStatus

async def start_learning_session(student_id: str, assignment_id: str):
    prisma = Prisma()
    await prisma.connect()
    
    session = await prisma.learningsession.create(
        data={
            'studentId': student_id,
            'assignmentId': assignment_id,
            'status': SessionStatus.ACTIVE,
        }
    )
    
    return session
```

### 2. Track Code Issue with Fingerprinting

```python
import hashlib

def generate_issue_fingerprint(rule_id: str, method_scope: str, node_type: str, context: str) -> str:
    """Generate stable fingerprint independent of line numbers"""
    content = f"{rule_id}:{method_scope}:{node_type}:{context}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

async def track_issue(session_id: str, analysis_run_id: str, file_path: str, line: int):
    fingerprint = generate_issue_fingerprint(
        rule_id="empty_password_validation",
        method_scope="LoginViewModel.loginUser",
        node_type="IfStatement",
        context="password.isEmpty() == true"
    )
    
    issue = await prisma.codeissue.upsert(
        where={
            'sessionId_issueFingerprint': {
                'sessionId': session_id,
                'issueFingerprint': fingerprint
            }
        },
        data={
            'create': {
                'sessionId': session_id,
                'analysisRunId': analysis_run_id,
                'filePath': file_path,
                'lineStart': line,
                'issueFingerprint': fingerprint,
                'category': 'LOGIC_ERROR',
                'severity': 'HIGH',
                'status': 'OPEN',
                'title': 'Incorrect password validation',
                'message': 'loginUser() executed when password is empty',
            },
            'update': {
                'attemptCount': {'increment': 1},
                'lineStart': line,  # Update display location
            }
        }
    )
    
    return issue
```

### 3. Resolve Issue

```python
async def resolve_issue(session_id: str, issue_fingerprint: str):
    issue = await prisma.codeissue.update(
        where={
            'sessionId_issueFingerprint': {
                'sessionId': session_id,
                'issueFingerprint': issue_fingerprint
            }
        },
        data={
            'status': 'RESOLVED',
            'resolvedAt': datetime.utcnow(),
        }
    )
    
    # Calculate resolution time
    if issue.detectedAt and issue.resolvedAt:
        resolution_seconds = (issue.resolvedAt - issue.detectedAt).total_seconds()
        await prisma.codeissue.update(
            where={'id': issue.id},
            data={'resolutionTime': int(resolution_seconds)}
        )
    
    return issue
```

## Migration Strategy

### Phase 1: Core Tables
- User, Student, Device
- Course, Lesson, Assignment
- LearningSession, Project

### Phase 2: Analysis Pipeline
- AnalysisRun, CodeIssue, CodeFeedback
- RequirementEvaluation, StudentProgress

### Phase 3: AI/ML Layer
- AIInteraction, KnowledgeDocument (with pgvector)
- BackgroundTask, SandboxExecution

### Phase 4: Production Features
- RealtimeEvent (outbox pattern)
- AuditLog, RateLimit
- SystemConfig

## Performance Indexes

Critical indexes already defined in schema:

```prisma
@@index([sessionId, status])        // Fast session queries
@@index([issueFingerprint])         // Issue deduplication
@@index([contentHash])              // File deduplication
@@index([status, createdAt])        // Task queue processing
@@index([sessionId, status, createdAt])  // Event outbox
```

## Backup Strategy

```bash
# Daily backup
pg_dump gs_android_learning > backup_$(date +%Y%m%d).sql

# Restore
psql gs_android_learning < backup_20260916.sql
```

## Notes

- **Prisma Client Python** is async-first; use with FastAPI's async endpoints
- **pgvector** dimensions match embedding model (1536 for OpenAI text-embedding-3-small)
- **Issue fingerprinting** prevents duplicate issues when line numbers shift
- **Outbox pattern** ensures no WebSocket events are lost during network disruptions
- **Sandbox execution** logs every gradle/lint run for security audit
