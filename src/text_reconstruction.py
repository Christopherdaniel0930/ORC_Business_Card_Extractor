from collections import defaultdict


def reconstruct_text(ocr_items, y_tolerance=15):
    """
    Reconstruct OCR text into lines using bounding-box positions.

    OCR items must contain:
        text
        x1
        y1
        x2
        y2
        center_y
    """

    if not ocr_items:
        return ""

    # --------------------------------------------------
    # 1. SORT TOP → BOTTOM
    # --------------------------------------------------

    items = sorted(
        ocr_items,
        key=lambda item: (
            item["center_y"],
            item["x1"]
        )
    )

    # --------------------------------------------------
    # 2. GROUP ITEMS INTO LINES
    # --------------------------------------------------

    lines = []

    for item in items:

        placed = False

        for line in lines:

            avg_y = sum(
                x["center_y"]
                for x in line
            ) / len(line)

            if abs(item["center_y"] - avg_y) <= y_tolerance:

                line.append(item)
                placed = True
                break

        if not placed:
            lines.append([item])

    # --------------------------------------------------
    # 3. SORT EACH LINE LEFT → RIGHT
    # --------------------------------------------------

    for line in lines:
        line.sort(
            key=lambda item: item["x1"]
        )

    # --------------------------------------------------
    # 4. BUILD TEXT
    # --------------------------------------------------

    reconstructed_lines = []

    for line in lines:

        text = " ".join(
            item["text"].strip()
            for item in line
            if item["text"].strip()
        )

        if text:
            reconstructed_lines.append(text)

    return "\n".join(reconstructed_lines)