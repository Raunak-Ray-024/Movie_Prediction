from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.user import User
from app.models.movie import Movie
from app.models.rating import Rating
from app.models.review import Review
from app.models.watch_history import WatchHistory
from app.models.favourite import Favourite
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre
from app.models.user_activity import UserActivity

router = APIRouter(prefix='/api/recommendation/users', tags=["User Actions"])

# ========== Pydantic Models ==========
class RatingInput(BaseModel):
    user_id: int
    movie_id: int
    rating: float
    review_text: Optional[str] = None

class WatchInput(BaseModel):
    user_id: int
    movie_id: int
    watch_duration: int  # in seconds
    completed: bool = False

class FavouriteInput(BaseModel):
    user_id: int
    movie_id: int

class ReviewInput(BaseModel):
    user_id: int
    movie_id: int
    review_text: str
    rating: Optional[float] = None

# ========== Response Models ==========
class RatingResponse(BaseModel):
    movie_id: int
    movie_title: str
    rating: float
    review_text: Optional[str]
    timestamp: datetime

class WatchHistoryResponse(BaseModel):
    movie_id: int
    movie_title: str
    watch_duration: int
    completed: bool
    timestamp: datetime

class FavouriteResponse(BaseModel):
    movie_id: int
    movie_title: str
    added_at: datetime

class ReviewResponse(BaseModel):
    movie_id: int
    movie_title: str
    review_text: str
    rating: Optional[float]
    timestamp: datetime

# ========== POST Endpoints (Create/Update) ==========

