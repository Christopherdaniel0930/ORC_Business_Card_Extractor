import re


# ============================================================
# REGEX
# ============================================================

def is_email(text):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, text.strip()) is not None


def is_phone(text):
    pattern = r'^\+?\d[\d\s().-]{7,}\d$'
    return re.match(pattern, text.strip()) is not None


def is_website(text):
    pattern = r'^(https?://)?(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(/.*)?$'
    return re.match(pattern, text.strip()) is not None


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
    "photographer",
    "accountant",
    "marketing",
    "sales",
    "salesman",
    "secretary",
    "specialist",
    "coordinator",
    "analyst",
    "intern",
    "assistant",
    "partner",
    "owner",
    "director",
    "managing director",
    "operations"
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
    "pincode",
    "box",
    "p.o.box",
    "po box",
    "building",
    "floor",
    "suite",
    "dubai",
    "uae",
    "deira",
    "barsha"
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
    "agency",
    "trading",
    "consulting",
    "tech",
    "llc",
    "l.l.c",
    "inc",
    "inc.",
    "co.",
    "enterprise",
    "enterprises"
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


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(text):

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def looks_like_name(text):

    text = clean_text(text)

    if not text:
        return False

    if any(char.isdigit() for char in text):
        return False

    if "@" in text:
        return False

    if is_website(text):
        return False

    if is_phone(text):
        return False

    if contains_designation_keyword(text):
        return False

    if contains_address_keyword(text):
        return False

    if looks_like_organization(text):
        return False

    if "." in text:
        return False

    words = text.split()

    # Person names normally contain 2-4 words
    if not 2 <= len(words) <= 4:
        return False

    if len(text) > 40:
        return False

    return True


# ============================================================
# ORGANIZATION SCORE
# ============================================================

def organization_score(text):

    text = clean_text(text)

    score = 0

    if looks_like_organization(text):
        score += 10

    # Corporate suffixes
    upper = text.upper()

    if any(
        suffix in upper
        for suffix in [
            "LLC",
            "L.L.C",
            "LTD",
            "LIMITED",
            "INC",
            "PVT",
            "PRIVATE",
            "CORP"
        ]
    ):
        score += 8

    # Organization-like length
    word_count = len(text.split())

    if 1 <= word_count <= 6:
        score += 2

    return score


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

        text = clean_text(text)

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

    address_items = sorted(
        address_items,
        key=lambda item: (
            item["center_y"],
            item["x1"]
        )
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

        if vertical_gap <= 25:
            lines[-1].append(item)

        else:
            lines.append([item])

    combined_lines = []

    for line in lines:

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
# FIND PERSON NAME
# ============================================================

def find_name(items, designation, organization):

    candidates = []

    for item in items:

        text = item["text"]

        if designation and text == designation["text"]:
            continue

        if organization and text == organization:
            continue

        if looks_like_name(text):

            score = 0

            # Prefer 2-word names
            words = len(text.split())

            if words == 2:
                score += 5

            elif words == 3:
                score += 4

            # Names often appear near the top
            score += max(
                0,
                3 - (item["center_y"] / 300)
            )

            candidates.append(
                (score, item)
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# FIND ORGANIZATION
# ============================================================

def find_organization(items, name, designation):

    candidates = []

    for item in items:

        text = item["text"]

        if name and text == name["text"]:
            continue

        if designation and text == designation["text"]:
            continue

        score = organization_score(text)

        if score == 0:
            continue

        # Organization often occurs near the name/designation
        if name:

            distance = abs(
                item["center_y"] -
                name["center_y"]
            )

            if distance < 250:
                score += 2

        candidates.append(
            (score, item)
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


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

        if is_email(text):

            result["email"] = text

        elif is_phone(text):

            result["phone"] = text

        elif is_website(text):

            result["website"] = text

        elif contains_address_keyword(text):

            address_items.append(item)

        else:

            remaining.append(item)

    # --------------------------------------------------------
    # Address
    # --------------------------------------------------------

    if address_items:

        result["address"] = group_address_lines(
            address_items
        )

    # --------------------------------------------------------
    # Sort remaining
    # --------------------------------------------------------

    remaining.sort(
        key=lambda item: item["center_y"]
    )

    # --------------------------------------------------------
    # Designation
    # --------------------------------------------------------

    designation = None

    for item in remaining:

        if contains_designation_keyword(
            item["text"]
        ):

            designation = item

            result["designation"] = item["text"]

            break

    # --------------------------------------------------------
    # Organization
    # --------------------------------------------------------

    organization = find_organization(
        remaining,
        None,
        designation
    )

    if organization:

        result["organization"] = organization["text"]

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    name = find_name(
        remaining,
        designation,
        organization
    )

    if name:

        result["name"] = name["text"]

    # --------------------------------------------------------
    # If organization was not found,
    # don't randomly assign remaining text.
    # --------------------------------------------------------

    return result