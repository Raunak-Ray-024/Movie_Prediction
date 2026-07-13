import csv
from datetime import datetime
from app.database import SessionLocal
from app.models.user import User
from app.models.rating import Rating
from app.models.movie import Movie

db = SessionLocal()

print("="*60)
print("📥 IMPORTING USERS & RATINGS")
print("="*60)

# ============================================
# 1️⃣ IMPORT USERS
# ============================================
print("\n👤 1. Importing users...")

user_ids = set()
with open('data/ratings.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print(f"   📋 Columns: {reader.fieldnames}")
    for row in reader:
        try:
            user_ids.add(int(row['user_id']))
        except:
            continue

print(f"   👥 Found {len(user_ids)} unique users")

user_count = 0
for user_id in sorted(user_ids):
    # Check if user already exists
    if db.query(User).filter_by(user_id=user_id).first():
        continue
    
    user = User(
        user_id=user_id,
        username=f"user_{user_id}",
        email=f"user_{user_id}@example.com",
        password_hash="placeholder",
        created_at=datetime.now()
    )
    db.add(user)
    user_count += 1
    
    if user_count % 100 == 0:
        db.commit()
        print(f"   ✅ {user_count} users created...")

db.commit()
print(f"   ✅ Total users created: {user_count}")

# ============================================
# 2️⃣ IMPORT RATINGS
# ============================================
print("\n⭐ 2. Importing ratings...")

rating_count = 0
skipped = 0

with open('data/ratings.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            user_id = int(row['user_id'])
            movie_id = int(row['movie_id'])
            rating_val = float(row['rating'])
            timestamp = datetime.fromtimestamp(int(row['timestamp']))
            
            # Check if user exists
            if not db.query(User).filter_by(user_id=user_id).first():
                skipped += 1
                continue
            
            # Check if movie exists
            if not db.query(Movie).filter_by(movie_id=movie_id).first():
                skipped += 1
                continue
            
            # Check if rating already exists
            existing = db.query(Rating).filter_by(
                user_id=user_id,
                movie_id=movie_id
            ).first()
            
            if existing:
                existing.rating = rating_val
                existing.rated_at = timestamp
            else:
                rating = Rating(
                    user_id=user_id,
                    movie_id=movie_id,
                    rating=rating_val,
                    rated_at=timestamp
                )
                db.add(rating)
            
            rating_count += 1
            
            if rating_count % 10000 == 0:
                db.commit()
                print(f"   ✅ {rating_count} ratings imported...")
                
        except Exception as e:
            skipped += 1
            continue

db.commit()
print(f"   ✅ Total ratings imported: {rating_count}")
print(f"   ⚠️ Skipped: {skipped}")

# ============================================
# ✅ FINAL SUMMARY
# ============================================
print("\n" + "="*60)
print("✅ IMPORT COMPLETE!")
print("="*60)

from app.models.movie import Movie
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre

print(f"\n📊 FINAL SUMMARY:")
print(f"   Movies:  {db.query(Movie).count():,}")
print(f"   Users:   {db.query(User).count():,}")
print(f"   Ratings: {db.query(Rating).count():,}")
print(f"   Genres:  {db.query(Genre).count()}")
print(f"   Movie-Genre: {db.query(MovieGenre).count():,}")
print("\n" + "="*60)

db.close()