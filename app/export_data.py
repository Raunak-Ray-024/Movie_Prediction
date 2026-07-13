import pandas as pd
from app.database import SessionLocal
from app.models.movie import Movie
from app.models.rating import Rating
from app.models.user import User
from app.models.movie_genre import MovieGenre
from app.models.genre import Genre
import os

os.makedirs('ml_data',exist_ok=True)

db=SessionLocal()

#export ratings
ratings=db.query(Rating).all()
ratings_df=pd.DataFrame([{
    'user_id':r.user_id,
    'movie_id':r.movie_id,
    'rating':r.rating,
    'timestamp':r.rated_at
    } 
    for r in ratings
    ])
ratings_df.to_csv('ml_data/ratingsml.csv',index=False)
print("ratings exported")

#exporting movies
movies_data=[]
movies=db.query(Movie).all()

for i in movies:
    genre_names=db.query(Genre.genre_name).join(
        MovieGenre,MovieGenre.genre_id==Genre.genre_id).filter(
            MovieGenre.movie_id==i.movie_id).all()

    genres_str='|'.join([g[0] for g in genre_names])
    movies_data.append({
        'movie_id': i.movie_id,
        'title': i.title,
        'genres': genres_str,
        'popularity': i.popularity or 0,
        'vote_count': i.vote_count or 0
    })

movies_df=pd.DataFrame(movies_data)
movies_df.to_csv('ml_data/moviesml.csv',index=False)
print("movies exported")

db.close()