# Backend API Documentation

This document describes the backend API endpoints required for the Mentorship AI Assistant.

## Base URL

```
http://localhost:8000/api
```

Configure this in `.env` file as `VITE_API_BASE_URL`.

---

## Authentication

All requests should include authentication headers:

```
Authorization: Bearer <token>
X-User-ID: <user_id>
```

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the backend is available.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 2. Authentication

#### Get Session
**GET** `/auth/session`

Get current user session.

**Response:**
```json
{
  "user": {
    "id": "mentor_123",
    "role": "mentor",
    "email": "mentor@example.com",
    "name": "John Doe",
    "mentor_id": "mentor_123"
  },
  "token": "jwt_token_here"
}
```

#### Login
**POST** `/auth/login`

**Request:**
```json
{
  "email": "mentor@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "user": {
    "id": "mentor_123",
    "role": "mentor",
    "email": "mentor@example.com",
    "name": "John Doe",
    "mentor_id": "mentor_123"
  },
  "token": "jwt_token_here"
}
```

#### Validate Session
**GET** `/auth/validate`

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "valid": true
}
```

#### Logout
**POST** `/auth/logout`

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true
}
```

---

### 3. Chat Service

**POST** `/chat`

Send a chat message to the AI assistant.

**Request:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a mentorship assistant."
    },
    {
      "role": "user",
      "content": "Generate discovery questions for career transition."
    }
  ],
  "user_id": "mentor_123",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response (Flexible Format):**

The frontend accepts any of these response formats:

```json
{
  "reply": "AI response here..."
}
```

OR

```json
{
  "message": "AI response here..."
}
```

OR

```json
{
  "content": "AI response here..."
}
```

OR

```json
{
  "data": {
    "reply": "AI response here..."
  }
}
```

**Backend Implementation Notes:**
- Integrate with OpenAI, Anthropic, or your preferred AI provider
- Apply rate limiting per user
- Log conversations for audit
- Implement content filtering
- Never fabricate information (as per policy)

---

### 4. Forum

#### Get Posts
**GET** `/forum/posts?page=1&limit=20&tag=mentorship`

**Response:**
```json
{
  "posts": [
    {
      "id": "post_123",
      "title": "Best practices for first mentorship session",
      "content": "I'm wondering what are the...",
      "author": {
        "id": "mentor_456",
        "name": "Jane Smith",
        "role": "mentor"
      },
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z",
      "replies_count": 5,
      "likes_count": 12,
      "tags": ["mentorship", "best-practices"]
    }
  ],
  "total": 42
}
```

#### Get Single Post
**GET** `/forum/posts/:postId`

**Response:**
```json
{
  "post": {
    "id": "post_123",
    "title": "Best practices for first mentorship session",
    "content": "I'm wondering what are the...",
    "author": {
      "id": "mentor_456",
      "name": "Jane Smith",
      "role": "mentor"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "replies_count": 5,
    "likes_count": 12,
    "tags": ["mentorship", "best-practices"]
  },
  "replies": [
    {
      "id": "reply_789",
      "post_id": "post_123",
      "content": "Great question! I recommend...",
      "author": {
        "id": "mentor_101",
        "name": "Bob Johnson",
        "role": "mentor"
      },
      "created_at": "2024-01-01T11:00:00Z",
      "likes_count": 3
    }
  ]
}
```

#### Create Post
**POST** `/forum/posts`

**Request:**
```json
{
  "title": "How to handle difficult conversations?",
  "content": "I need advice on...",
  "tags": ["communication", "challenges"]
}
```

**Response:**
```json
{
  "id": "post_124",
  "title": "How to handle difficult conversations?",
  "content": "I need advice on...",
  "author": {
    "id": "mentor_123",
    "name": "John Doe",
    "role": "mentor"
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "replies_count": 0,
  "likes_count": 0,
  "tags": ["communication", "challenges"]
}
```

#### Create Reply
**POST** `/forum/posts/:postId/replies`

**Request:**
```json
{
  "content": "Here's my perspective..."
}
```

#### Like Post
**POST** `/forum/posts/:postId/like`

#### Search Posts
**GET** `/forum/search?q=career+transition`

---

### 5. Knowledge Base

#### Get Categories
**GET** `/knowledge/categories`

**Response:**
```json
[
  {
    "id": "cat_001",
    "name": "Getting Started",
    "description": "Introduction to mentorship",
    "article_count": 15
  },
  {
    "id": "cat_002",
    "name": "Advanced Techniques",
    "description": "Expert mentorship strategies",
    "article_count": 23
  }
]
```

#### Get Articles by Category
**GET** `/knowledge/categories/:categoryId/articles`

**Response:**
```json
[
  {
    "id": "article_001",
    "title": "Setting up your first session",
    "content": "## Introduction\n\nWhen starting...",
    "category": "Getting Started",
    "tags": ["beginner", "setup"],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "author": {
      "id": "admin_001",
      "name": "Admin"
    },
    "views": 1250,
    "helpful_count": 89
  }
]
```

#### Get Article
**GET** `/knowledge/articles/:articleId`

#### Search Articles
**GET** `/knowledge/search?q=goal+setting`

#### Get Popular Articles
**GET** `/knowledge/popular?limit=10`

#### Get Recent Articles
**GET** `/knowledge/recent?limit=10`

#### Mark Article as Helpful
**POST** `/knowledge/articles/:articleId/helpful`

#### Get Related Articles
**GET** `/knowledge/articles/:articleId/related`

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE",
    "status": 400
  }
}
```

**Common Status Codes:**
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

---

## Backend Implementation Example (Python/FastAPI)

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import openai
from typing import List, Optional

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: str
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=request.model,
            messages=[m.dict() for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            "reply": response.choices[0].message.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Security Considerations

1. **API Keys**: Never expose AI API keys to the frontend
2. **Rate Limiting**: Implement per-user rate limits
3. **Authentication**: Validate JWT tokens on every request
4. **Input Validation**: Sanitize all user inputs
5. **Content Filtering**: Filter inappropriate content
6. **Audit Logging**: Log all AI interactions
7. **CORS**: Configure CORS properly for production
8. **Data Privacy**: Follow GDPR/privacy regulations
9. **No PII**: As per policy, do not collect or store PII

---

## Development Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure your backend URL:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

3. For testing without backend, set OpenAI key:
   ```
   VITE_OPENAI_API_KEY=sk-...
   ```

4. Start your backend server on port 8000

5. Start the frontend:
   ```bash
   npm run dev
   ```

---

## Testing

Use these curl commands to test your backend:

```bash
# Health check
curl http://localhost:8000/api/health

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "Hello"}
    ],
    "user_id": "test_user"
  }'
```
