from sqlalchemy import Column,Integer,DateTime,ForeignKey,Boolean,Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
class WatchHistory(Base):
    __tablename__="watch_history"
    history_id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.user_id"),nullable=False)
    movie_id=Column(Integer,ForeignKey("movies.movie_id"),nullable=False)
    watched_at=Column(DateTime,default=datetime.utcnow)
    completed=Column(Boolean,default=False)
    progress=Column(Float,default=0)
    user=relationship("User",back_populates="watch_history")
    movie=relationship("Movie",back_populates="watch_history")
