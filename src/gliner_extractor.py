from gliner import GLiNER


class GLiNERExtractor:

    def __init__(self):
        print("Loading GLiNER model...")

        self.model = GLiNER.from_pretrained(
            "gliner-community/gliner_small-v2.5"
        )

        print("GLiNER model loaded.")

    def extract(self, text):
        """
        Extract semantic entities from reconstructed OCR text.
        """

        labels = [
            "person name",
            "organization",
            "job title",
            "address"
        ]

        entities = self.model.predict_entities(
            text,
            labels,
            threshold=0.4
        )

        return entities