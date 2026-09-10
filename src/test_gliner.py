from gliner_extractor import GLiNERExtractor


extractor = GLiNERExtractor()

text = """
JULIANA SILVA
MANAGER
BORCELLE
123 Anywhere St., Any City
"""

entities = extractor.extract(text)

print("\nGLiNER RESULTS")
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