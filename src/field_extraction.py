import re

from difflib import SequenceMatcher

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


def extract_phone(text):
    """Find a phone number even when OCR adds a nearby label or symbol."""
    match = re.search(r'\+?\d[\d\s().-]{7,}\d', text)
    return match.group(0).strip() if match else None


def extract_email(text):
    """Find an email address embedded in a wider OCR line."""
    match = re.search(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        text,
    )

    if match:
        return match.group(0)

    # OCR commonly drops the dot in well-known provider domains, e.g.
    # ``name@gmaiLcom``. Restrict this repair to known domains so arbitrary
    # text cannot become an email address.
    match = re.search(
        r'([a-zA-Z0-9._%+-]+@(?:gmail|yahoo|outlook|hotmail))(com|org|net)\b',
        text,
        flags=re.IGNORECASE,
    )

    return f"{match.group(1)}.{match.group(2)}" if match else None


def extract_website(text):
    """Find a website embedded in a wider OCR line."""
    match = re.search(
        r'(?<!@)(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+(?:/[^\s]*)?',
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    website = match.group(0)
    website = re.sub(r"^wwww\.", "www.", website, flags=re.IGNORECASE)
    return None if "@" in website else website


def text_similarity(a, b):

    return SequenceMatcher(
        None,
        a.lower().strip(),
        b.lower().strip()
    ).ratio()
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

    # Normal person name
    if 2 <= len(words) <= 4:
        return len(text) <= 40

    # Single-word names are possible.
    # They will be accepted only when contextual
    # evidence supports them later.
    return False


def looks_like_single_word_name(text):
    """Allow a single-word name only when surrounding context supports it."""
    text = clean_text(text)

    if len(text.split()) != 1:
        return False

    return (
        re.sub(r"[^\w]", "", text, flags=re.UNICODE).isalpha()
        and not contains_designation_keyword(text)
        and not contains_address_keyword(text)
        and not looks_like_organization(text)
    )

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

    # Organization-like length is supporting evidence only. On its own, a
    # short phrase is just as likely to be a person's name.
    word_count = len(text.split())

    if score > 0 and 1 <= word_count <= 6:
        score += 2

    return score

def looks_like_company_name(text):
    """
    Detect organization names that may not contain
    obvious corporate keywords.
    """

    text = clean_text(text)

    if not text:
        return False

    # Must not be obvious personal/contact information
    if is_email(text):
        return False

    if is_phone(text):
        return False

    if is_website(text):
        return False

    if any(char.isdigit() for char in text):
        return False

    if contains_designation_keyword(text):
        return False

    if contains_address_keyword(text):
        return False

    # Strong organization indicators
    if looks_like_organization(text):
        return True

    # Common company-name pattern:
    # 1–4 words, reasonably short
    words = text.split()

    if len(words) == 1 and 2 <= len(text) <= 40:
        return True

    return False

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

def _is_organization_component(text, organization):
    """Return whether an OCR line is contained in a resolved organization."""
    if not organization:
        return False

    text_normalized = clean_text(text).lower()
    organization_normalized = clean_text(organization).lower()

    if not text_normalized:
        return False

    return (
        text_normalized == organization_normalized
        or text_normalized in organization_normalized
    )


def find_name(items, designation, organization, gliner_entities=None):

    candidates = []

    for item in items:

        text = item["text"]

        if designation and text == designation["text"]:
            continue

        if _is_organization_component(text, organization):
            continue

        if looks_like_name(text) or looks_like_single_word_name(text):

            score = 0

            # Prefer 2-word names
            words = len(text.split())

            if words == 2:
                score += 5

            elif words == 3:
                score += 4

            # A name commonly appears alongside a designation, regardless of
            # whether the card puts its logo at the top, side, or bottom.
            if designation:
                distance = abs(item["center_y"] - designation["center_y"])
                score += max(0, 4 - (distance / 100))
            else:
                score += max(0, 3 - (item["center_y"] / 300))

            # Prefer model-backed person candidates, but do not require the
            # model: rule extraction must still work offline.
            for entity in gliner_entities or []:
                if entity.get("label") != "person name":
                    continue

                if text_similarity(text, entity.get("text", "")) >= 0.75:
                    score += float(entity.get("score", 0)) * 8

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

def find_organization(items, name, designation, gliner_entities=None):

    candidates = []

    for item in items:

        text = clean_text(item["text"])

        if not text:
            continue

        # Never use name or designation as organization
        if name and text_similarity(text, name["text"]) >= 0.85:
            continue

        if designation and text_similarity(text, designation["text"]) >= 0.85:
            continue

        if is_phone(text) or is_email(text) or is_website(text):
            continue

        if contains_address_keyword(text):
            continue

        score = 0

        # --------------------------------------------------------
        # Rule-based organization evidence
        # --------------------------------------------------------

        org_score = organization_score(text)

        if org_score > 0:
            score += org_score

        # --------------------------------------------------------
        # GLiNER evidence
        # --------------------------------------------------------

        if gliner_entities:

            for entity in gliner_entities:

                label = entity["label"].lower()
                entity_text = clean_text(entity["text"])

                if label != "company name":
                    continue

                similarity = text_similarity(
                    text,
                    entity_text
                )

                if similarity >= 0.50:
                    score += entity["score"] * 15

        # --------------------------------------------------------
        # Keep candidate
        # --------------------------------------------------------

        if score > 0:
            candidates.append(
                (score, item)
            )

    if not candidates:
        return None

    # Highest scoring candidate
    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    best_score, best_item = candidates[0]

    organization = best_item["text"]

    # --------------------------------------------------------
    # Merge adjacent organization line
    # --------------------------------------------------------

    sorted_items = sorted(
        items,
        key=lambda item: item["center_y"]
    )

    best_index = sorted_items.index(best_item)

    # Previous line
    if best_index > 0:

        previous = sorted_items[best_index - 1]

        previous_text = clean_text(
            previous["text"]
        )

        if (
            previous_text
            and not (
                name
                and text_similarity(
                    previous_text,
                    name["text"]
                ) >= 0.85
            )
            and not (
                designation
                and text_similarity(
                    previous_text,
                    designation["text"]
                ) >= 0.85
            )
            and not is_phone(previous_text)
            and not is_email(previous_text)
            and not is_website(previous_text)
            and not contains_address_keyword(previous_text)
            and not contains_designation_keyword(previous_text)
        ):
            organization = (
                previous_text
                + " "
                + organization
            )

    return clean_text(organization)
# ============================================================
# MAIN FIELD EXTRACTION
# ============================================================

# ============================================================
# GROUP OCR ITEMS INTO TEXT LINES
# ============================================================

def group_text_lines(items, y_tolerance=20):

    if not items:
        return []

    sorted_items = sorted(
        items,
        key=lambda item: (
            item["center_y"],
            item["x1"]
        )
    )

    lines = []

    for item in sorted_items:

        placed = False

        for line in lines:

            avg_y = sum(
                x["center_y"]
                for x in line
            ) / len(line)

            if abs(
                item["center_y"] - avg_y
            ) <= y_tolerance:

                line.append(item)
                placed = True
                break

        if not placed:
            lines.append([item])

    # --------------------------------------------------------
    # Sort items inside each line
    # --------------------------------------------------------

    for line in lines:

        line.sort(
            key=lambda item: item["x1"]
        )

    # --------------------------------------------------------
    # Convert lines into logical objects
    # --------------------------------------------------------

    logical_lines = []

    for line in lines:

        text = " ".join(
            item["text"]
            for item in line
        )

        text = clean_text(text)

        if not text:
            continue

        logical_lines.append({
            "text": text,
            "items": line,
            "center_y": sum(
                item["center_y"]
                for item in line
            ) / len(line),
            "x1": min(
                item["x1"]
                for item in line
            ),
            "y1": min(
                item["y1"]
                for item in line
            ),
            "x2": max(
                item["x2"]
                for item in line
            ),
            "y2": max(
                item["y2"]
                for item in line
            )
        })

    return logical_lines

# ============================================================
# MERGE MULTI-LINE ORGANIZATION
# ============================================================

def merge_organization_lines(lines, name_line=None, designation_line=None):
    """
    Merge organization lines while preventing name/designation
    lines from being incorrectly included.
    """

    if not lines:
        return None

    # Remove name and designation lines
    filtered_lines = []

    for line in lines:
        if name_line is not None and line is name_line:
            continue

        if designation_line is not None and line is designation_line:
            continue

        filtered_lines.append(line)

    if not filtered_lines:
        return None

    # Find organization candidates
    candidates = []

    for line in filtered_lines:
        text = clean_text(line["text"])

        if not text:
            continue

        if contains_designation_keyword(text):
            continue

        if looks_like_name(text):
            continue

        score = organization_score(text)

        # Strong organization indicators
        if score > 0:
            candidates.append((line, score))

    if not candidates:
        return None

    # Pick the strongest organization line
    best_line, best_score = max(
        candidates,
        key=lambda x: x[1]
    )

    organization_text = clean_text(best_line["text"])

    # Merge nearby organization lines
    best_index = filtered_lines.index(best_line)

    # Previous line
    if best_index > 0:
        previous = filtered_lines[best_index - 1]
        previous_text = clean_text(previous["text"])

        if (
            previous_text
            and not looks_like_name(previous_text)
            and not contains_designation_keyword(previous_text)
            and not is_phone(previous_text)
            and not is_email(previous_text)
            and not is_website(previous_text)
        ):
            organization_text = previous_text + " " + organization_text

    # Next line
    if best_index + 1 < len(filtered_lines):
        next_line = filtered_lines[best_index + 1]
        next_text = clean_text(next_line["text"])

        if (
            next_text
            and not looks_like_name(next_text)
            and not contains_designation_keyword(next_text)
            and not is_phone(next_text)
            and not is_email(next_text)
            and not is_website(next_text)
        ):
            # Only merge if it looks organization-related
            if (
                organization_score(next_text) > 0
                or len(next_text.split()) <= 3
            ):
                organization_text += " " + next_text

    return organization_text

def extract_fields(texts, boxes, gliner_entities=None):

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

        email = extract_email(text)
        phone = extract_phone(text)
        website_source = re.sub(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            '',
            text,
        )
        website = extract_website(website_source)

        if email:

            result["email"] = email
            result["website"] = website or result["website"]

        elif phone:

            result["phone"] = phone
            result["website"] = website or result["website"]

        elif website:

            result["website"] = website

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
    # Sort remaining OCR items
    # --------------------------------------------------------

    remaining.sort(
        key=lambda item: item["center_y"]
    )

    # --------------------------------------------------------
    # Group into logical text lines
    # --------------------------------------------------------

    logical_lines = group_text_lines(
        remaining
    )

    # --------------------------------------------------------
    # FIND DESIGNATION
    # --------------------------------------------------------

    designation_line = None

    for line in logical_lines:

        if contains_designation_keyword(
            line["text"]
        ):

            designation_line = line

            result["designation"] = line["text"]

            break

    # --------------------------------------------------------
    # FIND ORGANIZATION BEFORE NAME
    # --------------------------------------------------------
    # Company names and people can both be short capitalized phrases. Resolve
    # a company first, then remove its component lines from name candidates.

    organization = find_organization(
        logical_lines,
        None,
        designation_line,
        gliner_entities
    )

    if organization:
        result["organization"] = organization

    # --------------------------------------------------------
    # FIND NAME
    # --------------------------------------------------------

    name_line = find_name(
        logical_lines,
        designation_line,
        organization,
        gliner_entities,
    )

    if name_line:
        result["name"] = name_line["text"]

    return result