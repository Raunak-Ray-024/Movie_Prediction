from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Genre(Base):
    __tablename__ = "genres"

    genre_id = Column(Integer, primary_key=True, index=True)

    genre_name = Column(String(50), unique=True, nullable=False)

    # Relationships
    movie_genres = relationship(
        "MovieGenre",
        back_populates="genre",
        cascade="all, delete-orphan"
    )