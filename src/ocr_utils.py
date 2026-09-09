def get_box_coordinates(box):
    x1 = min(point[0] for point in box)
    y1 = min(point[1] for point in box)

    x2 = max(point[0] for point in box)
    y2 = max(point[1] for point in box)

    return x1, y1, x2, y2


def create_ocr_items(
    texts,
    scores,
    boxes,
    min_confidence=0.50
):

    items = []

    for text, score, box in zip(texts, scores, boxes):

        text = text.strip()

        if float(score) < min_confidence:
            continue

        if not text:
            continue

        x1, y1, x2, y2 = get_box_coordinates(box)

        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        items.append({
            "text": text,
            "confidence": float(score),
            "box": [
                [int(point[0]), int(point[1])]
                for point in box
            ],
            "x1": int(x1),
            "y1": int(y1),
            "x2": int(x2),
            "y2": int(y2),
            "center_x": float(center_x),
            "center_y": float(center_y)
        })

    return items