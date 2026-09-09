import re


# ============================================================
# REGEX
# ============================================================

def is_email(text):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, text) is not None


def is_phone(text):
    pattern = r'^\+?\d[\d\s().-]{7,}\d$'
    return re.match(pattern, text) is not None


def is_website(text):
    pattern = r'^(https?://)?(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(/.*)?$'
    return re.match(pattern, text) is not None


# ============================================================
# KEYWORDS
# ============================================================

DESIGNATION_KEYWORDS = [
    "manager",
    "director",
    "ceo",
    "cto",
    "cfo",
    "coo",
    "founder",
    "co-founder",
    "president",
    "vice president",
    "vp",
    "developer",
    "engineer",
    "designer",
    "architect",
    "consultant",
    "executive",
    "officer",
    "administrator",
    "supervisor",
    "lead",
    "head",
    "photographer"
]


ADDRESS_KEYWORDS = [
    "street",
    "st.",
    "road",
    "rd.",
    "avenue",
    "ave.",
    "lane",
    "ln.",
    "boulevard",
    "blvd",
    "drive",
    "dr.",
    "city",
    "state",
    "country",
    "india",
    "usa",
    "chennai",
    "bangalore",
    "mumbai",
    "delhi",
    "tamil nadu",
    "pin",
    "pincode"
]


ORGANIZATION_KEYWORDS = [
    "company",
    "technologies",
    "technology",
    "solutions",
    "systems",
    "industries",
    "corporation",
    "corp",
    "ltd",
    "limited",
    "pvt",
    "private",
    "group",
    "services",
    "studio",
    "agency"
]


# ============================================================
# KEYWORD FUNCTIONS
# ============================================================

def contains_designation_keyword(text):

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in DESIGNATION_KEYWORDS
    )


def contains_address_keyword(text):

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in ADDRESS_KEYWORDS
    )


def looks_like_organization(text):

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in ORGANIZATION_KEYWORDS
    )


def looks_like_name(text):

    if any(char.isdigit() for char in text):
        return False

    if "@" in text:
        return False

    if "." in text:
        return False

    words = text.split()

    if not 1 <= len(words) <= 4:
        return False

    if len(text) > 40:
        return False

    return True


# ============================================================
# BOUNDING BOX FUNCTIONS
# ============================================================

def get_box_coordinates(box):

    x1 = min(point[0] for point in box)
    y1 = min(point[1] for point in box)

    x2 = max(point[0] for point in box)
    y2 = max(point[1] for point in box)

    return x1, y1, x2, y2


def get_box_center(box):

    x1, y1, x2, y2 = get_box_coordinates(box)

    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    return center_x, center_y


# ============================================================
# CREATE OCR ITEMS
# ============================================================

def create_items(texts, boxes):

    items = []

    for text, box in zip(texts, boxes):

        text = text.strip()

        if not text:
            continue

        x1, y1, x2, y2 = get_box_coordinates(box)

        center_x, center_y = get_box_center(box)

        items.append({
            "text": text,
            "box": box,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "center_x": center_x,
            "center_y": center_y
        })

    return items


# ============================================================
# GROUP ADDRESS LINES
# ============================================================

def group_address_lines(address_items):

    if not address_items:
        return None

    # Sort top → bottom
    address_items.sort(
        key=lambda item: item["center_y"]
    )

    lines = []

    for item in address_items:

        if not lines:

            lines.append([item])
            continue

        previous = lines[-1][-1]

        vertical_gap = (
            item["y1"] - previous["y2"]
        )

        # If lines are close vertically,
        # treat them as part of the same address.
        if vertical_gap <= 25:

            lines[-1].append(item)

        else:

            lines.append([item])

    combined_lines = []

    for line in lines:

        # Left → right
        line.sort(
            key=lambda item: item["x1"]
        )

        line_text = " ".join(
            item["text"]
            for item in line
        )

        combined_lines.append(line_text)

    return ", ".join(combined_lines)


# ============================================================
# MAIN FIELD EXTRACTION
# ============================================================

def extract_fields(texts, boxes):

    result = {
        "name": None,
        "designation": None,
        "organization": None,
        "phone": None,
        "email": None,
        "website": None,
        "address": None
    }

    # --------------------------------------------------------
    # Create OCR objects
    # --------------------------------------------------------

    items = create_items(
        texts,
        boxes
    )

    remaining = []
    address_items = []

    # --------------------------------------------------------
    # Detect obvious fields
    # --------------------------------------------------------

    for item in items:

        text = item["text"]

        # Email
        if is_email(text):

            result["email"] = text

        # Phone
        elif is_phone(text):

            result["phone"] = text

        # Website
        elif is_website(text):

            result["website"] = text

        # Address
        elif contains_address_keyword(text):

            address_items.append(item)

        else:

            remaining.append(item)

    # --------------------------------------------------------
    # Group address
    # --------------------------------------------------------

    if address_items:

        result["address"] = group_address_lines(
            address_items
        )

    # --------------------------------------------------------
    # Sort remaining text by vertical position
    # --------------------------------------------------------

    remaining.sort(
        key=lambda item: item["center_y"]
    )

    # ========================================================
    # FIND DESIGNATION
    # ========================================================

    designation = None

    for item in remaining:

        if contains_designation_keyword(
            item["text"]
        ):

            designation = item

            result["designation"] = item["text"]

            break

    if designation:

        remaining.remove(designation)

    # ========================================================
    # FIND NAME
    # ========================================================

    name = None

    for item in remaining:

        if looks_like_name(item["text"]):

            name = item

            result["name"] = item["text"]

            break

    if name:

        remaining.remove(name)

    # ========================================================
    # FIND ORGANIZATION
    # ========================================================

    if remaining:

        organization_candidates = []

        for item in remaining:

            text = item["text"]

            score = 0

            # Known organization keywords
            if looks_like_organization(text):
                score += 10

            # Short organization names
            if len(text.split()) <= 5:
                score += 2

            # Organization is commonly below
            # the person's name
            if name:

                if item["center_y"] > name["center_y"]:
                    score += 2

            item["organization_score"] = score

            organization_candidates.append(item)

        # Highest score first
        organization_candidates.sort(
            key=lambda item: (
                -item["organization_score"],
                item["center_y"]
            )
        )

        if organization_candidates:

            result["organization"] = (
                organization_candidates[0]["text"]
            )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return result

