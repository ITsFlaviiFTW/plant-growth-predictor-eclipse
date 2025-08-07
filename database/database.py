# database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# Declare the base class for models
Base = declarative_base()

# DB connection statement
DATABASE_URL = "postgresql://plant_user:plantUser!23@192.168.137.2:5432/plant_monitoring"

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
