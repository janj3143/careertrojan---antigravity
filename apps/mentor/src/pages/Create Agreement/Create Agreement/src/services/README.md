# Services Layer Documentation

This directory contains all backend service integrations for the Mentorship AI Assistant.

## Overview

The service layer provides a clean abstraction between the UI and backend APIs. All services are implemented as singleton classes for consistent state management.

## Services

### 1. API Service (`api.ts`)

Base HTTP client for all API requests.

**Features:**
- Request timeout handling
- Error standardization
- GET, POST, PUT, DELETE methods
- Automatic JSON parsing

**Usage:**
```typescript
import { apiService } from './services';

const data = await apiService.get('/endpoint');
const result = await apiService.post('/endpoint', { payload });
```

**Error Handling:**
```typescript
try {
  const data = await apiService.get('/endpoint');
} catch (error) {
  if (error instanceof APIError) {
    console.error(error.message, error.status);
  }
}
```

---

### 2. Chat Service (`chatService.ts`)

AI chat integration with automatic fallback.

**Architecture:**
```
chatService.sendChat()
    │
    ├─► Try Backend Proxy (preferred)
    │       ├─► Success → Return response
    │       └─► Fail → Mark backend unavailable
    │
    └─► Fallback to Direct API (if configured)
            ├─► OpenAI API
            └─► Return response
```

**Usage:**
```typescript
import { chatService } from './services';

const response = await chatService.sendChat({
  messages: [
    { role: 'system', content: 'You are a helpful assistant' },
    { role: 'user', content: 'Hello!' }
  ]
}, 'user_id');

console.log(response); // "Hello! How can I help you?"
```

**Response Flexibility:**

The service accepts multiple response formats from the backend:

```typescript
// All of these work:
{ "reply": "..." }           // ✓
{ "message": "..." }         // ✓
{ "content": "..." }         // ✓
{ "text": "..." }           // ✓
{ "answer": "..." }         // ✓
{ "data": { "reply": "..." } } // ✓
```

**Configuration:**

Set in `config.ts`:
```typescript
export const AI_CONFIG = {
  OPENAI_API_KEY: import.meta.env.VITE_OPENAI_API_KEY || '',
  MODEL: 'gpt-4',
  MAX_TOKENS: 2000,
  TEMPERATURE: 0.7,
};
```

**Methods:**

- `sendChat(payload, userId)` - Send chat request
- `testConnection()` - Test backend availability
- `isBackendAvailable()` - Check backend status

---

### 3. Auth Service (`authService.ts`)

Authentication and session management.

**Session Flow:**
```
1. initializeSession()
    ├─► Check localStorage
    ├─► Validate with backend
    └─► Return session or fallback to mock

2. requireMentorAuth()
    ├─► Check if authenticated
    ├─► Check if role = 'mentor'
    └─► Check if mentor_id exists
```

**Usage:**
```typescript
import { authService } from './services';

// Initialize session
await authService.initializeSession();

// Check authentication
authService.requireMentorAuth(); // Throws if not authorized

// Get current user
const session = authService.getSession();
console.log(session.user); // { id, role, email, name, mentor_id }

// Check role
if (authService.isMentor()) {
  const mentorId = authService.getMentorId();
}

// Login
const user = await authService.login('email@example.com', 'password');

// Logout
await authService.logout();
```

**Mock Session (Development):**

For development, a mock session is automatically provided:
```typescript
{
  user: {
    id: 'mentor_dev_001',
    role: 'mentor',
    email: 'mentor@intellicv.ai',
    name: 'Development Mentor',
    mentor_id: 'mentor_dev_001'
  },
  isAuthenticated: true,
  token: 'dev_token_12345'
}
```

---

### 4. Forum Service (`forumService.ts`)

Community forum operations.

**Usage:**
```typescript
import { forumService } from './services';

// Get posts
const { posts, total } = await forumService.getPosts({
  page: 1,
  limit: 20,
  tag: 'mentorship'
});

// Get single post with replies
const { post, replies } = await forumService.getPost('post_id');

// Create post
const newPost = await forumService.createPost({
  title: 'My question',
  content: 'Content here',
  tags: ['mentorship', 'career']
});

// Create reply
const reply = await forumService.createReply('post_id', 'My reply');

// Like post
await forumService.likePost('post_id');

// Search
const results = await forumService.searchPosts('career transition');
```

**Data Types:**

```typescript
interface ForumPost {
  id: string;
  title: string;
  content: string;
  author: {
    id: string;
    name: string;
    role: string;
  };
  created_at: string;
  updated_at: string;
  replies_count: number;
  likes_count: number;
  tags: string[];
}
```

---

### 5. Knowledge Base Service (`knowledgeBaseService.ts`)

Knowledge base and resource access.

**Usage:**
```typescript
import { knowledgeBaseService } from './services';

// Get categories
const categories = await knowledgeBaseService.getCategories();

// Get articles by category
const articles = await knowledgeBaseService.getArticlesByCategory('cat_id');

// Get single article
const article = await knowledgeBaseService.getArticle('article_id');

// Search articles
const results = await knowledgeBaseService.searchArticles('goal setting');

// Get popular articles
const popular = await knowledgeBaseService.getPopularArticles(10);

// Get recent articles
const recent = await knowledgeBaseService.getRecentArticles(10);

// Mark as helpful
await knowledgeBaseService.markHelpful('article_id');

// Get related articles
const related = await knowledgeBaseService.getRelatedArticles('article_id');
```

