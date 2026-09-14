import re


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_ocr_text(text):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


# ============================================================
# WORD BOX CONVERSION
# ============================================================

def convert_word_box(box):
    """
    Convert PaddleOCR word box:

        [x1, x2, y1, y2]

    into polygon:

        [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
    """

    x1, x2, y1, y2 = map(int, box)

    return [
        [x1, y1],
        [x2, y1],
        [x2, y2],
        [x1, y2]
    ]


# ============================================================
# CONTACT TEXT SPLITTING
# ============================================================

def split_contact_text(text):

    parts = re.split(
        r"\s*[|/]\s*",
        text
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


# ============================================================
# PHONE NORMALIZATION
# ============================================================

def normalize_phone(text):

    cleaned = re.sub(
        r"^(T|TEL|TEL\.|PHONE|M|MOBILE|F|FAX)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Do not modify email / website
    if "@" in cleaned:
        return text

    if re.search(
        r"\bwww\.|\.com\b|\.ae\b|\.net\b",
        cleaned,
        re.IGNORECASE
    ):
        return text

    digits = re.sub(
        r"\D",
        "",
        cleaned
    )

    if len(digits) < 7:
        return text

    cleaned = re.sub(
        r"[^\d+\-\s()]",
        "",
        cleaned
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned
    ).strip()

    return cleaned


# ============================================================
# APPROXIMATE BOX SPLITTING
# ============================================================

def split_box_horizontally(box, parts):

    x1, y1 = box[0]
    x2, y2 = box[2]

    total_length = sum(
        len(part)
        for part in parts
    )

    if total_length == 0:
        return [box] * len(parts)

    boxes = []

    current_x = x1
    total_width = x2 - x1

    for part in parts:

        part_width = (
            total_width *
            (len(part) / total_length)
        )

        new_x1 = int(current_x)
        new_x2 = int(current_x + part_width)

        new_box = [
            [new_x1, y1],
            [new_x2, y1],
            [new_x2, y2],
            [new_x1, y2]
        ]

        boxes.append(new_box)

        current_x = new_x2

    return boxes


# ============================================================
# CREATE OCR ITEMS
# ============================================================

def get_box_geometry(box):
    """Return the positional fields required by text reconstruction."""

    x_values = [point[0] for point in box]
    y_values = [point[1] for point in box]

    x1, x2 = min(x_values), max(x_values)
    y1, y2 = min(y_values), max(y_values)

    return {
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "center_x": (x1 + x2) / 2,
        "center_y": (y1 + y2) / 2,
    }

def create_ocr_items(
    texts,
    scores,
    boxes,
    word_texts=None,
    word_boxes=None
):

    ocr_items = []

    for i, (text, score, box) in enumerate(
        zip(texts, scores, boxes)
    ):

        normalized_box = (
            box.tolist()
            if hasattr(box, "tolist")
            else box
        )

        item = {
            "text": normalize_ocr_text(text),
            "confidence": float(score),
            "box": normalized_box,
            **get_box_geometry(normalized_box),
            "words": []
        }

        # ----------------------------------------------------
        # Add real PaddleOCR word boxes
        # ----------------------------------------------------

        if (
            word_texts is not None
            and word_boxes is not None
            and i < len(word_texts)
            and i < len(word_boxes)
        ):

            line_words = word_texts[i]
            line_word_boxes = word_boxes[i]

            for word, word_box in zip(
                line_words,
                line_word_boxes
            ):

                if not word.strip():
                    continue

                item["words"].append({
                    "text": word,
                    "box": convert_word_box(word_box)
                })

        ocr_items.append(item)

    return ocr_items


# ============================================================
# POST PROCESS OCR ITEMS
# ============================================================

def process_ocr_items(ocr_items):

    processed = []

    for item in ocr_items:

        original_text = item["text"]

        text = normalize_ocr_text(
            original_text
        )

        if not text:
            continue

        parts = split_contact_text(text)

        if len(parts) == 1:

            processed.append({
                "text": normalize_phone(parts[0]),
                "box": item["box"],
                "confidence": item["confidence"],
                **get_box_geometry(item["box"]),
                "words": item.get("words", [])
            })

        else:

            # This is only a fallback for text containing
            # "|" or "/". Real word boxes are preserved.
            sub_boxes = split_box_horizontally(
                item["box"],
                parts
            )

            for part, sub_box in zip(
                parts,
                sub_boxes
            ):

                processed.append({
                    "text": normalize_phone(part),
                    "box": sub_box,
                    "confidence": item["confidence"],
                    **get_box_geometry(sub_box),
                    "words": item.get("words", [])
                })

    return processed
