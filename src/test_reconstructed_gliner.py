from gliner_extractor import GLiNERExtractor


text = """
FAIR DEAL
TRADING L.L.C
ABBAS عباس
SALESMAN
+971 50 945 8994
Showroom 9,10 s Sheikh Mustafa Building,
Naif-Deira, Dubai, U.A.E P.O.Box: 27328
T: +971 4 227 8717 F: +971 422 78 728
sales.fairdealtradinguae@gmail.com www.lecxo.ae
"""


extractor = GLiNERExtractor()

entities = extractor.extract(text)


print()
print("=" * 60)
print("GLiNER ON RECONSTRUCTED TEXT")
print("=" * 60)

for entity in entities:

    print(
        f"Text:  {entity['text']}"
    )

    print(
        f"Label: {entity['label']}"
    )

    print(
        f"Score: {entity['score']:.3f}"
    )

    print("-" * 60)