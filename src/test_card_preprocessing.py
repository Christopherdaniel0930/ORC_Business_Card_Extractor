from pathlib import Path

import cv2

from preprocessing import preprocess_card


PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_PATH = (
    PROJECT_ROOT
    / "data"
    / "images"
    / "image5.jpeg"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "debug"
    / "image5_card.jpg"
)


image = cv2.imread(str(IMAGE_PATH))

if image is None:
    raise FileNotFoundError(
        f"Could not load image: {IMAGE_PATH}"
    )


processed = preprocess_card(image)

print(
    f"Processed shape: {processed.shape}"
)

cv2.imwrite(
    str(OUTPUT_PATH),
    processed
)

print()
print("=" * 60)
print("CARD PREPROCESSING COMPLETE")
print("=" * 60)

print(f"Original size:    {image.shape[1]} x {image.shape[0]}")
print(f"Processed size:   {processed.shape[1]} x {processed.shape[0]}")
print(f"Saved to:         {OUTPUT_PATH}")