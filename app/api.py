"""FastAPI application for business card image extraction."""

from io import BytesIO
import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError

from app.common.config import get_settings
from app.common.document_pipeline import process_document

logger = logging.getLogger(__name__)
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_PIXELS = 40_000_000

app = FastAPI(title="Business Card Extractor API", version="1.0.0")


def _validate_image(contents: bytes) -> str:
    """Validate an uploaded image and return its detected format."""
    try:
        with Image.open(BytesIO(contents)) as image:
            image.verify()
        with Image.open(BytesIO(contents)) as image:
            image_format = image.format
            if image_format not in ALLOWED_FORMATS:
                raise HTTPException(
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    "Upload a JPEG, PNG, or WEBP image.",
                )
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    "Image dimensions are too large to process.",
                )
            return image_format
    except HTTPException:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "The uploaded image is corrupted or invalid.",
        ) from exc


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/documents", tags=["business cards"])
async def submit_document(file: UploadFile = File(...)):
    """Extract business card fields from an image and return the completed result."""
    settings = get_settings()
    contents = await file.read(settings.max_upload_bytes + 1)
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "Image must be 10 MB or smaller.",
        )

    image_format = _validate_image(contents)
    suffix = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}[image_format]
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="business-card-", suffix=suffix, delete=False
        ) as image_file:
            image_file.write(contents)
            temp_path = image_file.name

        result = await run_in_threadpool(process_document, temp_path)
        data = result.get("data")
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        return {
            "document_type": result.get("document_type", "business_card"),
            "result": data,
        }
    except RuntimeError as exc:
        logger.warning("Business card extraction failed: %s", exc)
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No text could be extracted from the image.",
        ) from exc
    except Exception as exc:
        logger.exception("Business card extraction failed (%s)", type(exc).__name__)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "The image could not be processed as a business card.",
        ) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
