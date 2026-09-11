"""Camera capture support for the business-card OCR application."""

from datetime import datetime
from pathlib import Path

import cv2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "images"


def capture_business_card(camera_index=0):
    """Capture a card image with Space; press Esc or Q to cancel."""
    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        raise RuntimeError("Could not open the camera. Check its connection and permissions.")

    window_name = "Business Card Capture"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    try:
        while True:
            success, frame = camera.read()

            if not success:
                raise RuntimeError("Could not read an image from the camera.")

            preview = frame.copy()
            cv2.putText(
                preview,
                "Press SPACE to capture | ESC or Q to cancel",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(window_name, preview)

            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):
                IMAGE_DIR.mkdir(parents=True, exist_ok=True)
                filename = datetime.now().strftime("camera_capture_%Y%m%d_%H%M%S_%f.jpg")
                image_path = IMAGE_DIR / filename

                if not cv2.imwrite(str(image_path), frame):
                    raise RuntimeError(f"Could not save the captured image to {image_path}.")

                return image_path

            if key in (27, ord("q"), ord("Q")):
                raise RuntimeError("Camera capture cancelled.")
    finally:
        camera.release()
        cv2.destroyWindow(window_name)
