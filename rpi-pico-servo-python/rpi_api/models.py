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
from typing import List, Optional

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
    angle: int
    
    @classmethod
    def __get_validators__(cls):
        # Get dynamic limits from settings
        from .config import settings
        min_angle = settings.servo_min_angle
        max_angle = settings.servo_max_angle
        
        # Validate angle is within dynamic range
        def validate_angle(value):
            if not (min_angle <= value <= max_angle):
                raise ValueError(f'Angle must be between {min_angle} and {max_angle}')
            return int(value)
        
        yield validate_angle
    
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
