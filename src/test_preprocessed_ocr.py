import os
os.environ["FLAGS_use_mkldnn"] = "0"

from pathlib import Path
import cv2

from paddleocr import PaddleOCR
from preprocessing import preprocess_image


PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_PATH = PROJECT_ROOT / "data" / "images" / "image4.jpeg"


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

processed = preprocess_image(image)


# --------------------------------------------------
# OCR MODEL
# --------------------------------------------------

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)


# --------------------------------------------------
# ORIGINAL OCR
# --------------------------------------------------

print("\n" + "=" * 60)
print("ORIGINAL IMAGE OCR")
print("=" * 60)

original_result = ocr.predict(
    str(IMAGE_PATH)
)

for res in original_result:

    if not res:
        continue

    data = res

    texts = data["rec_texts"]
    scores = data["rec_scores"]

    for text, score in zip(texts, scores):

        print(
            f"{text:<35} confidence={score:.3f}"
        )


# --------------------------------------------------
# PREPROCESSED OCR
# --------------------------------------------------

print("\n" + "=" * 60)
print("PREPROCESSED IMAGE OCR")
print("=" * 60)


preprocessed_result = ocr.predict(
    processed
)

for res in preprocessed_result:

    if not res:
        continue

    data = res

    texts = data["rec_texts"]
    scores = data["rec_scores"]

    for text, score in zip(texts, scores):

        print(
            f"{text:<35} confidence={score:.3f}"
        )