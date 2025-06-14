# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    This function is a FastAPI dependency. It creates a database session per request,
    ensuring the session is closed correctly after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()