# Business Card Extractor

A Python pipeline and REST service for extracting structured contact details from business card images. The pipeline runs OCR locally with **RapidOCR**, extracts contact fields with **regular expressions**, uses an **OpenAI-compatible LLM** (e.g. Ollama) for semantic extraction (name, designation, and company name), and validates the combined result using **Pydantic**.

---

## Pipeline Overview

1. **OCR Processing:** [`app.common.document_pipeline.process_document(image_path)`](file:///d:/business_extractor/app/common/document_pipeline.py) runs RapidOCR once to extract recognized text and bounding boxes.
2. **Extraction & Merging:** [`app.business_card.pipeline.process_business_card(...)`](file:///d:/business_extractor/app/business_card/pipeline.py):
   - **Deterministic Extraction:** Regular expressions parse `phone`, `fax`, `email`, `website`, and `address`.
   - **Semantic Extraction:** Prompt sent to configured LLM (Ollama) extracts `name`, `designation`, and `company_name`.
   - **Merger & Validation:** Combines fields and validates them into a [`BusinessCardData`](file:///d:/business_extractor/app/business_card/models/business_card_model.py) model.

### Extracted Fields

All fields are optional strings (`Optional[str]`), defaulting to `null` if not found:

| Field | Extraction Method | Description |
|---|---|---|
| `name` | LLM | Individual's full name |
| `designation` | LLM | Job title or role |
| `company_name` | LLM | Organization or business name |
| `phone` | Regex | Telephone / mobile number |
| `fax` | Regex | Fax number |
| `email` | Regex | Email address |
| `website` | Regex | Website or URL |
| `address` | Regex | Physical address |

---

## Requirements & Setup

- **Python:** 3.11 or 3.12
- **LLM Service:** An Ollama or OpenAI-compatible endpoint providing a chat completion model.

### 1. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and set your Ollama/LLM parameters:

```bash
cp .env.example .env
```

```env
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama
OLLAMA_MODEL=qwen3:8b
```

> [!NOTE]
> Ensure the specified `OLLAMA_MODEL` is pulled and running on your local Ollama server (e.g., `ollama pull qwen3:8b`).

---

## Running the Application

### Option A: Interactive CLI

Run the interactive terminal extractor from the project root:

```bash
python -m app.cli
```

Provide the path to an image when prompted (e.g., `data/business_card/test/1.jpg`). The output will be printed as structured JSON.

### Option B: FastAPI REST Service

The FastAPI application is defined in `app/api/api.py`. Start it from the project root using `uvicorn`:

```bash
uvicorn app.api:app --reload
```

Open the [Swagger UI](http://127.0.0.1:8000/docs) to explore and try the API endpoints.

#### API Specification: `POST /api/v1/documents`

Extracts business card details from an uploaded image file.

- **Request Format:** `multipart/form-data`
- **Form Field:** `file` (UploadFile)
- **Supported Formats:** JPEG, PNG, WEBP
- **Limits:** Max file size 10 MB, max image dimensions 40 Megapixels

**Success Response (`200 OK`):**

```json
{
  "document_type": "business_card",
  "result": {
    "name": "Jane Doe",
    "designation": "Chief Technology Officer",
    "company_name": "Acme Innovations",
    "phone": "+1-555-0199",
    "fax": null,
    "email": "jane.doe@acme.com",
    "website": "https://www.acme.com",
    "address": "123 Innovation Way, Suite 400"
  }
}
```

**Common Error Responses:**

| Status Code | Reason |
|---|---|
| `400 Bad Request` | Corrupted or unreadable image file |
| `413 Request Entity Too Large` | Image exceeds 10 MB or 40 megapixels |
| `415 Unsupported Media Type` | Unsupported image format (not JPEG/PNG/WEBP) |
| `422 Unprocessable Entity` | OCR could not extract any text from the card |
| `500 Internal Server Error` | Unexpected processing failure during extraction |

---

## Testing

Run the test suite using `pytest`:

```bash
pytest -q
```

Tests are split into:
- `tests/`: Module-level unit tests for deterministic parsing, merging, validator, and pipeline mocks.
- `testing/`: Scoped tests categorized into `unit`, `integration`, and `component`.

Pipeline tests utilize fake/mocked clients and do not require a running LLM server.

---

## Project Structure

```text
business_extractor/
├── app/
│   |
│   ├── business_card/
│   │   ├── models/                # BusinessCardData Pydantic model
│   │   ├── modules/
│   │   │   ├── deterministic_extractor.py  # Regex extraction (phone, email, etc.)
│   │   │   ├── llm_extractor.py            # Prompt builder and LLM client caller
│   │   │   ├── merger.py                   # Combines deterministic & semantic outputs
│   │   │   └── validator.py                # Field normalization & validation
│   │   ├── schemas/               # Exported schemas
│   │   └── pipeline.py            # Pipeline orchestrator
│   ├── common/
│   │   ├── config.py              # Environment configuration & settings
│   │   ├── document_pipeline.py   # OCR bridge and document processor
│   │   ├── llm_client.py          # OpenAI/Ollama API wrapper
│   │   ├── logging.py             # Logging setup
│   │   ├── ocr.py                 # RapidOCR integration
│   │   └── processing_timing.py   # Stage timing utilities
│   ├── api.py                     # FastAPI application & business card endpoint
│   └── cli.py                     # Interactive CLI entrypoint
├── data/                          # Sample test images
├── tests/                         # Root test suite
├── testing/                       # Component, integration, and unit test suites
├── .env.example                   # Environment variable template
├── pyproject.toml                 # Build config & test settings
└── requirements.txt               # Dependencies
```
