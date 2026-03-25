"""
Konfiguracija aplikacije i environment varijable
Autor: AI Assistant
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Postavke aplikacije"""
    
    # Database postavke
    database_url: str = "postgresql://postgres:password@localhost:5432/servo_db"
    
    # Serial port postavke
    serial_port: str = "/dev/ttyACM0"
    serial_baudrate: int = 115200
    serial_timeout: float = 1.0
    
    # API postavke
    api_title: str = "RPi Pico Servo Control API"
    api_version: str = "1.0.0"
    api_description: str = "API za kontrolu SG90 servo motora preko Raspberry Pi Pico"
    
    # Logging postavke
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Servo postavke
    servo_min_angle: int = 0
    servo_max_angle: int = 180
    servo_move_timeout: float = 2.0  # sekunde
    
    # Health check postavke
    health_check_interval: float = 30.0  # sekunde
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
