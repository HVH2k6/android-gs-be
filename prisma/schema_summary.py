"""
Database Schema Design Summary

This schema implements the AI Android Learning Monitoring System with focus on:
1. Security (device pairing, sandbox execution, file size limits)
2. Reliability (issue fingerprinting via AST, outbox pattern for realtime events)
3. Scalability (background task queue, connection pooling, caching)
4. AI/ML Integration (RAG with pgvector, LLM tracking, ML predictions)

Key Design Patterns:
- Issue Fingerprinting: AST-based identity instead of line numbers
- Device Pairing: QR code token authentication
- Sandbox Execution: Docker isolation for student code
- Outbox Pattern: Reliable WebSocket event delivery
- Task Queue: Celery for heavy analysis pipeline
- Vector Search: pgvector for RAG knowledge retrieval

Total Tables: 27
- Core: 10 (User, Device, Course, Lesson, Assignment, etc)
- Analysis: 8 (AnalysisRun, CodeIssue, CodeFeedback, etc)
- AI/ML: 5 (AIInteraction, KnowledgeDocument, BackgroundTask, etc)
- Infrastructure: 4 (RealtimeEvent, SandboxExecution, AuditLog, etc)

See prisma/README.md for detailed documentation.
"""
