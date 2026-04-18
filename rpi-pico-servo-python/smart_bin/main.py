"""
Smart Bin FastAPI sub-application.
Endpoints: /classify, /classify/auto, /capture, /labels
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException

from .camera import take_photo, cleanup_camera
from .classifier.base import IClassifier, Prediction
from .classifier.mock_classifier import MockClassifier
from .config import smart_bin_settings
from .dataset import (
    decode_b64_image,
    estimate_light_level,
    read_labels_csv,
    save_image,
    save_to_dataset,
    update_user_label,
)
from .schemas import (
    AutoClassifyRequest,
    CaptureRequest,
    CaptureResponse,
    ClassifyResponse,
    LabelEntry,
    LabelsResponse,
    UpdateLabelRequest,
)

logger = logging.getLogger(__name__)


def _create_classifier() -> IClassifier:
    """Create classifier based on available model files."""
    model_path = smart_bin_settings.model_path
    labels_path = smart_bin_settings.labels_path

    # Try TFLite if model file exists
    if os.path.exists(model_path) and os.path.exists(labels_path):
        try:
            from .classifier.tflite_classifier import TFLiteClassifier

            clf = TFLiteClassifier(
                model_path=model_path,
                labels_path=labels_path,
                waste_angles=smart_bin_settings.waste_angles,
            )
            clf.load_model()
            logger.info("TFLite classifier loaded successfully")
            return clf
        except (ImportError, FileNotFoundError, Exception) as e:
            logger.warning(f"Failed to load TFLite classifier: {e}, falling back to mock")

    # Fall back to mock
    angles = {k: v.get("horizontal", 0) for k, v in smart_bin_settings.waste_angles.items()}
    clf = MockClassifier(angles=angles)
    clf.load_model()
    logger.info("Mock classifier loaded (no TFLite model found)")
    return clf


# Classifier instance (initialized at module level for mounted sub-app)
_classifier: IClassifier = _create_classifier()

# Ensure directories exist
os.makedirs(smart_bin_settings.images_dir, exist_ok=True)
os.makedirs(os.path.join(smart_bin_settings.dataset_dir, "images"), exist_ok=True)


def _get_angle_for_type(waste_type: str) -> int:
    """Get servo angle for waste type from config."""
    return smart_bin_settings.waste_angles.get(waste_type, {}).get("horizontal", 0)


async def _servo_return_to_base():
    """Return servo to base position after delay."""
    await asyncio.sleep(smart_bin_settings.servo_return_delay)
    try:
        from rpi_api.servo_service import servo_controller

        success, error_msg, _ = servo_controller.return_to_base()
        if success:
            logger.info("Servo returned to base (0,0)")
        else:
            logger.warning(f"Servo return to base failed: {error_msg}")
    except ImportError:
        logger.warning("servo_controller not available - skip return to base")
    except Exception as e:
        logger.error(f"Servo return error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Smart Bin lifecycle manager."""
    logger.info("Smart Bin module ready (classifier: %s)", type(_classifier).__name__)
    yield
    logger.info("Shutting down Smart Bin")
    cleanup_camera()


# Create sub-app
smart_bin_app = FastAPI(
    title="Smart Bin Classification API",
    version="0.1.0",
    description="Waste classification and dataset collection for smart bin",
    lifespan=lifespan,
)


