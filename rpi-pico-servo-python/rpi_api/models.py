"""
SQLAlchemy modeli za bazu podataka
ServoMovement model za logovanje pozicija serva
Autor: AI Assistant
"""

from sqlalchemy import Column, Integer, Boolean, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

Base = declarative_base()

class ServoMovement(Base):
    """Model za praćenje pokreta serva"""
    
    __tablename__ = "servo_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    angle = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)  # Vreme odziva u milisekundama
    
    def __repr__(self):
        return f"<ServoMovement(id={self.id}, angle={self.angle}, success={self.success})>"

# Pydantic modeli za API
class ServoMovementCreate(BaseModel):
    """Pydantic model za kreiranje servo pokreta"""
    angle: int = Field(..., ge=0, le=180, description="Ugao serva u stepenima (0-180)")
    
class ServoMovementResponse(BaseModel):
    """Pydantic model za odgovor sa podacima o pokretu"""
    id: int
    angle: int
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None
    
    class Config:
        from_attributes = True

class ServoStatusResponse(BaseModel):
    """Pydantic model za status serva"""
    connected: bool
    last_command: Optional[datetime] = None
    total_movements: int
    error_rate: float
    
class ServoHistoryResponse(BaseModel):
    """Pydantic model za istoriju pokreta"""
    movements: list[ServoMovementResponse]
    total_count: int
