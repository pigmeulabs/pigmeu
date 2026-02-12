# API Documentation

## Overview

Pigmeu Copilot API is a REST API built with FastAPI for managing book review submissions and generating automated articles.

**Base URL**: `http://localhost:8000` (development)

**API Format**: JSON

**Documentation**: 
- Interactive Swagger UI: `/docs`
- ReDoc: `/redoc`

---

## Authentication

Currently, the API has no authentication. This will be added in future phases.

---

## Response Format

All successful responses follow this format:

```json
{
  "data": { /* response data */ },
  "status": "success",
  "timestamp": "2024-02-10T10:30:00Z"
}
```

Error responses:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

---

## Endpoints

### Health Checks

#### Get API Health
```
GET /health
```

**Response (200 OK)**:
```json
{
  "status": "ok",
  "app": "Pigmeu Copilot API",
  "environment": "development"
}
```

---

### Submissions

#### Submit Book for Review
```
POST /submit
```

**Description**: Create a new book submission task for automated review generation.

**Request Body**:
```json
{
  "title": "Designing Data-Intensive Applications",
  "author_name": "Martin Kleppmann",
  "amazon_url": "https://www.amazon.com/Designing-Data-Intensive-Applications-1491901632/",
  "goodreads_url": "https://www.goodreads.com/book/show/23463279",
  "author_site": "https://www.linkedin.com/in/martinkleppmann/",
  "other_links": []
}
```

**Fields**:
- `title` (required, string): Book title (1-255 chars)
- `author_name` (required, string): Author full name (1-255 chars)
- `amazon_url` (required, URL): Amazon product page URL
- `goodreads_url` (optional, URL): Goodreads book page
- `author_site` (optional, URL): Author's personal website
- `other_links` (optional, array): Other relevant URLs (max 5)

**Response (201 Created)**:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Designing Data-Intensive Applications",
  "author_name": "Martin Kleppmann",
  "amazon_url": "https://www.amazon.com/Designing-Data-Intensive-Applications-1491901632/",
  "goodreads_url": "https://www.goodreads.com/book/show/23463279",
  "author_site": "https://www.linkedin.com/in/martinkleppmann/",
  "other_links": [],
  "status": "pending_scrape",
  "created_at": "2024-02-10T10:30:00.000Z",
  "updated_at": "2024-02-10T10:30:00.000Z"
}
```

**Status Values**:
- `pending_scrape`: Waiting to be scraped (initial state)
- `scraped`: Metadata extracted from Amazon/Goodreads
- `pending_context`: Ready for context generation
- `context_generated`: Knowledge base created
- `pending_article`: Ready for article generation
- `article_generated`: Article created
- `ready_for_review`: Waiting for user review
- `approved`: User approved for publishing
- `published`: Published to WordPress
- `failed`: Processing failed

**Error Responses**:

400 Bad Request (Duplicate):
```json
{
  "detail": "Book already submitted: 507f1f77bcf86cd799439010. Check status or contact support."
}
```

422 Unprocessable Entity (Validation):
```json
{
  "detail": [
    {
      "loc": ["body", "amazon_url"],
      "msg": "invalid URL",
      "type": "value_error.url"
    }
  ]
}
```

500 Internal Server Error:
```json
{
  "detail": "Failed to create submission. Please try again."
}
```

**Examples**:

Create submission with all fields:
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Designing Data-Intensive Applications",
    "author_name": "Martin Kleppmann",
    "amazon_url": "https://www.amazon.com/Designing-Data-Intensive-Applications-1491901632/",
    "goodreads_url": "https://www.goodreads.com/book/show/23463279",
    "author_site": "https://www.linkedin.com/in/martinkleppmann/"
  }'
```

Create submission with minimal fields:
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code",
    "author_name": "Robert Martin",
    "amazon_url": "https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/"
  }'
