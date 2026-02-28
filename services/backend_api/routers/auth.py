
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security
from services.backend_api.middleware.login_protection import login_protection

router = APIRouter(prefix="/api/auth/v1", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except security.JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

@router.post("/register")
def register(email: str, password: str, full_name: str = None, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = security.get_password_hash(password)
    new_user = models.User(email=email, hashed_password=hashed_password, full_name=full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email}

@router.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # --- Brute-force protection ---
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")

    locked, retry_after = login_protection.is_locked_out(client_ip)
    if locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        login_protection.record_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    login_protection.record_success(client_ip)
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
        expires_delta=access_token_expires
    )
    refresh_tok = security.create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_tok,
        "token_type": "bearer",
    }


# --- Refresh Token Endpoint ---
@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        payload = security.jwt.decode(refresh_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except security.JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = security.create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
    )
    new_refresh = security.create_refresh_token(
        data={"sub": user.email},
    )
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


# --- Google OAuth2 Social Login ---
@router.post("/google")
async def google_login(id_token: str, db: Session = Depends(get_db)):
    """
    Authenticate via Google OAuth2 ID token.
    
    Frontend sends the Google ID token obtained from Google Sign-In.
    Backend verifies it, creates or finds the user, and returns JWT tokens.
    
    Requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars.
    """
    if not security.GOOGLE_OAUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    google_user = await security.verify_google_id_token(id_token)
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    if not google_user.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email not verified",
        )

    email = google_user["email"]
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        # Auto-register Google users
        user = models.User(
            email=email,
            hashed_password=security.get_password_hash(security.secrets.token_urlsafe(32)),
            full_name=google_user.get("name", ""),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
    )
    refresh_tok = security.create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_tok,
        "token_type": "bearer",
        "is_new_user": user.created_at is not None,
    }

# --- 2FA Enhancements ---
import pyotp
import qrcode
import io
import base64

@router.post("/2fa/generate")
def generate_2fa(db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)):
    # 1. Decode token to get user
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_email = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Generate Secret
    secret = pyotp.random_base32()
    
    # 3. Create QR Code
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="CareerTrojan")
    
    img = qrcode.make(uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # 4. Save Secret (Temporary/Pending Verification in real app, but saving directly for now)
    user.otp_secret = secret
    db.commit()

    return {"secret": secret, "qr_code": img_str}

@router.post("/2fa/verify")
def verify_2fa(code: str, db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)):
    # 1. Get User
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_email = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user or not user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA not set up")

    # 2. Verify Code
    totp = pyotp.TOTP(user.otp_secret)
    if totp.verify(code):
        return {"status": "verified", "message": "2FA Setup Complete"}
    else:
        raise HTTPException(status_code=400, detail="Invalid 2FA Code")

