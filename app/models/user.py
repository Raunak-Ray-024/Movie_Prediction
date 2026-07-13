# # app/models/user.py
# from sqlalchemy import Column, Integer, Float, DateTime, String
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from app.database import Base

# class User(Base):
#     __tablename__ = "users"
    
#     user_id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(50), unique=True, nullable=False)
#     email = Column(String(100), unique=True, nullable=False)
#     password_hash = Column(String, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
    
#     # Relationships - SAB FIXED
#     ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    
#     favourites = relationship("Favourite", back_populates="user", cascade="all, delete-orphan")  # ✅ Sahi
    
#     watch_history = relationship("Watch", back_populates="user", cascade="all, delete-orphan")
#     reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")







from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1)
    
    # Relationships
    ratings = relationship("Rating", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    watch_history = relationship("WatchHistory", back_populates="user")
    favourites = relationship("Favourite", back_populates="user")
    logins = relationship("UserLogin", back_populates="user")
    activities = relationship("UserActivity", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")