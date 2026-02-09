# 🤖 Mentorship AI Assistant | IntelliCV AI Platform

A production-ready React application for AI-powered mentorship with real backend integration.

![Mentorship AI Assistant](./screenshot.png)

## 🌟 Features

### Core Functionality
- **🎯 Discovery Question Generator** - AI-powered question generation tailored to mentee goals
- **📝 Session Document Generator** - Transform notes into structured mentorship documents
- **🎥 Technique Review** - Get AI feedback on mentorship questioning techniques
- **💬 Community Forum** - Connect with other mentors (backend required)
- **📚 Knowledge Base** - Access curated mentorship resources (backend required)

### Technical Features
- ✅ Real AI chatbot integration (OpenAI/Anthropic)
- ✅ Production-ready backend service architecture
- ✅ Authentication and session management
- ✅ Responsive design with background imagery
- ✅ Error handling and loading states
- ✅ TypeScript for type safety
- ✅ Modular service layer
- ✅ Environment-based configuration

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+ (for backend)
- OpenAI API key or backend with AI integration

### 1. Clone and Install

```bash
# Install frontend dependencies
npm install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env
```

Edit `.env`:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000/api

# Optional: Direct OpenAI fallback (if backend unavailable)
VITE_OPENAI_API_KEY=sk-your-key-here
```

### 3. Start Backend (Choose One Option)

#### Option A: Use Provided Stub

```bash
cd backend_stub
pip install -r requirements.txt
cp .env.example .env
# Add your OpenAI key to .env
python main.py
```

#### Option B: Implement Your Own Backend

See [BACKEND_API.md](./BACKEND_API.md) for complete API specification.

### 4. Start Frontend

```bash
npm run dev
```

Visit http://localhost:5173

## 📁 Project Structure

```
/
├── src/
│   ├── app/
│   │   ├── App.tsx                 # Main application component
│   │   └── components/
│   │       └── ui/                 # Reusable UI components
│   ├── services/
│   │   ├── api.ts                  # Base API service
│   │   ├── authService.ts          # Authentication
│   │   ├── chatService.ts          # AI chat integration
│   │   ├── forumService.ts         # Forum operations
│   │   ├── knowledgeBaseService.ts # Knowledge base
│   │   ├── config.ts               # Configuration
│   │   └── index.ts                # Service exports
│   └── styles/                     # Global styles
├── backend_stub/
│   ├── main.py                     # FastAPI backend stub
│   ├── requirements.txt            # Python dependencies
│   └── README.md                   # Backend documentation
├── .env.example                    # Environment template
├── BACKEND_API.md                  # API specification
└── README.md                       # This file
```

## 🏗️ Architecture

### Frontend Architecture

```
┌─────────────────────────────────────┐
│         App.tsx (Main UI)           │
│  - Tab-based interface              │
│  - State management                 │
│  - Error handling                   │
└──────────────┬──────────────────────┘
               │
               ├─────────────┐
               │             │
        ┌──────▼──────┐  ┌──▼────────────┐
        │  Services   │  │  Components   │
        │  Layer      │  │  (UI)         │
        │             │  │               │
        │ • Chat      │  │ • Cards       │
        │ • Auth      │  │ • Tabs        │
        │ • Forum     │  │ • Buttons     │
        │ • KB        │  │ • Forms       │
        └──────┬──────┘  └───────────────┘
               │
        ┌──────▼──────────┐
        │   Backend API   │
        │   (FastAPI)     │
        └──────┬──────────┘
               │
        ┌──────▼──────────┐
        │   OpenAI API    │
        └─────────────────┘
