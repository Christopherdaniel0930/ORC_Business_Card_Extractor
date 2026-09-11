from gliner import GLiNER


class GLiNERExtractor:

    def __init__(self):
        print("Loading GLiNER model...")

        self.model = GLiNER.from_pretrained(
            "gliner-community/gliner_small-v2.5"
        )

        print("GLiNER model loaded.")

    def extract(self, text):

        # Accept either reconstructed text or the OCR-item list used by the
        # existing OCR integration scripts.
        if isinstance(text, (list, tuple)):
            text = "\n".join(
                item.get("text", "").strip()
                for item in text
                if isinstance(item, dict) and item.get("text")
            )

        if not isinstance(text, str):
            raise TypeError("text must be a string or a sequence of OCR items")

        if not text.strip():
            return []

        labels = [
            "person name",
            "company name",
            "job title",
            "physical address",
            "phone number",
            "email address",
            "website"
        ]

        entities = self.model.predict_entities(
            text,
            labels,
            threshold=0.35
        )

        return entities
