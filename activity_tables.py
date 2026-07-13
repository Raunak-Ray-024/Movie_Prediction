from app.database import engine
from app.models.user_activity import Base

def create_activity_tables():
    print("Creating activity tables...")
    Base.metadata.create_all(bind=engine)
    print("Activity tables created successfully!")

if __name__ == "__main__":
    create_activity_tables()