@router.post("/rate")
async def rate_movie(
    rating_input: RatingInput, 
    db: Session = Depends(get_db)
):
    """User rates a movie - updates rating table"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == rating_input.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if rating already exists
        existing = db.query(Rating).filter(
            Rating.user_id == rating_input.user_id,
            Rating.movie_id == rating_input.movie_id
        ).first()
        
        if existing:
            existing.rating = rating_input.rating
            existing.timestamp = datetime.utcnow()
        else:
            new_rating = Rating(
                user_id=rating_input.user_id,
                movie_id=rating_input.movie_id,
                rating=rating_input.rating,
                timestamp=datetime.utcnow()
            )
            db.add(new_rating)
        
        # If review text provided, add/update review
        if rating_input.review_text:
            existing_review = db.query(Review).filter(
                Review.user_id == rating_input.user_id,
                Review.movie_id == rating_input.movie_id
            ).first()
            
            if existing_review:
                existing_review.review_text = rating_input.review_text
                existing_review.rating = rating_input.rating
                existing_review.timestamp = datetime.utcnow()
            else:
                new_review = Review(
                    user_id=rating_input.user_id,
                    movie_id=rating_input.movie_id,
                    review_text=rating_input.review_text,
                    rating=rating_input.rating,
                    timestamp=datetime.utcnow()
                )
                db.add(new_review)
        
        # Log activity
        activity = UserActivity(
            user_id=rating_input.user_id,
            activity_type="rate",
            details={
                "movie_id": rating_input.movie_id,
                "rating": rating_input.rating,
                "review_text": rating_input.review_text[:50] if rating_input.review_text else None
            }
        )
        db.add(activity)
        
        db.commit()
        
        return {
            "message": "Rating recorded successfully",
            "user_id": rating_input.user_id,
            "movie_id": rating_input.movie_id,
            "rating": rating_input.rating,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watch")
async def watch_movie(
    watch_input: WatchInput, 
    db: Session = Depends(get_db)
):
    """User watches a movie - updates watch_history table"""
    try:
        user = db.query(User).filter(User.id == watch_input.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Add watch history entry
        new_watch = WatchHistory(
            user_id=watch_input.user_id,
            movie_id=watch_input.movie_id,
            watch_duration=watch_input.watch_duration,
            completed=watch_input.completed,
            timestamp=datetime.utcnow()
        )
        db.add(new_watch)
        
        # Log activity
        activity = UserActivity(
            user_id=watch_input.user_id,
            activity_type="watch",
            details={
                "movie_id": watch_input.movie_id,
                "duration": watch_input.watch_duration,
                "completed": watch_input.completed
            }
        )
        db.add(activity)
        
        # If completed, check if user already rated it
        if watch_input.completed:
            existing_rating = db.query(Rating).filter(
                Rating.user_id == watch_input.user_id,
                Rating.movie_id == watch_input.movie_id
            ).first()
            
            if not existing_rating:
                # Auto-rate based on watch duration (if watched full, assume they liked it)
                if watch_input.watch_duration > 1800:  # More than 30 minutes
                    auto_rating = Rating(
                        user_id=watch_input.user_id,
                        movie_id=watch_input.movie_id,
                        rating=4.0,
                        timestamp=datetime.utcnow()
                    )
                    db.add(auto_rating)
        
        db.commit()
        
        return {
            "message": "Watch recorded successfully",
            "user_id": watch_input.user_id,
            "movie_id": watch_input.movie_id,
            "watch_duration": watch_input.watch_duration,
            "completed": watch_input.completed,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/favourite")
async def add_favourite(fav_input: FavouriteInput, db: Session = Depends(get_db)):
    """User adds a movie to favorites"""
    try:
        user = db.query(User).filter(User.id == fav_input.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already in favorites
        existing = db.query(Favourite).filter(
            Favourite.user_id == fav_input.user_id,
            Favourite.movie_id == fav_input.movie_id
        ).first()
        
        if existing:
            return {
                "message": "Movie already in favorites",
                "user_id": fav_input.user_id,
                "movie_id": fav_input.movie_id,
                "status": "already_exists"
            }
        
        new_fav = Favourite(
            user_id=fav_input.user_id,
            movie_id=fav_input.movie_id,
            timestamp=datetime.utcnow()
        )
        db.add(new_fav)
        
        # Log activity
        activity = UserActivity(
            user_id=fav_input.user_id,
            activity_type="favourite",
            details={
                "movie_id": fav_input.movie_id,
                "action": "add"
            }
        )
        db.add(activity)
        
        db.commit()
        
        return {
            "message": "Movie added to favorites",
            "user_id": fav_input.user_id,
            "movie_id": fav_input.movie_id,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/favourite")
async def remove_favourite(fav_input: FavouriteInput, db: Session = Depends(get_db)):
    """User removes a movie from favorites"""
    try:
        fav = db.query(Favourite).filter(
            Favourite.user_id == fav_input.user_id,
            Favourite.movie_id == fav_input.movie_id
        ).first()
        
        if not fav:
            raise HTTPException(status_code=404, detail="Movie not in favorites")
        
        db.delete(fav)
        
        # Log activity
        activity = UserActivity(
            user_id=fav_input.user_id,
            activity_type="favourite",
            details={
                "movie_id": fav_input.movie_id,
                "action": "remove"
            }
        )
        db.add(activity)
        
        db.commit()
        
        return {
            "message": "Movie removed from favorites",
            "user_id": fav_input.user_id,
            "movie_id": fav_input.movie_id,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review")
async def add_review(review_input: ReviewInput, db: Session = Depends(get_db)):
    """User adds a review for a movie"""
    try:
        user = db.query(User).filter(User.id == review_input.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if review exists
        existing = db.query(Review).filter(
            Review.user_id == review_input.user_id,
            Review.movie_id == review_input.movie_id
        ).first()
        
        if existing:
            existing.review_text = review_input.review_text
            existing.rating = review_input.rating if review_input.rating else existing.rating
            existing.timestamp = datetime.utcnow()
        else:
            new_review = Review(
                user_id=review_input.user_id,
                movie_id=review_input.movie_id,
                review_text=review_input.review_text,
                rating=review_input.rating,
                timestamp=datetime.utcnow()
            )
            db.add(new_review)
        
        # If rating provided, also update rating table
        if review_input.rating:
            existing_rating = db.query(Rating).filter(
                Rating.user_id == review_input.user_id,
                Rating.movie_id == review_input.movie_id
            ).first()
            
            if existing_rating:
                existing_rating.rating = review_input.rating
                existing_rating.timestamp = datetime.utcnow()
            else:
                new_rating = Rating(
                    user_id=review_input.user_id,
                    movie_id=review_input.movie_id,
                    rating=review_input.rating,
                    timestamp=datetime.utcnow()
                )
                db.add(new_rating)
        
        # Log activity
        activity = UserActivity(
            user_id=review_input.user_id,
            activity_type="review",
            details={
                "movie_id": review_input.movie_id,
                "review_text": review_input.review_text[:50],
                "rating": review_input.rating
            }
        )
        db.add(activity)
        
        db.commit()
        
        return {
            "message": "Review added successfully",
            "user_id": review_input.user_id,
            "movie_id": review_input.movie_id,
            "review_text": review_input.review_text,
            "rating": review_input.rating,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ========== GET Endpoints (Retrieve User Data) ==========

@router.get("/{user_id}/ratings", response_model=List[RatingResponse])
async def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    """Get all ratings by a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        ratings = db.query(Rating).filter(
            Rating.user_id == user_id
        ).order_by(
            Rating.timestamp.desc()
        ).all()
        
        results = []
        for rating in ratings:
            movie = db.query(Movie).filter(Movie.id == rating.movie_id).first()
            # Get review if exists
            review = db.query(Review).filter(
                Review.user_id == user_id,
                Review.movie_id == rating.movie_id
            ).first()
            
            results.append(RatingResponse(
                movie_id=rating.movie_id,
                movie_title=movie.title if movie else "Unknown",
                rating=rating.rating,
                review_text=review.review_text if review else None,
                timestamp=rating.timestamp
            ))
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/watch-history", response_model=List[WatchHistoryResponse])
async def get_user_watch_history(user_id: int, db: Session = Depends(get_db)):
    """Get all watch history for a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        watch_history = db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id
        ).order_by(
            WatchHistory.timestamp.desc()
        ).all()
        
        results = []
        for watch in watch_history:
            movie = db.query(Movie).filter(Movie.id == watch.movie_id).first()
            results.append(WatchHistoryResponse(
                movie_id=watch.movie_id,
                movie_title=movie.title if movie else "Unknown",
                watch_duration=watch.watch_duration,
                completed=watch.completed,
                timestamp=watch.timestamp
            ))
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/favorites", response_model=List[FavouriteResponse])
async def get_user_favorites(user_id: int, db: Session = Depends(get_db)):
    """Get user's favorite movies"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        favorites = db.query(Favourite).filter(
            Favourite.user_id == user_id
        ).order_by(
            Favourite.timestamp.desc()
        ).all()
        
        results = []
        for fav in favorites:
            movie = db.query(Movie).filter(Movie.id == fav.movie_id).first()
            results.append(FavouriteResponse(
                movie_id=fav.movie_id,
                movie_title=movie.title if movie else "Unknown",
                added_at=fav.timestamp
            ))
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/reviews", response_model=List[ReviewResponse])
async def get_user_reviews(user_id: int, db: Session = Depends(get_db)):
    """Get all reviews by a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        reviews = db.query(Review).filter(
            Review.user_id == user_id
        ).order_by(
            Review.timestamp.desc()
        ).all()
        
        results = []
        for review in reviews:
            movie = db.query(Movie).filter(Movie.id == review.movie_id).first()
            results.append(ReviewResponse(
                movie_id=review.movie_id,
                movie_title=movie.title if movie else "Unknown",
                review_text=review.review_text,
                rating=review.rating,
                timestamp=review.timestamp
            ))
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/summary")
async def get_user_summary(user_id: int, db: Session = Depends(get_db)):
    """Get a summary of all user activities"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get counts
        rating_count = db.query(Rating).filter(Rating.user_id == user_id).count()
        watch_count = db.query(WatchHistory).filter(WatchHistory.user_id == user_id).count()
        favourite_count = db.query(Favourite).filter(Favourite.user_id == user_id).count()
        review_count = db.query(Review).filter(Review.user_id == user_id).count()
        
        # Get average rating
        avg_rating = db.query(db.func.avg(Rating.rating)).filter(
            Rating.user_id == user_id
        ).scalar()
        
        # Get recently watched
        recent_watches = db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id
        ).order_by(
            WatchHistory.timestamp.desc()
        ).limit(5).all()
        
        recent_movies = []
        for watch in recent_watches:
            movie = db.query(Movie).filter(Movie.id == watch.movie_id).first()
            recent_movies.append({
                "movie_id": watch.movie_id,
                "movie_title": movie.title if movie else "Unknown",
                "watched_at": watch.timestamp,
                "completed": watch.completed
            })
        
        return {
            "user_id": user_id,
            "username": user.username,
            "statistics": {
                "total_ratings": rating_count,
                "total_watches": watch_count,
                "total_favorites": favourite_count,
                "total_reviews": review_count,
                "average_rating": float(avg_rating) if avg_rating else None
            },
            "recent_activity": recent_movies,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))