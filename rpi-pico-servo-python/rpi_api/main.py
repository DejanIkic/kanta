"""
FastAPI glavna aplikacija za servo kontrolu
Autor: AI Assistant
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Literal
import time

import structlog
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .config import settings
from .database import check_db_health, get_db, init_db
from .models import (
    ServoHistoryResponse,
    ServoMovement,
    ServoMovementCreate,
    ServoMovementResponse,
    ServoStatusResponse,
)
from .servo_service import servo_controller

# Strukturirani logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager za aplikaciju"""
    # Startup
    logger.info("Starting RPi Pico Servo Control API")

    try:
        # Reset Pico da oistimo bafer
        logger.info("Resetting Pico to clear buffer...")
        servo_controller.disconnect()  # Prekini konekciju ako postoji
        time.sleep(1)  # Pauza za reset
        
        # Inicijalizacija baze
        init_db()
        logger.info("Database initialized")

        # Test konekcije sa Pico-om (automatski cisti bafer)
        connected, _, attempts = servo_controller.get_status()
        if connected:
            logger.info("Successfully connected to Pico, buffer cleared")
        else:
            logger.warning("Failed to connect to Pico", attempts=attempts)

        yield

    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application")
        servo_controller.cleanup()


# Kreiranje FastAPI aplikacije
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # U production postaviti konkretne domene
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint sa osnovnim informacijama"""
    return {
        "message": "RPi Pico Servo Control API",
        "version": settings.api_version,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    db_healthy = check_db_health()
    pico_connected, _, _ = servo_controller.get_status()
    status = "healthy" if db_healthy and pico_connected else "unhealthy"
    return {
        "status": status,
        "database": "healthy" if db_healthy else "unhealthy",
        "pico_connected": pico_connected,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/servo/{side}", response_model=ServoMovementResponse)
async def set_servo_side(
    side: Literal["left", "right"],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Postavi servo na levu ili desnu stranu
    :param side: "left" ili "right"
    :param background_tasks: FastAPI background tasks
    :param db: Database session
    :return: Informacije o izvršenoj komandi
    """
    angle = -20 if side == "left" else 20
    logger.info("Setting servo side", side=side, angle=angle)

    success, error_message, response_time = servo_controller.set_angle(angle)

    servo_movement = ServoMovement(
        angle=angle,
        command_type="legacy",  # Backward compatibility
        success=success,
        error_message=error_message,
        response_time_ms=response_time,
    )

    db.add(servo_movement)
    db.commit()
    db.refresh(servo_movement)

    background_tasks.add_task(
        log_servo_movement, angle=angle, side=side, success=success, response_time=response_time
    )

    if not success:
        raise HTTPException(
            status_code=500, detail=f"Failed to set servo side: {error_message}"
        )

    logger.info(
        "Servo side set successfully",
        side=side,
        angle=angle,
        movement_id=servo_movement.id,
        response_time_ms=response_time,
    )

    return servo_movement


@app.post("/api/servo/material/{material_type}", response_model=ServoMovementResponse)
async def set_servo_material(
    material_type: Literal["plastic", "glass", "pet", "organic"],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Postavi servoe za zadati materijal sa kompletnom sekvencom pokreta
    :param material_type: Tip materijala (plastic, glass, pet, organic)
    :param background_tasks: FastAPI background tasks
    :param db: Database session
    :return: Informacije o izvrðenoj komandi
    """
    logger.info("Setting servo material position", material=material_type)

    success, error_message, response_time, positions = servo_controller.set_material_position(material_type)

    # Kreiraj zapis sa informacijama o oba serva
    servo_movement = ServoMovement(
        angle=positions["horizontal"] if positions else 0,  # Legacy field - horizontal angle
        vertical_angle=positions["vertical"] if positions else None,
        horizontal_angle=positions["horizontal"] if positions else None,
        material_type=material_type,
        command_type="material",
        success=success,
        error_message=error_message,
        response_time_ms=response_time,
    )

    db.add(servo_movement)
    db.commit()
    db.refresh(servo_movement)

    background_tasks.add_task(
        log_material_movement, 
        material=material_type, 
        positions=positions, 
        success=success, 
        response_time=response_time
    )

    if not success:
        raise HTTPException(
            status_code=500, detail=f"Failed to set material position: {error_message}"
        )

    logger.info(
        "Material position set successfully",
        material=material_type,
        positions=positions,
        movement_id=servo_movement.id,
        response_time_ms=response_time,
    )

    return servo_movement


@app.get("/api/servo/status", response_model=ServoStatusResponse)
async def get_servo_status(db: Session = Depends(get_db)):
    """
    Vraća status serva i konekcije
    :param db: Database session
    :return: Status informacije
    """
    connected, last_command, attempts = servo_controller.get_status()

    # Statistika iz baze
    total_movements = db.query(ServoMovement).count()
    error_count = db.query(ServoMovement).filter(ServoMovement.success == False).count()
    error_rate = (error_count / total_movements * 100) if total_movements > 0 else 0.0

    return ServoStatusResponse(
        connected=connected,
        last_command=last_command,
        total_movements=total_movements,
        error_rate=round(error_rate, 2),
    )


@app.get("/api/servo/history", response_model=ServoHistoryResponse)
async def get_servo_history(db: Session = Depends(get_db)):
    """
    Vraća istoriju zadnjih 100 pokreta serva
    :param db: Database session
    :return: Lista pokreta
    """
    movements = (
        db.query(ServoMovement).order_by(desc(ServoMovement.timestamp)).limit(100).all()
    )

    total_count = db.query(ServoMovement).count()

    return ServoHistoryResponse(movements=movements, total_count=total_count)


@app.get("/api/servo/history/{limit:int}", response_model=ServoHistoryResponse)
async def get_servo_history_limit(limit: int, db: Session = Depends(get_db)):
    """
    Vraća istoriju pokreta sa zadatim limitom
    :param limit: Maksimalan broj zapisa (1-1000)
    :param db: Database session
    :return: Lista pokreta
    """
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

    movements = (
        db.query(ServoMovement)
        .order_by(desc(ServoMovement.timestamp))
        .limit(limit)
        .all()
    )

    total_count = db.query(ServoMovement).count()

    return ServoHistoryResponse(movements=movements, total_count=total_count)


async def log_servo_movement(angle:int, side: str, success: bool, response_time: int):
    """Background task za logovanje servo pokreta"""
    if success:
        logger.info(
            "Servo movement completed",angle=angle, side=side, response_time_ms=response_time
        )
    else:
        logger.error("Servo movement failed", angle=angle, side=side)


async def log_material_movement(material: str, positions: dict, success: bool, response_time: int):
    """Background task za logovanje materijal pokreta"""
    if success:
        logger.info(
            "Material movement completed",
            material=material,
            vertical_angle=positions["vertical"],
            horizontal_angle=positions["horizontal"],
            response_time_ms=response_time
        )
    else:
        logger.error("Material movement failed", material=material)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Za development
        log_level=settings.log_level.lower(),
    )
