"""Application entry point for business-card OCR."""

import os

from camera_capture import capture_business_card


def main() -> None:
    """Capture one card using the camera and run it through OCR."""
    try:
        image_path = capture_business_card()
    except RuntimeError as error:
        print(error)
        return

    os.environ["BUSINESS_CARD_IMAGE"] = str(image_path)

    # The OCR module runs the pipeline for the selected image on import.
    import ocr  # noqa: F401


if __name__ == "__main__":
    main()
