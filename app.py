"""Streamlit web interface for the business-card text extractor.

Run from the project root with ``streamlit run app.py``.
"""

import hashlib
import json
import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
FIELD_LABELS = {
    "name": "Name",
    "designation": "Designation",
    "organization": "Organization",
    "phone": "Phone",
    "email": "Email",
    "website": "Website",
    "address": "Address",
}

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@st.cache_resource(show_spinner=False)
def get_processor():
    """Import the pipeline once so its OCR models stay warm between reruns."""
    # pyrefly: ignore [missing-import]
    from ocr import process_image

    return process_image


def persist_upload(uploaded_file) -> Path:
    """Save an uploaded image under a stable, collision-resistant local name."""
    content = uploaded_file.getvalue()
    digest = hashlib.sha256(content).hexdigest()[:16]
    suffix = Path(uploaded_file.name).suffix.lower() or ".png"
    upload_path = UPLOAD_DIR / f"{digest}{suffix}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if not upload_path.exists():
        upload_path.write_bytes(content)
    return upload_path


def reset_result(upload_key: str) -> None:
    """Reset editable values when the selected image changes."""
    if st.session_state.get("upload_key") == upload_key:
        return
    st.session_state.upload_key = upload_key
    st.session_state.result = None
    for field in FIELD_LABELS:
        st.session_state[f"field_{field}"] = ""


def current_fields() -> dict[str, str | None]:
    return {
        field: st.session_state.get(f"field_{field}", "").strip() or None
        for field in FIELD_LABELS
    }


st.set_page_config(page_title="Business Card Extractor", page_icon="🪪", layout="wide")
st.markdown(
    """<style>
    .block-container { max-width: 1200px; padding-top: 2.5rem; }
    [data-testid="stMetric"] { background: #f7f9fc; border-radius: 10px; padding: .6rem; }
    </style>""",
    unsafe_allow_html=True,
)

st.title("Business Card Text Extractor")
st.caption("Upload or photograph a business card, extract its contact details, then correct or download the result.")

input_source = st.radio(
    "Add a business-card image",
    ("Upload image", "Use camera"),
    horizontal=True,
    label_visibility="collapsed",
)

if input_source == "Upload image":
    uploaded_file = st.file_uploader(
        "Business-card image",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        help="Use a clear, front-facing photo for the best OCR result.",
    )
else:
    uploaded_file = st.camera_input(
        "Take a photo of the business card",
        help="Allow camera access, keep the card flat and well lit, then take a photo.",
    )

if not uploaded_file:
    st.info("Choose an image or take a photo to get started.")
    st.stop()

image_path = persist_upload(uploaded_file)
upload_key = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
reset_result(upload_key)

left, right = st.columns((1.05, 0.95), gap="large")
with left:
    st.subheader("Card preview")
    st.image(uploaded_file, use_container_width=True)

with right:
    st.subheader("Extract contact details")
    st.write("The first extraction can take a little longer while the OCR models load.")
    if st.button("Extract details", type="primary", use_container_width=True):
        try:
            with st.spinner("Reading the business card…"):
                result = get_processor()(image_path)
            st.session_state.result = {
                "fields": result["fields"],
                "ocr_text": result["ocr_text"],
                "output_path": str(result["output_path"]),
                "debug_path": str(result["debug_path"]),
            }
            for field in FIELD_LABELS:
                st.session_state[f"field_{field}"] = result["fields"].get(field) or ""
            st.success("Details extracted. Review and edit them below.")
        except Exception as error:
            st.error(f"Extraction failed: {error}")

result = st.session_state.get("result")
if not result:
    st.stop()

st.divider()
st.subheader("Extracted details")
form_left, form_right = st.columns(2, gap="large")
fields = list(FIELD_LABELS)
for index, field in enumerate(fields):
    target = form_left if index < 4 else form_right
    with target:
        if field == "address":
            st.text_area(FIELD_LABELS[field], key=f"field_{field}", height=100)
        else:
            st.text_input(FIELD_LABELS[field], key=f"field_{field}")

edited_fields = current_fields()
output_path = Path(result["output_path"])
actions, download = st.columns(2)
with actions:
    if st.button("Save edited JSON", use_container_width=True):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(edited_fields, indent=4, ensure_ascii=False), encoding="utf-8")
        st.success(f"Saved to {output_path.relative_to(PROJECT_ROOT)}")
with download:
    st.download_button(
        "Download JSON",
        data=json.dumps(edited_fields, indent=4, ensure_ascii=False),
        file_name=f"{image_path.stem}.json",
        mime="application/json",
        use_container_width=True,
    )

with st.expander("Recognized text"):
    st.text(result["ocr_text"] or "No text was recognized.")

debug_path = Path(result["debug_path"])
if debug_path.is_file():
    with st.expander("OCR box preview"):
        st.image(str(debug_path), caption="Text regions detected by OCR", use_container_width=True)
