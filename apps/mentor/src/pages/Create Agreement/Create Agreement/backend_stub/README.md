# Mentorship AI Assistant - Backend Stub

This is a minimal FastAPI backend implementation for the Mentorship AI Assistant.

## Features

- ✅ Chat endpoint with OpenAI integration
- ✅ Authentication stubs (mock implementation)
- ✅ Health check endpoint
- ✅ CORS configuration for local development
- ✅ Forum endpoints (stub)
- ✅ Knowledge base endpoints (stub)

## Quick Start

### 1. Install Dependencies

```bash
cd backend_stub
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Run Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### 4. View API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Test Health Endpoint

```bash
curl http://localhost:8000/api/health
```

### Test Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a mentorship assistant."},
      {"role": "user", "content": "Generate 3 discovery questions for a mentee."}
    ],
    "user_id": "test_mentor"
  }'
```

### Test Authentication

```bash
curl http://localhost:8000/api/auth/session
```

## Frontend Integration

### 1. Configure Frontend

In the main project directory, create/edit `.env`:

```
VITE_API_BASE_URL=http://localhost:8000/api
```

### 2. Start Frontend

```bash
npm run dev
```

The frontend will now connect to this backend.

## Production Deployment

For production, you should:

1. **Implement Real Authentication**
   - Add JWT token validation
   - Implement user database
   - Secure password hashing

2. **Add Database**
   - PostgreSQL for data persistence
   - Store chat history
   - Forum posts and knowledge base

3. **Add Rate Limiting**
   - Limit requests per user
   - Prevent abuse

4. **Implement Logging**
   - Log all AI interactions
   - Audit trail for compliance

5. **Add Content Filtering**
   - Filter inappropriate content
   - Compliance with policies

6. **Environment Variables**
   - Never commit API keys
   - Use secrets management

7. **Deploy with Gunicorn**
   ```bash
   gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

## API Endpoints

### Authentication
- `GET /api/auth/session` - Get current session
- `POST /api/auth/login` - Login
- `GET /api/auth/validate` - Validate session
- `POST /api/auth/logout` - Logout

### Chat
- `POST /api/chat` - Send chat message

### Forum
- `GET /api/forum/posts` - Get forum posts
- `POST /api/forum/posts` - Create forum post

### Knowledge Base
- `GET /api/knowledge/categories` - Get categories
- `GET /api/knowledge/popular` - Get popular articles

## Security Notes

⚠️ **This is a development stub. Do NOT use in production without:**

1. Proper authentication (JWT with secure secrets)
2. Database for data persistence
3. Rate limiting
4. Input validation and sanitization
5. HTTPS/TLS encryption
6. API key rotation
7. Monitoring and logging
8. Error handling improvements
9. CORS configuration for production domains
10. Compliance with data privacy regulations

## License

Proprietary - IntelliCV AI Platform
