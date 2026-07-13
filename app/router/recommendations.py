from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ml_module.recommender import recommender
from app.database import get_db
from app.models.user import User
from app.models.rating import Rating
from app.models.watch_history import WatchHistory
from app.models.favourite import Favourite
from app.models.review import Review

router = APIRouter(prefix="/api/recommendation",tags=["Recommendations"])

class RatingPredictionResponse(BaseModel):
    user_id: int
    movie_id: int
    movie_title: str
    predicted_rating: float
    status: str

class MovieRecommendation(BaseModel):
    movie_id: int
    title: str
    genre: str
    predicted_rating: float

class RecommendationsResponse(BaseModel):
    user_id: int
    recommendations: List[MovieRecommendation]
    status: str

@router.get("/users/{user_id}", response_model=RecommendationsResponse)
async def get_recommendations(
    user_id: int, 
    top_n: Optional[int] = 10,
    db: Session = Depends(get_db)
):
    try:
        print(f"Getting recommendations for user {user_id}")
        
        # Get recommendations with real-time data
        recommendations = recommender.get_top_recommendations(user_id, top_n, db)
        
        print(f"Received {len(recommendations) if recommendations else 0} recommendations")
        
        # If no recommendations, return empty list with status
        if not recommendations:
            print("No recommendations found, returning empty list")
            return RecommendationsResponse(
                user_id=user_id,
                recommendations=[],
                status="no_recommendations_found"
            )
        
        return RecommendationsResponse(
            user_id=user_id,
            recommendations=recommendations,
            status="success"
        )
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        import traceback
        traceback.print_exc()
        
        # Return empty list instead of raising error
        return RecommendationsResponse(
            user_id=user_id,
            recommendations=[],
            status=f"error: {str(e)}"
        )

@router.post("/predict_rating", response_model=RatingPredictionResponse)
async def predict_rating(
    user_id: int,
    movie_id: int,
    db: Session = Depends(get_db)
):
    try:
        rating = recommender.predict_rating(user_id, movie_id)
        title = recommender.get_movie_title(movie_id)
        
        if rating == 0.0:
            raise HTTPException(status_code=404, detail="Rating not found")
        
        return RatingPredictionResponse(
            user_id=user_id,
            movie_id=movie_id,
            movie_title=title,
            predicted_rating=rating,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similarity/{movie_id}")
async def get_similar_movies(
    movie_id: int,
    top_n: Optional[int] = 10
):
    try:
        similar = recommender.get_similar_movies(movie_id, top_n)
        if not similar:
            raise HTTPException(status_code=404, detail="No similar movies found")
        
        return {
            'movie_id': movie_id,
            'similar_movies': similar,
            'status': 'success'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/movies/search")
async def search_movies(query: str, limit: int = 10):
    """Search for movies by title"""
    try:
        results = recommender.search_movies_by_title(query, limit)
        return {
            "query": query,
            "count": len(results),
            "results": results,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/movies/popular")
async def get_popular_movies(limit: int = 20):
    """Get list of popular movies"""
    try:
        popular = recommender.get_popular_movies(limit)
        return {
            "count": len(popular),
            "movies": popular,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict_by_title")
async def predict_rating_by_title(
    user_id: int,
    movie_title: str,
    db: Session = Depends(get_db)
):
    """Predict rating using movie title"""
    try:
        movie_id = recommender.get_movie_id_by_title(movie_title)
        
        if movie_id is None:
            suggestions = recommender.search_movies_by_title(movie_title, 3)
            raise HTTPException(
                status_code=404,
                detail=f"Movie '{movie_title}' not found. Suggestions: {[s['title'] for s in suggestions]}"
            )
        
        rating = recommender.predict_rating(user_id, movie_id)
        title = recommender.get_movie_title(movie_id)
        
        return RatingPredictionResponse(
            user_id=user_id,
            movie_id=movie_id,
            movie_title=title,
            predicted_rating=rating,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch_predict")
async def batch_predict(
    user_id: int,
    movie_ids: str,
    db: Session = Depends(get_db)
):
    try:
        movie_list = [int(mid) for mid in movie_ids.split(',')]
        results = []
        
        for movie_id in movie_list:
            rating = recommender.predict_rating(user_id, movie_id)
            title = recommender.get_movie_title(movie_id)
            results.append({
                'movie_id': movie_id,
                'title': title,
                'predicted_rating': rating
            })
        
        return {
            'user_id': user_id,
            'predictions': results,
            'status': 'success'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))