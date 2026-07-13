from sqlalchemy import Column,Integer,String,DateTime,ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base
class Review(Base):
    __tablename__="reviews"
    review_id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.user_id"),nullable=False)
    movie_id=Column(Integer,ForeignKey("movies.movie_id"),nullable=False)
    review_text=Column(String)
    created_at=Column(DateTime,default=datetime.utcnow)
    user=relationship("User",back_populates="reviews")
    movie=relationship("Movie",back_populates="reviews")


