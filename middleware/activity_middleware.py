from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database import SessionLocal
from app.models.user_activity import UserActivity

class ActivityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get user_id from request (you need to implement this based on your auth)
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        
        # Process request
        response = await call_next(request)
        
        # Log activity if user is authenticated
        if user_id:
            try:
                db = SessionLocal()
                activity = UserActivity(
                    user_id=user_id,
                    activity_type="api_call",
                    details={
                        "path": request.url.path,
                        "method": request.method,
                        "status_code": response.status_code
                    }
                )
                db.add(activity)
                db.commit()
                db.close()
            except Exception as e:
                print(f"Error logging activity: {e}")
        
        return response