```

### Service Layer

The application uses a modular service architecture:

1. **API Service** (`api.ts`) - Base HTTP client with error handling
2. **Chat Service** (`chatService.ts`) - AI chat integration with fallback
3. **Auth Service** (`authService.ts`) - Session management
4. **Forum Service** (`forumService.ts`) - Community features
5. **Knowledge Base Service** (`knowledgeBaseService.ts`) - Resource access

### Authentication Flow

```
User Request → Auth Service → Session Check → Backend Validation → Access Granted/Denied
```

For development, a mock session is provided. In production:
- Replace with real JWT authentication
- Validate tokens on backend
- Store sessions securely

## 🔒 Security & Policy

### Core Policies

✅ **No Fabricated Content** - AI responses are real, not mocked  
✅ **Backend Required** - No local AI processing (prevents key exposure)  
✅ **No PII Collection** - Figma Make is not for sensitive data  
✅ **Mentor Access Only** - Role-based access control  

### Security Checklist for Production

- [ ] Implement real JWT authentication
- [ ] Use HTTPS only
- [ ] Store API keys in secure vault (not .env)
- [ ] Add rate limiting
- [ ] Implement input sanitization
- [ ] Enable CORS for specific domains
- [ ] Add request logging
- [ ] Implement content filtering
- [ ] Regular security audits
- [ ] Data encryption at rest

## 🎨 Customization

### Change AI Provider

Edit `src/services/chatService.ts`:

```typescript
// Switch from OpenAI to Anthropic
const response = await fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': AI_CONFIG.ANTHROPIC_API_KEY,
    'anthropic-version': '2023-06-01'
  },
  body: JSON.stringify({
    model: 'claude-3-opus-20240229',
    messages: payload.messages,
    max_tokens: AI_CONFIG.MAX_TOKENS
  })
});
```

### Customize System Prompts

In `App.tsx`, modify system prompts for each feature:

```typescript
const response = await callChat(
  prompt,
  'Your custom system prompt here'
);
```

### Styling

The app uses:
- **Tailwind CSS** for utility classes
- **shadcn/ui** for component library
- **Background image** from `figma:asset`

To change the background:
```typescript
// In App.tsx
import newBackground from 'figma:asset/your-image-id.png';
```

## 📡 API Integration

### Backend Requirements

Your backend must implement:

1. **POST /api/chat** - AI chat endpoint
2. **GET /api/auth/session** - Session validation
3. **GET /api/health** - Health check

See [BACKEND_API.md](./BACKEND_API.md) for complete specification.

### Response Format

The chat service accepts flexible response formats:

```json
// Option 1
{ "reply": "AI response..." }

// Option 2
{ "message": "AI response..." }

// Option 3
{ "data": { "reply": "AI response..." } }
```

## 🧪 Testing

### Test Chat Service

```typescript
import { chatService } from './services';

const response = await chatService.sendChat({
  messages: [
    { role: 'system', content: 'You are a helpful assistant' },
    { role: 'user', content: 'Hello!' }
  ]
}, 'user_id');
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# Chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"user_id":"test"}'
```

## 🚢 Deployment

### Frontend (Vercel/Netlify)

```bash
npm run build
# Deploy dist/ folder
```

Environment variables to set:
- `VITE_API_BASE_URL` - Your production API URL

### Backend (Railway/Render/AWS)

```bash
cd backend_stub
# Deploy with your preferred platform
```

Environment variables to set:
- `OPENAI_API_KEY` - Your OpenAI key
- `ALLOWED_ORIGINS` - Your frontend URL

## 📚 Documentation

- [Backend API Specification](./BACKEND_API.md)
- [Backend Stub README](./backend_stub/README.md)
- [Service Layer Documentation](./src/services/README.md)

## 🐛 Troubleshooting

### "Backend chat bridge not available"

**Solution:** 
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Verify `VITE_API_BASE_URL` in `.env`
3. Check CORS settings in backend
4. As fallback, set `VITE_OPENAI_API_KEY` (not recommended for production)

### "Mentor access only"

**Solution:**
- The app requires mentor role authentication
- In development, mock session is provided
- Check `authService.ts` for session configuration

### Chat responses not appearing

**Solution:**
1. Check browser console for errors
2. Verify backend logs
3. Test backend directly with curl
4. Check OpenAI API key is valid

### CORS errors

**Solution:**
```python
# In backend main.py, update CORS origins:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📄 License

Proprietary - IntelliCV AI Platform

---

**Built with:**
- React + TypeScript
- Tailwind CSS
- shadcn/ui
- FastAPI
- OpenAI API

**For support:** Contact your platform administrator
