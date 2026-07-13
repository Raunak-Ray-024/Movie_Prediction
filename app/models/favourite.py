from sqlalchemy import Column,Integer,ForeignKey
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base
class Favourite(Base):
    __tablename__="favourites"
    favourite_id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.user_id"),nullable=False)
    movie_id=Column(Integer,ForeignKey("movies.movie_id"),nullable=False)
    added_at=Column(DateTime,default=datetime.utcnow)
    user=relationship("User",back_populates="favourites")
    movie=relationship("Movie",back_populates="favourites")

