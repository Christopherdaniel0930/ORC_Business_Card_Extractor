"""Business-card OCR pipeline reusable from the desktop interface or CLI."""

import json
import os
from pathlib import Path

os.environ["FLAGS_use_mkldnn"] = "0"

import cv2
from paddleocr import PaddleOCR

from field_extraction import extract_fields
from field_resolver import resolve_fields
from gliner_extractor import GLiNERExtractor
from ocr_utils import create_ocr_items
from preprocessing import preprocess_card
from text_reconstruction import reconstruct_text
from visualize import draw_ocr_boxes


PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "images"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEBUG_DIR = PROJECT_ROOT / "data" / "debug"
_ocr_engine = None
_gliner = None


def _get_engines():
    """Load OCR models only when an image is actually processed."""
    global _ocr_engine, _gliner
    if _ocr_engine is None:
        print("Loading PaddleOCR...")
        _ocr_engine = PaddleOCR(lang="ar", return_word_box=True, enable_mkldnn=False)
        print("PaddleOCR loaded.")
    if _gliner is None:
        _gliner = GLiNERExtractor()
    return _ocr_engine, _gliner


def process_image(image_path, save_output=True, save_debug=True):
    """Extract fields from one image and return fields plus output paths."""
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Selected image does not exist: {image_path}")
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ocr_engine, gliner = _get_engines()
    processed_image = preprocess_card(image)

    ocr_items = []
    for result in ocr_engine.predict(processed_image):
        ocr_items.extend(create_ocr_items(
            result["rec_texts"], result["rec_scores"], result["rec_polys"],
            result.get("text_word", []), result.get("text_word_boxes", []),
        ))

    reconstructed_text = reconstruct_text(ocr_items, y_tolerance=15)
    gliner_entities = gliner.extract(reconstructed_text)
    rule_fields = extract_fields(
        [item["text"] for item in ocr_items],
        [item["box"] for item in ocr_items],
        gliner_entities,
        ocr_items,
    )
    fields, _, _ = resolve_fields(ocr_items, gliner_entities, rule_fields)
    output_path = OUTPUT_DIR / f"{image_path.stem}.json"
    debug_path = DEBUG_DIR / f"{image_path.stem}_ocr.jpg"
    if save_output:
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(fields, output_file, indent=4, ensure_ascii=False)
    if save_debug:
        draw_ocr_boxes(processed_image, ocr_items, debug_path)
    return {"fields": fields, "ocr_text": reconstructed_text,
            "output_path": output_path, "debug_path": debug_path}


def main():
    """Process BUSINESS_CARD_IMAGE, or every supported image in data/images."""
    selected = os.environ.get("BUSINESS_CARD_IMAGE")
    image_paths = [Path(selected)] if selected else sorted(
        path for pattern in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp")
        for path in IMAGE_DIR.glob(pattern)
    )
    print(f"Found {len(image_paths)} images.")
    for image_path in image_paths:
        print(f"Processing: {image_path.name}")
        try:
            print(json.dumps(process_image(image_path)["fields"], indent=4, ensure_ascii=False))
        except Exception as error:
            print(f"ERROR processing {image_path.name}: {error}")


if __name__ == "__main__":
    main()
