from sqlalchemy import Column,Integer,Float,ForeignKey,DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
class Rating(Base):
    __tablename__="ratings"
    rating_id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.user_id"),nullable=False)
    movie_id=Column(Integer,ForeignKey("movies.movie_id"),nullable=False)
    rating=Column(Float,nullable=False)
    rated_at=Column(DateTime,default=datetime.utcnow)
    user=relationship("User",back_populates="ratings")
    movie=relationship("Movie",back_populates="ratings")
