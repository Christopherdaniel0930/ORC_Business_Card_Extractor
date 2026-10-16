from app.common.ocr import read_ocr_rows
from app.business_card.pipeline import process_business_card


def process_document(image_path, llm_client=None):
    """Run OCR and business card extraction for one uploaded image."""
    rows = read_ocr_rows(str(image_path))
    text = "\n".join(
        str(row.get("text", "")).strip() for row in rows if row.get("text")
    )
    if not text.strip():
        raise RuntimeError("OCR returned no text")
    data = process_business_card(
        image_path, ocr_text=text, ocr_rows=rows, llm_client=llm_client
    )
    return {"document_type": "business_card", "data": data}
