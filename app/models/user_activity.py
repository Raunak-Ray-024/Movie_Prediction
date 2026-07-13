from sqlalchemy import Column,Integer,String,DateTime,ForeignKey,Text,JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class UserLogin(Base):
    __tablename__="user_logins"
    login_id=Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    session_duration = Column(Integer, nullable=True) 
    user=relationship("User",back_populates="logins")

class UserActivity(Base):
    __tablename__="user_activities"
    activity_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    activity_timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user = relationship("User", back_populates="activities")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    session_id = Column(String(255), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    
    # Relationship
    user = relationship("User", back_populates="sessions")