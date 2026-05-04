# DocInsight API Reference

Complete API documentation for DocInsight backend.

**Base URL:** `http://localhost:8000`  
**API Version:** v1.0.0

---

## Table of Contents

1. [Authentication](#authentication)
2. [Documents API](#documents-api)
3. [Chat API](#chat-api)
4. [Sessions API](#sessions-api)
5. [Advanced API](#advanced-api)
6. [Error Handling](#error-handling)
7. [Response Formats](#response-formats)

---

## Authentication

Currently, DocInsight uses **API key-based authentication** (optional in local dev, required in production).

### Adding API Key Support

```env
# backend/.env
API_KEY_ENABLED=true
API_KEY=your-secret-api-key
```

Include in requests:
```bash
curl -H "X-API-Key: your-secret-api-key" ...
```

---

## Documents API

### Upload Document

**Endpoint:** `POST /api/documents/upload`

Upload PDF, DOCX, or TXT documents for indexing.

**Parameters:**
- `file` (form-data, required) — Document file (PDF, DOCX, TXT)

**Example:**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@document.pdf"
```

**Response (200 OK):**
```json
{
  "document_id": "doc_uuid_123",
  "filename": "document.pdf",
  "size_bytes": 245123,
  "pages": 15,
  "chunks": 47,
  "indexed_at": "2024-05-01T10:30:00Z",
  "summary": "This document discusses...",
  "status": "indexed"
}
```

**Error Responses:**
- `400 Bad Request` — Invalid file format or missing file
- `413 Payload Too Large` — File exceeds size limit
- `422 Unprocessable Entity` — File could not be parsed

---

### List Documents

**Endpoint:** `GET /api/documents`

Retrieve all uploaded documents with metadata.

**Query Parameters:**
- `skip` (integer, optional) — Pagination offset (default: 0)
- `limit` (integer, optional) — Items per page (default: 50)
- `search` (string, optional) — Filter by filename

**Example:**
```bash
curl http://localhost:8000/api/documents?skip=0&limit=10
```

**Response (200 OK):**
```json
{
  "documents": [
    {
      "document_id": "doc_uuid_123",
      "filename": "document.pdf",
      "size_bytes": 245123,
      "pages": 15,
      "chunks": 47,
      "indexed_at": "2024-05-01T10:30:00Z",
      "summary": "...",
      "embedding_model": "all-MiniLM-L6-v2"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

---

### Get Document Details

**Endpoint:** `GET /api/documents/{document_id}`

Retrieve detailed information for a specific document.

**Path Parameters:**
- `document_id` (string, required) — Document UUID

**Example:**
```bash
curl http://localhost:8000/api/documents/doc_uuid_123
```

**Response (200 OK):**
```json
{
  "document_id": "doc_uuid_123",
  "filename": "document.pdf",
  "size_bytes": 245123,
  "pages": 15,
  "chunks": 47,
  "indexed_at": "2024-05-01T10:30:00Z",
  "summary": "...",
  "content_preview": "First 500 chars...",
  "chunk_details": [
    {
      "chunk_id": "chunk_1",
      "page": 1,
      "text": "...",
      "metadata": {}
    }
  ]
}
```

---

### Delete Document

**Endpoint:** `DELETE /api/documents/{document_id}`

Remove document from index and storage.

**Path Parameters:**
- `document_id` (string, required) — Document UUID

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/documents/doc_uuid_123
```

**Response (204 No Content)**

---

### Get Document Summary

**Endpoint:** `GET /api/documents/{document_id}/summary`

Retrieve AI-generated summary for a document.

**Path Parameters:**
- `document_id` (string, required) — Document UUID

**Example:**
```bash
curl http://localhost:8000/api/documents/doc_uuid_123/summary
```

**Response (200 OK):**
```json
{
  "document_id": "doc_uuid_123",
  "filename": "document.pdf",
  "summary": "Comprehensive summary...",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "word_count": 150,
  "generated_at": "2024-05-01T10:30:00Z"
}
```

---

## Chat API

### Stream Chat Response

**Endpoint:** `POST /api/chat/stream`

Submit a query and receive streaming responses with sources.

**Request Body:**
```json
{
  "message": "What are the main topics discussed?",
  "session_id": "session_uuid_optional",
  "document_ids": [],
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_k_retrieval": 4
}
```

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `message` | string | Yes | — | User query |
| `session_id` | string | No | New UUID | Chat session ID |
| `document_ids` | array | No | `[]` | Specific docs to query (empty = all) |
| `temperature` | float | No | 0.7 | LLM creativity (0.0-2.0) |
| `max_tokens` | integer | No | 1000 | Max response length |
| `top_k_retrieval` | integer | No | 4 | Number of chunks to retrieve |

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize the document",
    "session_id": "session_123",
    "document_ids": [],
    "temperature": 0.7
  }'
```

**Response (200 OK - Server-Sent Events):**
```
data: {"type": "chunk", "content": "The", "token_count": 1}
data: {"type": "chunk", "content": " main", "token_count": 2}
data: {"type": "chunk", "content": " topics", "token_count": 3}
...
data: {"type": "sources", "sources": [{"filename": "doc.pdf", "page": 5, "text": "..."}]}
data: {"type": "completion", "total_tokens": 150, "confidence": 0.92}
```

---

### Get Chat History

**Endpoint:** `GET /api/chat/history/{session_id}`

Retrieve all messages in a session.

**Path Parameters:**
- `session_id` (string, required) — Session UUID

**Example:**
```bash
curl http://localhost:8000/api/chat/history/session_uuid_123
```

**Response (200 OK):**
```json
{
  "session_id": "session_uuid_123",
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "content": "What is this about?",
      "timestamp": "2024-05-01T10:00:00Z"
    },
    {
      "id": "msg_2",
      "role": "assistant",
      "content": "This document discusses...",
      "sources": [
        {
          "document_id": "doc_123",
          "filename": "document.pdf",
          "page": 1,
          "snippet": "..."
        }
      ],
      "confidence": 0.92,
      "timestamp": "2024-05-01T10:01:00Z"
    }
  ],
  "total_messages": 2
}
```

---

## Sessions API

### Create Session

**Endpoint:** `POST /api/sessions`

Create a new chat session.

**Request Body:**
```json
{
  "name": "Q&A Session",
  "description": "Discussing report findings"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "My Session", "description": "Notes"}'
```

**Response (201 Created):**
```json
{
  "session_id": "session_uuid_123",
  "name": "Q&A Session",
  "description": "Discussing report findings",
  "created_at": "2024-05-01T10:00:00Z",
  "updated_at": "2024-05-01T10:00:00Z",
  "message_count": 0
}
```

---

### List Sessions

**Endpoint:** `GET /api/sessions`

Retrieve all chat sessions.

**Query Parameters:**
- `skip` (integer, optional) — Pagination offset
- `limit` (integer, optional) — Items per page

**Example:**
```bash
curl http://localhost:8000/api/sessions?skip=0&limit=10
```

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "session_id": "session_uuid_123",
      "name": "Q&A Session",
      "description": "...",
      "created_at": "2024-05-01T10:00:00Z",
      "updated_at": "2024-05-01T10:30:00Z",
      "message_count": 5
    }
  ],
  "total": 1
}
```

---

### Get Session Details

**Endpoint:** `GET /api/sessions/{session_id}`

Retrieve a specific session with full history.

**Example:**
```bash
curl http://localhost:8000/api/sessions/session_uuid_123
```

**Response (200 OK):**
```json
{
  "session_id": "session_uuid_123",
  "name": "Q&A Session",
  "messages": [...],
  "created_at": "2024-05-01T10:00:00Z",
  "updated_at": "2024-05-01T10:30:00Z"
}
```

---

### Rename Session

**Endpoint:** `PUT /api/sessions/{session_id}`

Update session name or description.

**Request Body:**
```json
{
  "name": "New Session Name",
  "description": "Updated description"
}
```

**Example:**
```bash
curl -X PUT http://localhost:8000/api/sessions/session_uuid_123 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```

**Response (200 OK):**
```json
{
  "session_id": "session_uuid_123",
  "name": "New Session Name",
  "description": "Updated description",
  "updated_at": "2024-05-01T10:35:00Z"
}
```

---

### Delete Session

**Endpoint:** `DELETE /api/sessions/{session_id}`

Delete a chat session and all associated messages.

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/sessions/session_uuid_123
```

**Response (204 No Content)**

---

## Advanced API

### Export Session to PDF

**Endpoint:** `POST /api/advanced/export-pdf`

Generate a PDF report of a chat session.

**Request Body:**
```json
{
  "session_id": "session_uuid_123",
  "include_sources": true,
  "include_metadata": true
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/advanced/export-pdf \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_uuid_123"}' \
  --output session_report.pdf
```

**Response (200 OK):**
- Returns binary PDF file
- Filename format: `session_{session_id}_{timestamp}.pdf`

---

### Batch Process Documents

**Endpoint:** `POST /api/advanced/batch-process`

Process multiple documents in batch mode.

**Request Body:**
```json
{
  "documents": ["doc_id_1", "doc_id_2"],
  "action": "summarize",
  "options": {}
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/advanced/batch-process \
  -H "Content-Type: application/json" \
  -d '{"documents": ["doc_1", "doc_2"], "action": "summarize"}'
```

**Response (200 OK):**
```json
{
  "batch_id": "batch_uuid_123",
  "status": "processing",
  "processed": 0,
  "total": 2,
  "results": []
}
```

---

### Health Check

**Endpoint:** `GET /api/health`

Check backend service health.

**Example:**
```bash
curl http://localhost:8000/api/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "models_loaded": true,
  "vector_db_connected": true,
  "llm_provider": "groq"
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "status_code": 400,
  "timestamp": "2024-05-01T10:30:00Z",
  "request_id": "req_uuid_123"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `DOCUMENT_NOT_FOUND` | 404 | Document doesn't exist |
| `SESSION_NOT_FOUND` | 404 | Session doesn't exist |
| `INVALID_FILE_FORMAT` | 400 | Unsupported file type |
| `FILE_TOO_LARGE` | 413 | File exceeds size limit |
| `PARSING_ERROR` | 422 | Could not parse document |
| `LLM_ERROR` | 503 | LLM service unavailable |
| `VECTOR_DB_ERROR` | 503 | Database connection failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `UNAUTHORIZED` | 401 | Invalid or missing API key |

---

## Response Formats

### Pagination

```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 10,
  "has_more": true
}
```

### Timestamps

All timestamps use ISO 8601 format with UTC timezone:
```
2024-05-01T10:30:00Z
```

### UUID Format

All IDs are UUID v4:
```
550e8400-e29b-41d4-a716-446655440000
```

---

## Rate Limiting

Production deployments should implement rate limiting:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704106200
```

---

## WebSocket Support (Future)

Real-time chat streaming via WebSocket:
```
ws://localhost:8000/api/chat/ws/{session_id}
```

---

## SDK Examples

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/documents/upload",
    files={"file": open("document.pdf", "rb")}
)
print(response.json())
```

### JavaScript/Node.js
```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

fetch("http://localhost:8000/api/documents/upload", {
  method: "POST",
  body: formData
})
.then(r => r.json())
.then(data => console.log(data));
```

### cURL
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Your question here",
    "session_id": "session-uuid"
  }'
```

---

## Versioning

API versioning via URL path: `/api/v1/`, `/api/v2/`, etc.

Current version: `v1` (implicit in all endpoints)

---

## Support

For API issues or questions:
- Check [Troubleshooting](./TROUBLESHOOTING.md)
- Review logs: `backend/logs/`
- Open an issue on GitHub
