import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from app.models.rating import Rating
from app.models.user import User
from app.models.watch_history import WatchHistory  
from app.models.favourite import Favourite
from app.models.review import Review

class MovieRecommender:
    def __init__(self, model_path='app/ml_module/saved_model'):
        self.model_path = Path(model_path)
        self.model = None
        self.movies = None
        self.user_avg = None
        self.db_session=None
        self.load_models()
    
    def load_models(self):
        try:
            self.model = joblib.load(self.model_path / 'svd_model.pkl')
            self.movies = joblib.load(self.model_path / 'movies.pkl')
            self.user_avg = joblib.load(self.model_path / 'user_avg.pkl')
            print("models loaded")
        except Exception as e:
            print("not loaded")
            raise

    def set_db_session(self,db:Session):
        self.db_session=db
    
    def predict_rating(self, user_id: int, movie_id: int) -> float:
        try:
            if self.db_session:
                from models.rating import Rating
                from models.user import User
                avg_rating=self.db_session.query(
                    Rating.rating
                ).filter(Rating.user_id==user_id).all()
                if avg_rating:
                    user_avg=sum(r[0]for r in avg_rating)/len(avg_rating)
                else:
                    user_avg=3.0
            else:
                user_avg=self.user_avg.get(user_id,3.0)

            svd_pred = self.model.predict(user_id, movie_id).est
            rating=0.85*svd_pred+0.15*user_avg
            return round(rating,2)
        except Exception as e:
            print("error")
            return 0.0
        
    def get_movie_title(self, movie_id: int) -> str:
        try:
            title = self.movies[self.movies['movie_id'] == movie_id]['title'].values[0]
            return title
        except:
            return "Unknown movie"

    def get_movie_genre(self, movie_id: int) -> str:
        try:
            genre = self.movies[self.movies['movie_id'] == movie_id]['genres'].values[0]
            return genre
        except:
            return "Unknown"

    def get_top_recommendations(self, user_id: int, top_n: int = 10, db=None):
        """Get recommendations using real-time user data from DB"""
        try:
            print(f"Getting recommendations for user {user_id}")
            
            # Get all movie IDs
            all_movies = self.movies['movie_id'].values
            print(f"Total movies: {len(all_movies)}")
            
            # Get user's watched and favorite movies from DB
            watched_movies = []
            fav_movies = []
            
            if db:
                try:
                    from models.watch_history import WatchHistory
                    from models.favourite import Favourite
                    
                    watched = db.query(WatchHistory.movie_id).filter(
                        WatchHistory.user_id == user_id
                    ).all()
                    watched_movies = [w[0] for w in watched]
                    print(f"User has watched {len(watched_movies)} movies")
                    
                    favorites = db.query(Favourite.movie_id).filter(
                        Favourite.user_id == user_id
                    ).all()
                    fav_movies = [f[0] for f in favorites]
                    print(f"User has {len(fav_movies)} favorites")
                except Exception as e:
                    print(f"Error fetching user data from DB: {e}")
                    # Continue with empty lists if DB fails
            
            predictions = []
            
            # Limit to first 100 movies for performance
            for movie_id in all_movies[:100]:
                # Skip if already watched or favorited
                if movie_id in watched_movies or movie_id in fav_movies:
                    continue
                
                # Get title and genre
                title = self.get_movie_title(movie_id)
                genre = self.get_movie_genre(movie_id)
                
                # Predict rating
                try:
                    pred = self.predict_rating(user_id, movie_id)
                except:
                    pred = 3.0  # Default rating
                
                # Calculate boost (if movie shares genre with favorites)
                boost = 0
                if fav_movies:
                    for fav_id in fav_movies[:3]:
                        fav_genre = self.get_movie_genre(fav_id)
                        if fav_genre != "Unknown" and fav_genre == genre:
                            boost = 0.5
                            break
                
                predictions.append({
                    'movie_id': int(movie_id),
                    'title': title,
                    'genre': genre,
                    'predicted_rating': round(pred + boost, 2)
                })
            
            print(f"Generated {len(predictions)} predictions")
            
            # Sort by predicted rating
            predictions.sort(key=lambda x: x['predicted_rating'], reverse=True)
            
            result = predictions[:top_n]
            print(f"Returning {len(result)} recommendations")
            
            # If no predictions, return popular movies
            if not result:
                print("No predictions, returning popular movies")
                result = self.get_popular_movies(top_n)
            
            return result
            
        except Exception as e:
            print(f"Error in get_top_recommendations: {e}")
            import traceback
            traceback.print_exc()
            
            # Return popular movies as fallback
            try:
                return self.get_popular_movies(top_n)
            except:
                return []  # Return empty list if even popular fails

    def get_popular_movies(self, limit: int = 20):
        """Get popular movies (fallback)"""
        try:
            print("Getting popular movies as fallback")
            # Return first N movies
            result = self.movies[['movie_id', 'title', 'genres']].head(limit).to_dict('records')
            # Add predicted_rating field
            for r in result:
                r['predicted_rating'] = 4.0
            return result
        except Exception as e:
            print(f"Error getting popular movies: {e}")
            return []




    def _get_interaction_boost(self, user_id: int, movie_id: int, db: Session) -> float:
        """Calculate boost based on user's recent interactions"""
        try:
            if not db:
                return 0.0
            
            from models.review import Review
            from models.rating import Rating
            from models.watch_history import WatchHistory
            
            # Check recent interactions (last 7 days)
            recent_ratings = db.query(Rating).filter(
                Rating.user_id == user_id,
                Rating.timestamp > datetime.utcnow() - timedelta(days=7)
            ).count()
            
            recent_reviews = db.query(Review).filter(
                Review.user_id == user_id,
                Review.timestamp > datetime.utcnow() - timedelta(days=7)
            ).count()
            
            recent_watches = db.query(WatchHistory).filter(
                WatchHistory.user_id == user_id,
                WatchHistory.watched_at > datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Boost based on activity (max 0.3)
            total_interactions = recent_ratings + recent_reviews + recent_watches
            return min(total_interactions * 0.01, 0.3)
        except:
            return 0.0
    
    def _get_favorite_boost(self, movie_id: int, favorite_movies: List[int], db: Session) -> float:
        """Boost based on similarity to user's favorite movies"""
        try:
            if not favorite_movies:
                return 0.0
            
            # Get genre of current movie
            current_genre = self.get_movie_genre(movie_id)
            if not current_genre or current_genre == "Unknown":
                return 0.0
            
            # Get genres of favorite movies
            fav_genres = []
            for fav_id in favorite_movies[:5]:  # Check top 5 favorites
                fav_genre = self.get_movie_genre(fav_id)
                if fav_genre != "Unknown":
                    fav_genres.append(fav_genre)
            
            # Check genre overlap
            current_genres = set(current_genre.split('|'))
            overlap = 0
            for genre in fav_genres:
                fav_genres_set = set(genre.split('|'))
                common = len(current_genres & fav_genres_set)
                if common > 0:
                    overlap += common
            
            # Boost based on genre similarity (max 0.4)
            return min(overlap * 0.1, 0.4)
        except:
            return 0.0
    
    def get_movie_id_by_title(self, title: str):
        try:
            result = self.movies[self.movies['title'].str.lower() == title.lower()]
            if result.empty:
                result = self.movies[self.movies['title'].str.lower().str.contains(title.lower(), na=False)]
            if not result.empty:
                return int(result.iloc[0]['movie_id'])
            return None
        except Exception as e:
            print(f"Error finding movie: {e}")
            return None

    def search_movies_by_title(self, query: str, limit: int = 10):
        try:
            mask = self.movies['title'].str.lower().str.contains(query.lower(), na=False)
            results = self.movies[mask].head(limit)
            return results[['movie_id', 'title', 'genres']].to_dict('records')
        except Exception as e:
            print(f"Error searching movies: {e}")
            return []

    def get_popular_movies(self, limit: int = 20):
        try:
            return self.movies[['movie_id', 'title', 'genres']].head(limit).to_dict('records')
        except Exception as e:
            print(f"Error getting popular movies: {e}")
            return []
    
    def get_similar_movies(self, movie_id: int, top_n: int = 10) -> List[Dict[str, Any]]:
        try:
            genre = self.get_movie_genre(movie_id)
            similar = self.movies[self.movies['genres'] == genre]
            similar = similar[similar['movie_id'] != movie_id]
            results = []
            for _, row in similar.head(top_n).iterrows():
                results.append({
                    'movie_id': int(row['movie_id']),
                    'title': row['title'],
                    'genre': row['genre']
                })
            return results
        except Exception as e:
            print("error")
            return []

recommender = MovieRecommender()