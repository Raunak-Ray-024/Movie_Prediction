from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    id = Column(Integer, primary_key=True, index=True)

    movie_id = Column(
        Integer,
        ForeignKey("movies.movie_id"),
        nullable=False
    )

    genre_id = Column(
        Integer,
        ForeignKey("genres.genre_id"),
        nullable=False
    )

    # Relationships
    movie = relationship(
        "Movie",
        back_populates="movie_genres"
    )

    genre = relationship(
        "Genre",
        back_populates="movie_genres"
    )