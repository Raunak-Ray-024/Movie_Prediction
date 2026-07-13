# # from sqlalchemy import Column,Integer,Float,DateTime,String
# # from sqlalchemy.orm import relationship
# # from datetime import datetime
# # from app.database import Base
# # class Movie(Base):
# #     __tablename__="movies"
# #     movie_id = Column(Integer, primary_key=True, index=True)
# #     title = Column(String(255), nullable=False)
# #     genres=Column(String,nullable=False)
# #     overview = Column(String)
# #     imdb_id = Column(String(20), unique=True)
# #     homepage = Column(String)
# #     poster_path = Column(String)
# #     popularity = Column(Float)
# #     release_date = Column(DateTime)
# #     runtime = Column(Integer)
# #     status = Column(String(50))
# #     vote_count = Column(Integer)

# #     # Relationships
# # # app/models/movie.py
# #     ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")  # ✅ Sahi

# #     favorites = relationship(
# #         "Favourite",
# #         back_populates="favourites",
# #         cascade="all, delete-orphan"
# #     )

# #     watch_history = relationship(
# #         "Watch",
# #         back_populates="watch_history",
# #         cascade="all, delete-orphan"
# #     )

# #     reviews = relationship(
# #         "Review",
# #         back_populates="reviews",
# #         cascade="all, delete-orphan"
# #     )

# #     movie_genres = relationship(
# #     "MovieGenre",
# #     back_populates="movie_genres",
# #     cascade="all, delete-orphan"
# # )



# # app/models/movie.py
# from sqlalchemy import Column, Integer, Float, DateTime, String
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from app.database import Base

# class Movie(Base):
#     __tablename__ = "movies"
    
#     movie_id = Column(Integer, primary_key=True, index=True)
#     title = Column(String(255), nullable=False)
#     genres = Column(String, nullable=False)
#     overview = Column(String)
#     imdb_id = Column(String(20), unique=True)
#     homepage = Column(String)
#     poster_path = Column(String)
#     popularity = Column(Float)
#     release_date = Column(DateTime)
#     runtime = Column(Integer)
#     status = Column(String(50))
#     vote_count = Column(Integer)

#     # ============================================
#     # RELATIONSHIPS - SAB FIXED
#     # ============================================
    
#     # Rating - Sahi
#     ratings = relationship(
#         "Rating",
#         back_populates="movie",
#         cascade="all, delete-orphan"
#     )

#     # Favourite - ✅ YAHAN FIX KARO
#     favourites = relationship(  # ✅ 'favorites' ki jagah 'favourites' (British spelling)
#         "Favourite",
#         back_populates="favourites",  # ✅ 'favourites' - favourite.py mein same hai
#         cascade="all, delete-orphan"
#     )

#     # Watch History - ✅ FIXED
#     watch_history = relationship(
#         "Watch",
#         back_populates="watch_history",
#         cascade="all, delete-orphan"
#     )

#     # Reviews - ✅ FIXED
#     reviews = relationship(
#         "Review",
#         back_populates="reviews",
#         cascade="all, delete-orphan"
#     )

#     # Movie Genres - ✅ FIXED
#     movie_genres = relationship(
#         "MovieGenre",
#         back_populates="movie_genres",
#         cascade="all, delete-orphan"
#     )


# app/models/movie.py - YEH EXACT COPY KARO
from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Movie(Base):
    __tablename__ = "movies"
    
    movie_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    genres = Column(String, nullable=False)
    overview = Column(String)
    imdb_id = Column(String(20), unique=True)
    homepage = Column(String)
    poster_path = Column(String)
    popularity = Column(Float)
    release_date = Column(DateTime)
    runtime = Column(Integer)
    status = Column(String(50))
    vote_count = Column(Integer)

    # ============================================
    # RELATIONSHIPS - SAB FIXED
    # ============================================
    
    ratings = relationship(
        "Rating",
        back_populates="movie",  # ✅ rating.py mein 'movie' hai
        cascade="all, delete-orphan"
    )

    favourites = relationship(
        "Favourite",
        back_populates="movie",  # ✅ favourite.py mein 'movie' hai, 'favourites' nahi!
        cascade="all, delete-orphan"
    )

    watch_history = relationship(
        "WatchHistory",
        back_populates="movie",  # ✅ watch_history.py mein 'movie' hai
        cascade="all, delete-orphan"
    )

    reviews = relationship(
        "Review",
        back_populates="movie",  # ✅ review.py mein 'movie' hai
        cascade="all, delete-orphan"
    )

    movie_genres = relationship(
        "MovieGenre",
        back_populates="movie",  # ✅ movie_genre.py mein 'movie' hai
        cascade="all, delete-orphan"
    )