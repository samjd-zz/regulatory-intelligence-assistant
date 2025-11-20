"""
Database configuration and session management for PostgreSQL.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/regulatory_db")

# Create SQLAlchemy engine
# Using NullPool for better connection management in async environments
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=os.getenv("DEBUG", "False").lower() == "true",  # Log SQL queries in debug mode
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency function to get database session.
    Use this in FastAPI route dependencies.
    
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables.
    This should be called on application startup.
    """
    from backend.models import models  # Import all models
    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    """
    Drop and recreate all tables.
    USE WITH CAUTION - This will delete all data!
    Only for development/testing.
    """
    from backend.models import models  # Import all models
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
