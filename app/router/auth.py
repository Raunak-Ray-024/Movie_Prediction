from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import hashlib
import secrets
import json

from app.database import get_db
from app.models.user import User
from app.models.user_activity import UserLogin, UserActivity, UserSession
from app.models.watch_history import WatchHistory
from app.models.rating import Rating
from app.models.review import Review
from app.models.favourite import Favourite

router = APIRouter(prefix='/api/auth', tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LogoutRequest(BaseModel):
    user_id: int
    session_id: Optional[str] = None

class ActivityRequest(BaseModel):
    user_id: int
    activity_type: str
    details: Optional[dict] = None

# Helper function to hash passwords
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Helper to get client IP
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# Helper to get user agent
def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")

@router.post("/register")
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check if username exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email exists
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Log registration activity
        activity = UserActivity(
            user_id=new_user.user_id,
            activity_type="register",
            details={"username": user_data.username, "email": user_data.email}
        )
        db.add(activity)
        db.commit()
        
        return {
            "message": "User registered successfully",
            "user_id": new_user.user_id,
            "username": new_user.username,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """User login with tracking"""
    try:
        # Find user
        user = db.query(User).filter(User.username == login_data.username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if user.password_hash != hash_password(login_data.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Create session
        session = UserSession(
            session_id=session_token,
            user_id=user.user_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_active=1
        )
        db.add(session)
        
        # Log login activity
        login_record = UserLogin(
            user_id=user.user_id,
            login_time=datetime.utcnow(),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        db.add(login_record)
        
        # Log activity
        activity = UserActivity(
            user_id=user.user_id,
            activity_type="login",
            details={"session_id": session_token[:8] + "..."},
            ip_address=get_client_ip(request)
        )
        db.add(activity)
        
        db.commit()
        
        return {
            "message": "Login successful",
            "user_id": user.user_id,
            "username": user.username,
            "session_token": session_token,
            "last_login": user.last_login,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """User logout with tracking"""
    try:
        # Find user
        user = db.query(User).filter(User.user_id == logout_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update active session if session_id provided
        if logout_data.session_id:
            session = db.query(UserSession).filter(
                UserSession.session_id == logout_data.session_id,
                UserSession.user_id == logout_data.user_id,
                UserSession.is_active == 1
            ).first()
            if session:
                session.is_active = 0
                session.expires_at = datetime.utcnow()
        
        # Update last login record with logout time
        last_login = db.query(UserLogin).filter(
            UserLogin.user_id == logout_data.user_id
        ).order_by(UserLogin.login_time.desc()).first()
        
        if last_login and not last_login.logout_time:
            last_login.logout_time = datetime.utcnow()
            if last_login.login_time:
                duration = (last_login.logout_time - last_login.login_time).total_seconds()
                last_login.session_duration = int(duration)
        
        # Log logout activity
        activity = UserActivity(
            user_id=logout_data.user_id,
            activity_type="logout",
            ip_address=get_client_ip(request)
        )
        db.add(activity)
        
        db.commit()
        
        return {
            "message": "Logout successful",
            "user_id": logout_data.user_id,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/activity")
async def log_activity(
    activity_data: ActivityRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Log user activity"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.user_id == activity_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Log activity
        activity = UserActivity(
            user_id=activity_data.user_id,
            activity_type=activity_data.activity_type,
            details=activity_data.details,
            ip_address=get_client_ip(request)
        )
        db.add(activity)
        db.commit()
        
        return {
            "message": "Activity logged successfully",
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def get_user_sessions(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's active sessions"""
    try:
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == 1
        ).all()
        
        return {
            "user_id": user_id,
            "active_sessions": len(sessions),
            "sessions": [
                {
                    "session_id": s.session_id[:8] + "...",
                    "created_at": s.created_at,
                    "expires_at": s.expires_at
                }
                for s in sessions
            ],
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_user_activity_history(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get user's activity history"""
    try:
        activities = db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(
            UserActivity.activity_timestamp.desc()
        ).limit(limit).all()
        
        return {
            "user_id": user_id,
            "total_activities": len(activities),
            "activities": [
                {
                    "activity_id": a.activity_id,
                    "type": a.activity_type,
                    "timestamp": a.activity_timestamp,
                    "details": a.details,
                    "ip": a.ip_address
                }
                for a in activities
            ],
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{user_id}")
async def get_user_activity_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user activity statistics"""
    try:
        # Get total logins
        total_logins = db.query(UserLogin).filter(
            UserLogin.user_id == user_id
        ).count()
        
        # Get total activities
        total_activities = db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).count()
        
        # Get login history with durations
        logins = db.query(UserLogin).filter(
            UserLogin.user_id == user_id,
            UserLogin.logout_time.isnot(None)
        ).all()
        
        avg_duration = 0
        if logins:
            total_duration = sum(l.session_duration or 0 for l in logins)
            avg_duration = total_duration // len(logins) if logins else 0
        
        # Get activity breakdown
        activity_types = db.query(
            UserActivity.activity_type,
            db.func.count(UserActivity.activity_id)
        ).filter(
            UserActivity.user_id == user_id
        ).group_by(
            UserActivity.activity_type
        ).all()
        
        return {
            "user_id": user_id,
            "statistics": {
                "total_logins": total_logins,
                "total_activities": total_activities,
                "average_session_duration": avg_duration,
                "activity_breakdown": [
                    {"type": at[0], "count": at[1]}
                    for at in activity_types
                ]
            },
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))