**Data Types:**

```typescript
interface KnowledgeArticle {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  author?: {
    id: string;
    name: string;
  };
  views: number;
  helpful_count: number;
}
```

---

### 6. Configuration (`config.ts`)

Central configuration for all services.

**API Configuration:**
```typescript
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  CHAT_ENDPOINT: '/chat',
  FORUM_ENDPOINT: '/forum',
  KNOWLEDGE_BASE_ENDPOINT: '/knowledge',
  AUTH_ENDPOINT: '/auth',
  TIMEOUT: 30000,
};
```

**AI Configuration:**
```typescript
export const AI_CONFIG = {
  OPENAI_API_KEY: import.meta.env.VITE_OPENAI_API_KEY || '',
  ANTHROPIC_API_KEY: import.meta.env.VITE_ANTHROPIC_API_KEY || '',
  MODEL: import.meta.env.VITE_AI_MODEL || 'gpt-4',
  MAX_TOKENS: 2000,
  TEMPERATURE: 0.7,
};
```

---

## Error Handling

All services throw `APIError` for failed requests:

```typescript
import { APIError } from './services';

try {
  const data = await chatService.sendChat(payload, userId);
} catch (error) {
  if (error instanceof APIError) {
    // API error
    console.error('Status:', error.status);
    console.error('Message:', error.message);
    console.error('Data:', error.data);
  } else if (error instanceof Error) {
    // Other errors
    console.error('Error:', error.message);
  }
}
```

---

## Adding a New Service

1. **Create service file** (`src/services/newService.ts`):

```typescript
import { apiService } from './api';
import { API_CONFIG } from './config';

class NewService {
  async getData(): Promise<any> {
    return await apiService.get('/new-endpoint');
  }
}

export const newService = new NewService();
```

2. **Export from index.ts**:

```typescript
export { newService } from './newService';
```

3. **Use in components**:

```typescript
import { newService } from '../services';

const data = await newService.getData();
```

---

## Testing Services

### Unit Testing

```typescript
import { chatService } from './chatService';

describe('ChatService', () => {
  it('should send chat request', async () => {
    const response = await chatService.sendChat({
      messages: [
        { role: 'user', content: 'Hello' }
      ]
    }, 'test_user');
    
    expect(response).toBeDefined();
    expect(typeof response).toBe('string');
  });
});
```

### Integration Testing

```bash
# Start backend
cd backend_stub
python main.py

# Run integration tests
npm run test:integration
```

---

## Best Practices

1. **Always use services, never fetch directly:**
   ```typescript
   // ✗ Bad
   const response = await fetch('/api/endpoint');
   
   // ✓ Good
   const data = await apiService.get('/endpoint');
   ```

2. **Handle errors properly:**
   ```typescript
   try {
     const data = await service.method();
   } catch (error) {
     // Handle error
     console.error(error);
   }
   ```

3. **Use TypeScript types:**
   ```typescript
   import type { ChatMessage } from '../services';
   
   const messages: ChatMessage[] = [...];
   ```

4. **Don't expose API keys:**
   ```typescript
   // ✗ Bad - Hardcoded key
   const apiKey = 'sk-1234567890';
   
   // ✓ Good - Environment variable
   const apiKey = import.meta.env.VITE_API_KEY;
   ```

5. **Use singleton instances:**
   ```typescript
   // Services are already singletons
   import { chatService } from './services';
   // Don't create new instances
   ```

---

## Troubleshooting

### Service not connecting to backend

1. Check backend is running
2. Verify `VITE_API_BASE_URL` in `.env`
3. Check CORS configuration
4. Test with curl: `curl http://localhost:8000/api/health`

### TypeScript errors

1. Check type imports: `import type { Type } from './services'`
2. Regenerate types if API changed
3. Check `tsconfig.json` includes service directory

### Authentication errors

1. Check session initialization
2. Verify token is valid
3. Check backend `/auth/validate` endpoint

---

## Environment Variables

Required in `.env`:

```env
# Required
VITE_API_BASE_URL=http://localhost:8000/api

# Optional (for fallback)
VITE_OPENAI_API_KEY=sk-...
VITE_AI_MODEL=gpt-4

# Optional (Anthropic)
VITE_ANTHROPIC_API_KEY=sk-ant-...
```

---

## Production Considerations

1. **Never commit `.env`** - Add to `.gitignore`
2. **Use environment secrets** - Railway, Render, Vercel, etc.
3. **Enable error logging** - Sentry, LogRocket, etc.
4. **Add request retries** - For network resilience
5. **Implement caching** - Reduce API calls
6. **Monitor API usage** - Track costs and limits
7. **Rate limiting** - Implement on backend
8. **Validate responses** - Don't trust external data

---

## Contributing

When adding or modifying services:

1. Update TypeScript types
2. Add JSDoc comments
3. Update this README
4. Add tests
5. Update BACKEND_API.md if API changes
