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
    database_url: str = "sqlite:///./servo_db.sqlite3"
    
    # Serial port postavke
    serial_port: str = "/dev/ttyACM10"
    serial_baudrate: int = 115200
    serial_timeout: float = 10.0
    
    # API postavke
    api_title: str = "RPi Pico Servo Control API"
    api_version: str = "1.0.0"
    api_description: str = "API za kontrolu SG90 servo motora preko Raspberry Pi Pico"
    
    # Logging postavke
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Servo postavke
    servo_orientation: str = "horizontal"  # vertical or horizontal
    servo_move_timeout: float = 2.0  # sekunde
    
    # Health check postavke
    health_check_interval: float = 30.0  # sekunde
    
    @property
    def servo_min_angle(self) -> int:
        """Minimum servo angle based on orientation"""
        if self.servo_orientation.lower() == "vertical":
            return 30  # 90 - 60
        else:  # horizontal
            return 54  # 90 - 36
    
    @property
    def servo_max_angle(self) -> int:
        """Maximum servo angle based on orientation"""
        if self.servo_orientation.lower() == "vertical":
            return 150  # 90 + 60
        else:  # horizontal
            return 126  # 90 + 36
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

# Global settings instance
settings = Settings()
