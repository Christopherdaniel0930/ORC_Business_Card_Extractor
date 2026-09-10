from gliner_extractor import GLiNERExtractor


# Simulated PaddleOCR output
ocr_items = [
    {
        "text": "JULIANA SILVA",
        "confidence": 0.99,
        "box": [[100, 100], [300, 100], [300, 140], [100, 140]]
    },
    {
        "text": "MANAGER",
        "confidence": 0.99,
        "box": [[100, 160], [220, 160], [220, 190], [100, 190]]
    },
    {
        "text": "BORCELLE",
        "confidence": 0.99,
        "box": [[100, 210], [250, 210], [250, 240], [100, 240]]
    },
    {
        "text": "123 Anywhere St., Any City",
        "confidence": 0.99,
        "box": [[100, 260], [400, 260], [400, 290], [100, 290]]
    }
]


extractor = GLiNERExtractor()

entities = extractor.extract(ocr_items)


print("\nGLiNER + PaddleOCR")
print("=" * 60)

for entity in entities:
    print(
        f"Text: {entity['text']}"
    )
    print(
        f"Label: {entity['label']}"
    )
    print(
        f"Score: {entity['score']:.3f}"
    )
    print("-" * 60)