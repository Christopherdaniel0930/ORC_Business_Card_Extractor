"""Desktop interface for the business-card text extractor.

Run from the project root with ``.venv\\Scripts\\python.exe src\\ui.py``.
"""

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from ocr import OUTPUT_DIR, process_image


FIELD_LABELS = {
    "name": "Name", "designation": "Designation", "organization": "Organization",
    "phone": "Phone", "email": "Email", "website": "Website", "address": "Address",
}


class BusinessCardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Business Card Text Extractor")
        self.minsize(940, 620)
        self.configure(bg="#f5f7fb")
        self.selected_path = None
        self.photo = None
        self.fields = {key: tk.StringVar() for key in FIELD_LABELS}
        self.status = tk.StringVar(value="Choose a business-card image to begin.")
        self._build()

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), background="#f5f7fb")
        style.configure("Sub.TLabel", foreground="#596579", background="#f5f7fb")
        style.configure("Card.TFrame", background="white")
        header = ttk.Frame(self, padding=(28, 22, 28, 10)); header.pack(fill="x")
        ttk.Label(header, text="Business Card Text Extractor", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Upload a card image and review the extracted contact details.", style="Sub.TLabel").pack(anchor="w", pady=(3, 0))
        toolbar = ttk.Frame(self, padding=(28, 8)); toolbar.pack(fill="x")
        self.choose_button = ttk.Button(toolbar, text="Choose image", command=self.choose_image); self.choose_button.pack(side="left")
        self.extract_button = ttk.Button(toolbar, text="Extract details", command=self.extract, state="disabled"); self.extract_button.pack(side="left", padx=8)
        self.save_button = ttk.Button(toolbar, text="Save edited JSON", command=self.save_fields, state="disabled"); self.save_button.pack(side="left")
        content = ttk.Frame(self, padding=(28, 8, 28, 20)); content.pack(fill="both", expand=True)
        content.columnconfigure((0, 1), weight=1); content.rowconfigure(0, weight=1)
        preview_card = ttk.Frame(content, style="Card.TFrame", padding=18); preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ttk.Label(preview_card, text="Card preview", font=("Segoe UI", 12, "bold"), background="white").pack(anchor="w")
        self.preview = ttk.Label(preview_card, text="No image selected", anchor="center", background="#eef1f6", foreground="#697386"); self.preview.pack(fill="both", expand=True, pady=(12, 0))
        details = ttk.Frame(content, style="Card.TFrame", padding=18); details.grid(row=0, column=1, sticky="nsew", padx=(10, 0)); details.columnconfigure(1, weight=1)
        ttk.Label(details, text="Extracted details", font=("Segoe UI", 12, "bold"), background="white").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        for row, (key, label) in enumerate(FIELD_LABELS.items(), 1):
            ttk.Label(details, text=label + ":", background="white").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
            ttk.Entry(details, textvariable=self.fields[key]).grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Label(self, textvariable=self.status, style="Sub.TLabel", padding=(28, 0, 28, 18)).pack(fill="x")

    def choose_image(self):
        path = filedialog.askopenfilename(title="Choose a business card image", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"), ("All files", "*.*")])
        if not path: return
        self.selected_path = Path(path); self._show_preview(self.selected_path)
        self.extract_button.configure(state="normal"); self.status.set(f"Ready to extract: {self.selected_path.name}")

    def _show_preview(self, path):
        image = Image.open(path); image.thumbnail((430, 420)); self.photo = ImageTk.PhotoImage(image)
        self.preview.configure(image=self.photo, text="")

    def extract(self):
        if not self.selected_path: return
        self.extract_button.configure(state="disabled"); self.choose_button.configure(state="disabled")
        self.status.set("Extracting details — first use may take a moment while models load.")
        threading.Thread(target=self._run_extraction, daemon=True).start()

    def _run_extraction(self):
        try: result = process_image(self.selected_path)
        except Exception as error: self.after(0, lambda: self._finish_error(error)); return
        self.after(0, lambda: self._finish_extraction(result))

    def _finish_extraction(self, result):
        for key, variable in self.fields.items(): variable.set(result["fields"].get(key) or "")
        self.choose_button.configure(state="normal"); self.extract_button.configure(state="normal"); self.save_button.configure(state="normal")
        self.status.set(f"Done. Automatic JSON saved to {result['output_path'].name}")

    def _finish_error(self, error):
        self.choose_button.configure(state="normal"); self.extract_button.configure(state="normal"); self.status.set("Extraction failed.")
        messagebox.showerror("Extraction failed", str(error))

    def save_fields(self):
        if not self.selected_path: return
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True); output_path = OUTPUT_DIR / f"{self.selected_path.stem}.json"
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump({key: value.get().strip() or None for key, value in self.fields.items()}, output_file, indent=4, ensure_ascii=False)
        self.status.set(f"Saved edited fields to {output_path.name}")


if __name__ == "__main__":
    BusinessCardApp().mainloop()
