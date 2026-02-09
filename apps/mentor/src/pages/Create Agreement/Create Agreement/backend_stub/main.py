"""
Mentorship AI Assistant - Backend API Stub
FastAPI implementation

Install dependencies:
    pip install fastapi uvicorn openai python-dotenv pydantic

Run server:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import openai
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Mentorship AI Assistant API",
    description="Backend API for IntelliCV AI Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# ============================================================================
# Models
# ============================================================================

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = None
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

class ChatResponse(BaseModel):
    reply: str

class User(BaseModel):
    id: str
    role: str
    email: str
    name: str
    mentor_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    user: User
    token: str

# ============================================================================
# Dependency: Authentication
# ============================================================================

def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    """
    Validate authentication token and return user.
    For this stub, we'll return a mock user.
    """
    if not authorization:
        # For development, return mock user
        return {
            "id": "mentor_dev_001",
            "role": "mentor",
            "email": "mentor@intellicv.ai",
            "name": "Development Mentor",
            "mentor_id": "mentor_dev_001"
        }
    
    # In production, validate JWT token here
    # For now, return mock user
    return {
        "id": x_user_id or "mentor_dev_001",
        "role": "mentor",
        "email": "mentor@intellicv.ai",
        "name": "Development Mentor",
        "mentor_id": x_user_id or "mentor_dev_001"
    }

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Check if the API is running"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.get("/api/auth/session")
async def get_session(user: dict = Depends(get_current_user)):
    """Get current user session"""
    return {
        "user": user,
        "token": "dev_token_12345"
    }

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login user"""
    # Mock authentication - accept any credentials
    return {
        "user": {
            "id": "mentor_001",
            "role": "mentor",
            "email": request.email,
            "name": "Test Mentor",
            "mentor_id": "mentor_001"
        },
        "token": "mock_jwt_token_12345"
    }

@app.get("/api/auth/validate")
async def validate_session(user: dict = Depends(get_current_user)):
    """Validate current session"""
    return {"valid": True}

@app.post("/api/auth/logout")
async def logout():
    """Logout user"""
    return {"success": True}

# ============================================================================
# Chat Endpoints
# ============================================================================

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user)
):
    """
    Send chat message to AI assistant.
    
    This endpoint proxies requests to OpenAI API.
    """
    try:
        # Validate OpenAI API key
        if not openai.api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Set OPENAI_API_KEY in .env file."
            )
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=request.model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Extract reply
        reply = response.choices[0].message.content
        
        # Log the interaction (in production, save to database)
        print(f"[CHAT] User: {user['id']}, Model: {request.model}")
        print(f"[CHAT] User message: {request.messages[-1].content[:100]}...")
        print(f"[CHAT] AI reply: {reply[:100]}...")
        
        return {"reply": reply}
        
    except openai.error.AuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Invalid OpenAI API key"
        )
    except openai.error.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="OpenAI API rate limit exceeded"
        )
    except openai.error.APIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat service error: {str(e)}"
        )

# ============================================================================
# Forum Endpoints (Stubs)
# ============================================================================

@app.get("/api/forum/posts")
async def get_forum_posts(
    page: int = 1,
    limit: int = 20,
    tag: Optional[str] = None
):
    """Get forum posts (stub implementation)"""
    return {
        "posts": [
            {
                "id": "post_001",
                "title": "Best practices for first mentorship session",
                "content": "I'm starting my first mentorship session next week...",
                "author": {
                    "id": "mentor_002",
                    "name": "Jane Smith",
                    "role": "mentor"
                },
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
                "replies_count": 5,
                "likes_count": 12,
                "tags": ["best-practices", "getting-started"]
            }
        ],
        "total": 1
    }

@app.post("/api/forum/posts")
async def create_forum_post(data: Dict[str, Any]):
    """Create forum post (stub implementation)"""
    return {
        "id": "post_new",
        "title": data.get("title"),
        "content": data.get("content"),
        "author": {
            "id": "mentor_001",
            "name": "Current User",
            "role": "mentor"
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "replies_count": 0,
        "likes_count": 0,
        "tags": data.get("tags", [])
    }

# ============================================================================
# Knowledge Base Endpoints (Stubs)
# ============================================================================

@app.get("/api/knowledge/categories")
async def get_kb_categories():
    """Get knowledge base categories (stub implementation)"""
    return [
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

@app.get("/api/knowledge/popular")
async def get_popular_articles(limit: int = 10):
    """Get popular knowledge base articles (stub implementation)"""
    return [
        {
            "id": "article_001",
            "title": "Setting Effective Mentorship Goals",
            "content": "## Introduction\n\nSetting clear goals...",
            "category": "Getting Started",
            "tags": ["goals", "planning"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "views": 1250,
            "helpful_count": 89
        }
    ]

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
