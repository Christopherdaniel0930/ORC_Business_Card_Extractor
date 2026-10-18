# Business Card Extractor

A Python library-style pipeline for extracting contact details from business card images. The project runs OCR locally with RapidOCR, extracts contact fields with regular expressions, uses an OpenAI-compatible LLM for name, designation, and company name, then validates the combined result with Pydantic.

## Pipeline

1. `app.common.document_pipeline.process_document(image_path)` runs OCR once and prepares the recognized text and rows.
2. `app.business_card.pipeline.process_business_card(...)` extracts deterministic contact details and LLM semantic fields, merges them, and returns a `BusinessCardData` model.

Fields are optional strings: `name`, `designation`, `company_name`, `phone`, `fax`, `email`, `website`, and `address`.

## Requirements and setup

- Python 3.11 or 3.12 (declared supported versions)
- An Ollama or OpenAI-compatible chat completions endpoint for semantic fields

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set the endpoint and model:

```env
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama
OLLAMA_MODEL=qwen3:8b
```

The default endpoint in code is `https://ollama.com/v1`; set `OLLAMA_BASE_URL` explicitly for local Ollama. The configured model must be available from that endpoint.

## Run extraction from the terminal

From the repository root, start the interactive extractor:

```bash
python -m app.cli
```

When prompted, enter or paste the path to a business card image, for example `data/business_card/test/1.jpg`. The extracted fields are printed as JSON. The path can be absolute or relative to the current directory.

The command uses RapidOCR and the configured LLM client. For tests or custom integrations, call `process_document(image_path)` from `app.common.document_pipeline` and optionally inject an `llm_client` implementing `extract(prompt)`.

## Tests

Run the business-card and document-pipeline tests:

```bash
pytest -q tests/business_card tests/test_document_pipeline.py
```

The OCR test uses a sample under `data/business_card/test/`. Pipeline tests inject fake OCR and LLM clients and do not need a live model endpoint.

## Project structure

```text
app/
  business_card/       Extraction pipeline, modules, and output model
  common/              Settings, OCR, LLM client, document bridge, and timing hooks
  cli.py               Interactive terminal extractor
data/                  Sample business card images
tests/                 Business-card and document-pipeline tests
.env.example           Environment configuration template
pyproject.toml          Package metadata and pytest configuration
requirements.txt        Dependencies
```