@smart_bin_app.post("/classify", response_model=ClassifyResponse)
async def classify(background_tasks: BackgroundTasks):
    """
    Take photo, classify waste, trigger servo, return result.
    Auto-returns servo to base after delay.
    """
    if _classifier is None:
        raise HTTPException(status_code=503, detail="Classifier not initialized")

    # 1. Capture photo
    image = take_photo()

    # 2. Classify
    prediction: Prediction = _classifier.predict(image)

    # 3. Save classified image
    img_path = save_image(image, smart_bin_settings.images_dir, prefix="classify")

    # 4. Estimate light level
    light_level = estimate_light_level(image)

    # 5. Trigger servo internally
    servo_success = False
    try:
        from rpi_api.servo_service import servo_controller

        success, error_msg, _ = servo_controller.set_material_position(prediction.waste_type)
        servo_success = success
        if not success:
            logger.warning(f"Servo move failed: {error_msg}")

        # Schedule return to base
        background_tasks.add_task(_servo_return_to_base)
    except ImportError:
        logger.warning("servo_controller not available - skip servo action")
    except Exception as e:
        logger.error(f"Servo error: {e}")

    return ClassifyResponse(
        waste_type=prediction.waste_type,
        confidence=prediction.confidence,
        angle=prediction.angle,
        servo_success=servo_success,
        image_path=img_path,
        light_level=light_level,
        all_scores=prediction.all_scores,
    )


@smart_bin_app.post("/classify/auto", response_model=ClassifyResponse)
async def classify_auto(
    request: AutoClassifyRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger classification only if object detected within distance threshold.
    Input: sensor distance in cm.
    """
    if request.distance_cm >= smart_bin_settings.sensor_distance_cm:
        raise HTTPException(
            status_code=200,
            detail=f"Object too far ({request.distance_cm}cm >= {smart_bin_settings.sensor_distance_cm}cm threshold). Classification skipped.",
        )

    # Same pipeline as /classify
    return await classify(background_tasks)


@smart_bin_app.post("/capture", response_model=CaptureResponse)
async def capture(request: CaptureRequest):
    """
    Save image to dataset with prediction metadata.
    Used for building labeled dataset for model improvement.
    """
    try:
        image = decode_b64_image(request.image_b64)
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    angle = _get_angle_for_type(request.predicted)
    img_path, row_id, light_level = save_to_dataset(
        image=image,
        predicted_class=request.predicted,
        confidence=request.confidence,
        angle=angle,
    )

    return CaptureResponse(
        image_path=img_path,
        csv_row=row_id,
        light_level=light_level,
    )


@smart_bin_app.get("/labels", response_model=LabelsResponse)
async def get_labels():
    """List all entries from labels.csv for web labeling UI."""
    entries = read_labels_csv()

    labels = []
    for e in entries:
        labels.append(LabelEntry(
            row_id=e.get("row_id", 0),
            img_path=e.get("img_path", ""),
            predicted_class=e.get("predicted_class", ""),
            user_label=e.get("user_label", ""),
            confidence=float(e.get("confidence", 0)),
            timestamp=e.get("timestamp", ""),
            angle=int(e.get("angle", 0)),
            light_level=float(e.get("light_level", 0)),
        ))

    return LabelsResponse(labels=labels, total_count=len(labels))


@smart_bin_app.patch("/labels/{row_id}")
async def update_label(row_id: int, request: UpdateLabelRequest):
    """Update user_label (ground truth) for a dataset entry."""
    success = update_user_label(row_id, request.user_label)
    if not success:
        raise HTTPException(status_code=404, detail=f"Row {row_id} not found in labels.csv")
    return {"row_id": row_id, "user_label": request.user_label, "updated": True}


@smart_bin_app.get("/status")
async def smart_bin_status():
    """Smart Bin module status."""
    return {
        "classifier": type(_classifier).__name__ if _classifier else "none",
        "classifier_loaded": _classifier.is_loaded if _classifier else False,
        "camera_mock": smart_bin_settings.camera_mock or not _picamera2_available(),
        "model_path": smart_bin_settings.model_path,
        "model_exists": os.path.exists(smart_bin_settings.model_path),
        "confidence_threshold": smart_bin_settings.confidence_threshold,
        "servo_return_delay": smart_bin_settings.servo_return_delay,
    }


def _picamera2_available() -> bool:
    """Check if picamera2 is importable."""
    try:
        from picamera2 import Picamera2  # noqa: F401
        return True
    except ImportError:
        return False
