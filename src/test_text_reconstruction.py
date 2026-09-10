from text_reconstruction import reconstruct_text


ocr_items = [
    {
        "text": "FAIR",
        "x1": 100,
        "center_y": 100
    },
    {
        "text": "DEAL",
        "x1": 180,
        "center_y": 101
    },
    {
        "text": "TRADING",
        "x1": 100,
        "center_y": 130
    },
    {
        "text": "L.L.C",
        "x1": 220,
        "center_y": 131
    },
    {
        "text": "ABBAS",
        "x1": 100,
        "center_y": 170
    },
    {
        "text": "SALESMAN",
        "x1": 200,
        "center_y": 171
    }
]


text = reconstruct_text(
    ocr_items
)


print()
print("=" * 60)
print("RECONSTRUCTED TEXT")
print("=" * 60)
print(text)