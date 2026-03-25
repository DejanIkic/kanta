"""
Database konekcija i SQLAlchemy setup
Autor: AI Assistant
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings
import structlog

logger = structlog.get_logger()

# Database engine
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,  # Za SQLite
    } if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()

def get_db():
    """
    Dependency za database session
    Yield-a session i zatvara je nakon upotrebe
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Inicijalizacija baze podataka
    Kreira tabele ako ne postoje
    """
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise

def check_db_health():
    """
    Proverava da li je baza dostupna
    :return: True ako je baza dostupna, False inače
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False
