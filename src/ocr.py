import os

os.environ["FLAGS_use_mkldnn"] = "0"

import json
from pathlib import Path

from paddleocr import PaddleOCR

from ocr_utils import create_ocr_items
from field_extraction import extract_fields
from visualize import draw_ocr_boxes


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
    lang="en",
    enable_mkldnn=False
)

print("PaddleOCR loaded.")


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

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        result = ocr.predict(
            str(image_path)
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
            # Visual debugging
            # ------------------------------------------------

            debug_path = (
                DEBUG_DIR
                / f"{image_path.stem}_ocr.jpg"
            )

            draw_ocr_boxes(
                image_path,
                ocr_items,
                debug_path
            )


            # ------------------------------------------------
            # Field extraction
            # ------------------------------------------------

            fields = extract_fields(
                texts,
                boxes
            )


            # ------------------------------------------------
            # Create JSON
            # ------------------------------------------------

            output_data = {

                "image": image_path.name,

                "fields": fields,

                "ocr": ocr_items
            }


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

            print("\nExtracted fields:")

            for key, value in fields.items():

                print(
                    f"{key}: {value}"
                )


            print(
                f"\nJSON saved to: {output_path}"
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