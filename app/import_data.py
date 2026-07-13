import csv
import re
import ast
from datetime import datetime
from app.database import SessionLocal, engine, Base
from app.models.movie import Movie
from app.models.user import User
from app.models.rating import Rating
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre

def clean_id(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        digits = re.sub(r'[^0-9]', '', value)
        if digits:
            return int(digits)
    return None

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%d-%m-%y')
    except:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None

def extract_genres(genres_str):
    if not genres_str or genres_str == '[]':
        return []
    try:
        data = ast.literal_eval(genres_str)
        return [g['name'] for g in data if 'name' in g]
    except:
        return []

# Create tables
print("📋 Creating tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables ready\n")

db = SessionLocal()

try:
        # ============================================
    # 1️⃣ IMPORT MOVIES
    # ============================================
    print("🎬 1. Importing movies...")
    movie_count = 0
    skipped_count = 0

    with open('data/moviemetadata.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f"   📋 Columns: {reader.fieldnames}")
        
        for row in reader:
            movie_id = clean_id(row.get('movie_id'))
            if not movie_id:
                skipped_count += 1
                continue
            
            # Check if movie already exists
            existing = db.query(Movie).filter_by(movie_id=movie_id).first()
            if existing:
                skipped_count += 1
                continue
            
            # ✅ FIX: imdb_id ko None karo agar invalid hai
            imdb_id_val = row.get('imdb_id', '').strip()
            if not imdb_id_val or imdb_id_val == '0' or imdb_id_val.lower() in ['null', 'none', '']:
                imdb_id_val = None
            else:
                imdb_id_val = imdb_id_val[:20]
            
            movie = Movie(
                movie_id=movie_id,
                title=row.get('title', 'Unknown')[:255],
                genres=row.get('genres', '')[:1000],
                overview=row.get('overview', '')[:1000],
                imdb_id=imdb_id_val,  # ✅ FIXED
                poster_path=row.get('poster_path', ''),
                release_date=parse_date(row.get('release_date')),
                runtime=int(row['runtime']) if row.get('runtime', '').isdigit() else None,
                vote_count=int(row['vote_count']) if row.get('vote_count', '').isdigit() else None,
                popularity=float(row['popularity']) if row.get('popularity') else None
            )
            db.add(movie)
            movie_count += 1
            
            if movie_count % 1000 == 0:
                db.commit()
                print(f"   ✅ {movie_count} movies imported...")

    db.commit()
    print(f"   ✅ Total movies: {movie_count}")
    print(f"   ⚠️ Skipped: {skipped_count}\n")

    # ============================================
    # 2️⃣ IMPORT GENRES
    # ============================================
    print("🏷️ 2. Importing genres...")
    
    all_genres = set()
    movie_genres_map = {}

    with open('data/moviemetadata.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie_id = clean_id(row.get('movie_id'))
            if not movie_id:
                continue
            genres = extract_genres(row.get('genres'))
            if genres:
                movie_genres_map[movie_id] = genres
                all_genres.update(genres)

    genre_map = {}
    for genre_name in sorted(all_genres):
        existing = db.query(Genre).filter_by(genre_name=genre_name).first()
        if existing:
            genre_map[genre_name] = existing.genre_id
        else:
            genre = Genre(genre_name=genre_name)
            db.add(genre)
            db.flush()
            genre_map[genre_name] = genre.genre_id

    db.commit()
    print(f"   ✅ Total genres: {len(genre_map)}\n")

    # ============================================
    # 3️⃣ MOVIE-GENRE RELATIONSHIPS
    # ============================================
    print("🔗 3. Creating movie-genre relationships...")
    
    relation_count = 0
    for movie_id, genres in movie_genres_map.items():
        for genre_name in genres:
            if genre_name in genre_map:
                existing = db.query(MovieGenre).filter_by(
                    movie_id=movie_id,
                    genre_id=genre_map[genre_name]
                ).first()
                if not existing:
                    mg = MovieGenre(movie_id=movie_id, genre_id=genre_map[genre_name])
                    db.add(mg)
                    relation_count += 1
        if relation_count % 5000 == 0:
            db.commit()
            print(f"   ✅ {relation_count} relationships created...")

    db.commit()
    print(f"   ✅ Total relationships: {relation_count}\n")


    # ============================================
    # ✅ FINAL SUMMARY
    # ============================================
    print("="*60)
    print("✅ ALL DATA IMPORT COMPLETE!")
    print("="*60)
    
    movie_count = db.query(Movie).count()
    genre_count = db.query(Genre).count()
    movie_genre_count = db.query(MovieGenre).count()
    
    print(f"\n📊 FINAL SUMMARY:")
    print(f"   Movies:  {movie_count:,}")
    print(f"   Genres:  {genre_count}")
    print(f"   Movie-Genre: {movie_genre_count:,}")
    print("\n" + "="*60)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()