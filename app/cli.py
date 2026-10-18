"""Interactive terminal entry point for business card extraction."""

import sys
from pathlib import Path

from app.common.document_pipeline import process_document


def main() -> int:
    image_path = input("Enter the business card image path: ").strip().strip('"')
    if not image_path:
        print("No image path provided.", file=sys.stderr)
        return 2

    path = Path(image_path).expanduser()
    if not path.is_file():
        print(f"Image file not found: {path}", file=sys.stderr)
        return 2

    try:
        result = process_document(path)
    except Exception as exc:
        print(f"Extraction failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1

    print(result["data"].model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
