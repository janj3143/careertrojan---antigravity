
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import urllib.request
import urllib.parse
import json
import os
import secrets

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security

router = APIRouter(prefix="/api/auth/v1", tags=["auth"])

GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "https://www.careertrojan.com/api/auth/v1/google/callback").strip()
GOOGLE_OAUTH_DOMAIN = os.getenv("GOOGLE_OAUTH_DOMAIN", "https://www.careertrojan.com").strip().rstrip("/")
GOOGLE_OAUTH_AUTHORIZED_ORIGINS = os.getenv("GOOGLE_OAUTH_AUTHORIZED_ORIGINS", "https://www.careertrojan.com").strip()


def _google_oauth_configured() -> bool:
    return bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET and GOOGLE_OAUTH_REDIRECT_URI)


def _build_google_auth_url(state: str) -> str:
    query = urlencode(
        {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "include_granted_scopes": "true",
            "prompt": "select_account",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def _exchange_google_code(code: str) -> dict:
    payload = urlencode(
        {
            "code": code,
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_google_userinfo(access_token: str) -> dict:
    req = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _resolve_post_login_url() -> str:
    post_login_url = os.getenv("GOOGLE_OAUTH_POST_LOGIN_URL", "").strip()
    if post_login_url:
        return post_login_url
    return f"{GOOGLE_OAUTH_DOMAIN}/login"


def _ensure_user_from_google(db: Session, email: str, full_name: str | None = None) -> models.User:
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        if full_name and not user.full_name:
            user.full_name = full_name
            db.commit()
            db.refresh(user)
        return user

    random_password = secrets.token_urlsafe(32)
    hashed_password = security.get_password_hash(random_password)
    user = models.User(email=email, hashed_password=hashed_password, full_name=full_name, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/v1/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except security.TokenValidationError:
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
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/google/login")
def google_login(next_path: str = "/"):
    if not _google_oauth_configured():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    normalized_next = next_path if next_path.startswith("/") else "/"
    state_payload = {"next": normalized_next, "nonce": secrets.token_urlsafe(16)}
    state = urllib.parse.quote(json.dumps(state_payload))
    return RedirectResponse(url=_build_google_auth_url(state), status_code=302)


@router.get("/google/callback")
def google_callback(code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    post_login_url = _resolve_post_login_url()

    if error:
        fail_url = f"{post_login_url}#oauth_error={urllib.parse.quote(error)}"
        return RedirectResponse(url=fail_url, status_code=302)

    if not code:
        fail_url = f"{post_login_url}#oauth_error=missing_code"
        return RedirectResponse(url=fail_url, status_code=302)

    try:
        token_payload = _exchange_google_code(code)
        google_access_token = token_payload.get("access_token")
        if not google_access_token:
            raise HTTPException(status_code=401, detail="Google token exchange failed")

        userinfo = _fetch_google_userinfo(google_access_token)
        email = (userinfo.get("email") or "").strip().lower()
        full_name = (userinfo.get("name") or "").strip() or None
        if not email:
            raise HTTPException(status_code=400, detail="Google account email not available")

        user = _ensure_user_from_google(db, email=email, full_name=full_name)
        access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.email, "role": user.role, "user_id": user.id},
            expires_delta=access_token_expires,
        )

        parsed_state = {}
        if state:
            try:
                parsed_state = json.loads(urllib.parse.unquote(state))
            except Exception:
                parsed_state = {}

        next_path = parsed_state.get("next", "/") if isinstance(parsed_state, dict) else "/"
        if not isinstance(next_path, str) or not next_path.startswith("/"):
            next_path = "/"

        success_fragment = urllib.parse.urlencode(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "provider": "google",
                "next": next_path,
            }
        )
        success_url = f"{post_login_url}#{success_fragment}"
        return RedirectResponse(url=success_url, status_code=302)
    except HTTPException:
        raise
    except Exception:
        fail_url = f"{post_login_url}#oauth_error=google_callback_failed"
        return RedirectResponse(url=fail_url, status_code=302)

# --- 2FA Enhancements ---
import io
import base64

@router.post("/2fa/generate")
def generate_2fa(db: Session = Depends(get_db), token: str = Depends(security.oauth2_scheme)):
    try:
        import pyotp
        import qrcode
    except Exception:
        raise HTTPException(status_code=503, detail="2FA dependencies are not installed")

    # 1. Decode token to get user
    try:
        payload = security.decode_access_token(token)
        user_email = payload.get("sub")
    except security.TokenValidationError:
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
    try:
        import pyotp
    except Exception:
        raise HTTPException(status_code=503, detail="2FA dependencies are not installed")

    # 1. Get User
    try:
        payload = security.decode_access_token(token)
        user_email = payload.get("sub")
    except security.TokenValidationError:
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

