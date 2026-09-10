import os

os.environ["FLAGS_use_mkldnn"] = "0"

from pathlib import Path

import cv2
from paddleocr import PaddleOCR

from preprocessing import preprocess_card
from ocr_utils import create_ocr_items
from text_reconstruction import reconstruct_text


PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_PATH = (
    PROJECT_ROOT
    / "data"
    / "images"
    / "image4.jpeg"
)


# --------------------------------------------------
# LOAD IMAGE
# --------------------------------------------------

image = cv2.imread(str(IMAGE_PATH))

if image is None:
    raise FileNotFoundError(
        f"Could not load image: {IMAGE_PATH}"
    )


# --------------------------------------------------
# PREPROCESS
# --------------------------------------------------

processed = preprocess_card(image)


# --------------------------------------------------
# OCR
# --------------------------------------------------

ocr = PaddleOCR(
    lang="ar",
    enable_mkldnn=False
)

result = ocr.predict(processed)


# --------------------------------------------------
# CREATE OCR ITEMS
# --------------------------------------------------

for res in result:

    if not res:
        continue

    texts = res["rec_texts"]
    scores = res["rec_scores"]
    boxes = res["rec_polys"]

    ocr_items = create_ocr_items(
        texts,
        scores,
        boxes
    )

    break
else:
    ocr_items = []


# --------------------------------------------------
# RECONSTRUCT TEXT
# --------------------------------------------------

reconstructed_text = reconstruct_text(
    ocr_items,
    y_tolerance=15
)


print()
print("=" * 60)
print("RECONSTRUCTED OCR TEXT")
print("=" * 60)

print(reconstructed_text)

print()
print("=" * 60)
print("OCR ITEM COUNT")
print("=" * 60)

print(len(ocr_items))