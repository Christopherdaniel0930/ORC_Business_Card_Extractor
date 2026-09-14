# Business Card OCR

Extract text and contact details from business-card images.

## Web UI (Streamlit)

Install the dependencies, then run the app from the project root:

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL shown in the terminal, upload a card image or use **Use
camera** to take one, extract its details, and edit, save, or download the
resulting JSON. The OCR box preview is available in the app after extraction.

## Desktop UI

From the project root, run:

```powershell
.venv\Scripts\python.exe src\ui.py
```

Choose a card image, select **Extract details**, then review or correct the
fields before saving. Results are written to `outputs/`; the OCR box preview is
written to `data/debug/`.
