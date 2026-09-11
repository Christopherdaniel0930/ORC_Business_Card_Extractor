import os

os.environ["FLAGS_use_mkldnn"] = "0"

import json
import cv2
from pathlib import Path

from paddleocr import PaddleOCR

from ocr_utils import create_ocr_items
from field_extraction import extract_fields
from visualize import draw_ocr_boxes
from gliner_extractor import GLiNERExtractor
from field_resolver import resolve_fields
from text_reconstruction import reconstruct_text
from preprocessing import preprocess_card


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_DIR = PROJECT_ROOT / "data" / "images"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEBUG_DIR = PROJECT_ROOT / "data" / "debug"

# Create directories
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DEBUG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INITIALIZE OCR
# ============================================================

print("Loading PaddleOCR...")

ocr = PaddleOCR(
    lang="ar",
    enable_mkldnn=False
)

print("PaddleOCR loaded.")

gliner = GLiNERExtractor()

# ============================================================
# FIND IMAGES
# ============================================================

image_extensions = [
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.bmp",
    "*.webp"
]

image_paths = []

selected_image = os.environ.get("BUSINESS_CARD_IMAGE")

if selected_image:

    selected_path = Path(selected_image)

    if not selected_path.is_file():
        raise FileNotFoundError(
            f"Selected image does not exist: {selected_path}"
        )

    image_paths.append(selected_path)

else:

    for extension in image_extensions:

        image_paths.extend(
            IMAGE_DIR.glob(extension)
        )


# Sort images
image_paths.sort()


print(
    f"\nFound {len(image_paths)} images."
)


# ============================================================
# PROCESS IMAGES
# ============================================================

for image_path in image_paths:

    print("\n" + "=" * 60)

    print(
        f"Processing: {image_path.name}"
    )

    print("=" * 60)


    try:

        image = cv2.imread(str(image_path))

        if image is None:
            raise FileNotFoundError(
                f"Could not load image: {image_path}"
            )


# ----------------------------------------------------
# PREPROCESS BUSINESS CARD
# ----------------------------------------------------

        processed_image = preprocess_card(image)


# ----------------------------------------------------
# OCR
# ----------------------------------------------------

        result = ocr.predict(
            processed_image
        )


        for res in result:

            texts = res["rec_texts"]

            scores = res["rec_scores"]

            boxes = res["rec_polys"]


            # ------------------------------------------------
            # Create clean OCR items
            # ------------------------------------------------

            ocr_items = create_ocr_items(
                texts,
                scores,
                boxes
            )

            # ------------------------------------------------
            # Reconstruct OCR text
            # ------------------------------------------------

            reconstructed_text = reconstruct_text(
                ocr_items,
                y_tolerance=15
                )


            # ------------------------------------------------
            # Visual debugging
            # ------------------------------------------------

            debug_path = (
                DEBUG_DIR
                / f"{image_path.stem}_ocr.jpg"
            )

            draw_ocr_boxes(
                processed_image,
                ocr_items,
                debug_path
            )


            # ------------------------------------------------
            # Field extraction
            # ------------------------------------------------
            # GLiNER extraction
            gliner_entities = gliner.extract(reconstructed_text)
            # Existing rule-based extraction
            texts = [item["text"] for item in ocr_items]
            boxes = [item["box"] for item in ocr_items]

            rule_fields = extract_fields(texts, boxes, gliner_entities)

            

            # Combine both
            fields, field_confidence, field_levels = resolve_fields(
                ocr_items,
                gliner_entities,
                rule_fields
            )


            # ------------------------------------------------
            # Create JSON
            # ------------------------------------------------

            output_data = fields


            # ------------------------------------------------
            # Save JSON
            # ------------------------------------------------

            output_path = (
                OUTPUT_DIR
                / f"{image_path.stem}.json"
            )


            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    output_data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )


            # ------------------------------------------------
            # Print result
            # ------------------------------------------------

            print(
                json.dumps(
                    output_data,
                    indent=4,
                    ensure_ascii=False
                )
            )


    except Exception as e:

        print(
            f"ERROR processing {image_path.name}"
        )

        print(e)


# ============================================================
# FINISHED
# ============================================================

print("\n" + "=" * 60)

print("BATCH PROCESSING COMPLETE")

print("=" * 60)
