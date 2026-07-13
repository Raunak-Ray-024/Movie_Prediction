from app.database import Base, engine
from fastapi import FastAPI
from app.models.user import User
from app.models.movie import Movie
from app.models.rating import Rating
from app.models.favourite import Favourite
from app.models.review import Review
from app.models.watch_history import WatchHistory
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.models.user import Base
from app.router import recommendations
from app.router import user_interaction
from app.database import get_db
from app.ml_module.recommender import recommender
from app.models.user_activity import UserLogin, UserActivity, UserSession 
from app.router import recommendations, user_interaction, auth
app = FastAPI(
    title="Movie Recommendation API",
    docs_url="/docs", 
    redoc_url="/redoc" 
)

Base.metadata.create_all(bind=engine)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommendations.router)
app.include_router(user_interaction.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {
        "message": "Movie Recommendation API",
        "docs": "/docs",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )