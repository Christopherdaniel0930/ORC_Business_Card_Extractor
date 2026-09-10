import os

os.environ["FLAGS_use_mkldnn"] = "0"

from pathlib import Path

import cv2
from paddleocr import PaddleOCR

from preprocessing import preprocess_card


PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_PATH = (
    PROJECT_ROOT
    / "data"
    / "images"
    / "image4.jpeg"
)


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


print()
print("=" * 60)
print("PREPROCESSED CARD OCR")
print("=" * 60)


for res in result:

    if not res:
        continue

    texts = res["rec_texts"]
    scores = res["rec_scores"]

    for text, score in zip(texts, scores):

        print(
            f"{text:<40} confidence={score:.3f}"
        )