```

---

### Tasks

#### List All Submissions
```
GET /tasks
```

**Description**: Get paginated list of all book submissions.

**Query Parameters**:
- `skip` (optional, int): Skip first N items (default: 0)
- `limit` (optional, int): Max items to return (default: 20, max: 100)
- `status` (optional, string): Filter by status (e.g., "pending_scrape")

**Response (200 OK)**:
```json
{
  "tasks": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "Designing Data-Intensive Applications",
      "author_name": "Martin Kleppmann",
      "amazon_url": "https://www.amazon.com/...",
      "status": "pending_scrape",
      "created_at": "2024-02-10T10:30:00Z",
      "updated_at": "2024-02-10T10:30:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20,
  "count": 1
}
```

**Examples**:

List first 20 tasks:
```bash
curl http://localhost:8000/tasks
```

List second page (skip 20, limit 20):
```bash
curl http://localhost:8000/tasks?skip=20&limit=20
```

List only pending tasks:
```bash
curl http://localhost:8000/tasks?status=pending_scrape
```

---

#### Get Task Details
```
GET /tasks/{submission_id}
```

**Description**: Get detailed information about a specific submission including extraction status and extracted data.

**Path Parameters**:
- `submission_id` (required, string): Submission MongoDB ObjectId

**Response (200 OK)**:
```json
{
  "submission": {
    "id": "507f1f77bcf86cd799439011",
    "title": "Designing Data-Intensive Applications",
    "author_name": "Martin Kleppmann",
    "amazon_url": "https://www.amazon.com/...",
    "status": "pending_scrape",
    "created_at": "2024-02-10T10:30:00Z",
    "updated_at": "2024-02-10T10:30:00Z"
  },
  "book": {
    "id": "507f1f77bcf86cd799439012",
    "extracted": {
      "title_original": "Designing Data-Intensive Applications: Reliable, Scalable, and Maintainable Systems",
      "authors": ["Martin Kleppmann"],
      "theme": "Computer Science - Databases",
      "isbn": "1491901632",
      "pages": 626,
      "publisher": "O'Reilly Media",
      "pub_date": "2017-03-28"
    },
    "last_updated": "2024-02-10T10:35:00Z"
  },
  "progress": {
    "current_stage": "pending_scrape",
    "steps": [
      {
        "stage": "pending_scrape",
        "label": "Scraping metadata...",
        "completed": false
      },
      {
        "stage": "pending_context",
        "label": "Generating context...",
        "completed": false
      },
      {
        "stage": "pending_article",
        "label": "Creating article...",
        "completed": false
      },
      {
        "stage": "ready_for_review",
        "label": "Ready for review",
        "completed": false
      }
    ]
  }
}
```

**Error Responses**:

404 Not Found:
```json
{
  "detail": "Submission not found: 507f1f77bcf86cd799439011"
}
```

500 Internal Server Error:
```json
{
  "detail": "Failed to retrieve task. Please try again."
}
```

**Examples**:

Get task details:
```bash
curl http://localhost:8000/tasks/507f1f77bcf86cd799439011
```

---

## Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST request |
| 400 | Bad Request | Invalid input (e.g., duplicate book) |
| 404 | Not Found | Requested resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

Currently no rate limiting is implemented. Will be added in production deployment.

---

## Pagination

List endpoints support pagination:

```
GET /tasks?skip=0&limit=20
```

**Response includes**:
- `skip`: Number of items skipped
- `limit`: Max items requested
- `count`: Number of items returned
- `total`: Total items available

**Example - Implement pagination in client**:

```javascript
async function getAllTasks(pageSize = 20) {
  let allTasks = [];
  let skip = 0;
  
  while (true) {
    const response = await fetch(
      `http://localhost:8000/tasks?skip=${skip}&limit=${pageSize}`
    );
    const data = await response.json();
    
    allTasks = [...allTasks, ...data.tasks];
    
    if (data.count < pageSize) break;
    skip += pageSize;
  }
  
  return allTasks;
}
```

---

## Error Handling

### Validation Errors (422)

When input fails Pydantic validation:

```json
{
  "detail": [
    {
      "loc": ["body", "amazon_url"],
      "msg": "Invalid URL",
      "type": "value_error.url"
    }
  ]
}
```

### Business Logic Errors (400)

When request violates business rules:

```json
{
  "detail": "Book already submitted: 507f1f77bcf86cd799439010"
}
```

### Server Errors (500)

When server encounters unexpected error:

```json
{
  "detail": "Failed to create submission. Please try again."
}
```

---

## Future Enhancements (Roadmap)

### Phase 2: Scraping API
- GET `/submissions/{id}/metadata` — Get extracted book metadata
- POST `/submissions/{id}/rescrape` — Retry scraping

### Phase 3: Context Generation API
- GET `/submissions/{id}/context` — Get knowledge base
- GET `/submissions/{id}/summaries` — Get source summaries

### Phase 4: Article API
- GET `/submissions/{id}/article` — Get generated article
- PUT `/submissions/{id}/article` — Save draft edits
- POST `/submissions/{id}/article/publish` — Publish to WordPress

### Phase 5: Config API
- POST `/config/credentials` — Store API keys
- GET `/config/prompts` — List prompt templates
- POST `/config/prompts` — Create custom prompt

---

## Client Libraries

### Python
```python
import httpx

client = httpx.AsyncClient(base_url="http://localhost:8000")

# Submit book
response = await client.post("/submit", json={
    "title": "Test",
    "author_name": "Author",
    "amazon_url": "https://amazon.com/..."
})
submission = response.json()

# List tasks
tasks = await client.get("/tasks")

# Get task details
task = await client.get(f"/tasks/{submission['id']}")
```

### JavaScript/TypeScript
```javascript
// Fetch API
async function submitBook(book) {
  const response = await fetch('http://localhost:8000/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(book)
  });
  return response.json();
}

// Axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

const submission = await api.post('/submit', book);
```

### cURL
```bash
# Submit
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{"title":"...","author_name":"...","amazon_url":"..."}'

# List
curl http://localhost:8000/tasks

# Get details
curl http://localhost:8000/tasks/{id}
```

---

## Support

For issues or questions:
- Check [SETUP.md](SETUP.md) for setup help
- View [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Open issue on GitHub: https://github.com/pigmeulabs/pigmeu/issues
