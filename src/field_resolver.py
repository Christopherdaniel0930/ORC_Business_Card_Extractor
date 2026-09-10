from difflib import SequenceMatcher

def confidence_level(score):
    """
    Convert numeric confidence into a reliability level.
    """

    if score >= 0.90:
        return "HIGH"

    if score >= 0.70:
        return "MEDIUM"

    return "LOW"

def normalize(text):
    """Normalize text for comparison."""
    return " ".join(text.lower().strip().split())


def similarity(a, b):
    """Calculate text similarity."""
    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()


def match_entity_to_ocr(entity, ocr_items):
    """
    Match a GLiNER entity back to the original OCR item.
    """

    entity_text = entity["text"]

    best_item = None
    best_score = 0

    for item in ocr_items:

        score = similarity(
            entity_text,
            item["text"]
        )

        if score > best_score:
            best_score = score
            best_item = item

    # Require reasonable similarity
    if best_score >= 0.75:
        return best_item

    return None

def merge_address_entities(gliner_entities):
    """
    Merge multiple GLiNER address entities into one address string.
    """

    address_entities = [
        entity
        for entity in gliner_entities
        if entity["label"] == "address"
    ]

    if not address_entities:
        return None

    # GLiNER provides character offsets.
    # Sort entities according to their position in the text.
    address_entities.sort(
        key=lambda entity: entity["start"]
    )

    merged = " ".join(
        entity["text"].strip()
        for entity in address_entities
    )

    return merged


def resolve_fields(ocr_items, gliner_entities, rule_fields):
    """
    Combine rule-based extraction and GLiNER.

    Priority:
    1. Regex/rules for phone, email, website
    2. Rule-based semantic extraction
    3. GLiNER only fills missing fields
    4. Never allow the same value to occupy
       multiple semantic fields
    """

    result = {
        "name": rule_fields.get("name"),
        "designation": rule_fields.get("designation"),
        "organization": rule_fields.get("organization"),
        "phone": rule_fields.get("phone"),
        "email": rule_fields.get("email"),
        "website": rule_fields.get("website"),
        "address": rule_fields.get("address")
    }

    field_confidence = {
        "name": 0.0,
        "designation": 0.0,
        "organization": 0.0,
        "phone": 0.0,
        "email": 0.0,
        "website": 0.0,
        "address": 0.0
    }

    # --------------------------------------------------------
    # Existing rule-based fields
    # --------------------------------------------------------

    for field in field_confidence:

        if result[field]:

            # Rule-based extraction is considered reliable.
            field_confidence[field] = 0.80

    # --------------------------------------------------------
    # Semantic GLiNER labels
    # --------------------------------------------------------

    gliner_map = {
        "person name": "name",
        "organization": "organization",
        "job title": "designation",
        "address": "address"
    }

    # --------------------------------------------------------
    # Track values already assigned
    # --------------------------------------------------------

    def value_already_used(value, exclude_field=None):

        if not value:
            return False

        for field, existing_value in result.items():

            if field == exclude_field:
                continue

            if not existing_value:
                continue

            if similarity(
                value,
                existing_value
            ) >= 0.85:
                return True

        return False

    # --------------------------------------------------------
    # Sort GLiNER entities by confidence
    # --------------------------------------------------------

    sorted_entities = sorted(
        gliner_entities,
        key=lambda entity: entity["score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Process GLiNER
    # --------------------------------------------------------

    for entity in sorted_entities:

        label = entity["label"]
        entity_text = entity["text"].strip()
        score = entity["score"]

        field = gliner_map.get(label)

        if field is None:
            continue

        if not entity_text:
            continue

        # Ignore weak predictions
        if score < 0.60:
            continue

        # ----------------------------------------------------
        # Don't reuse an existing value
        # ----------------------------------------------------

        if value_already_used(
            entity_text,
            exclude_field=field
        ):
            continue

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        if field == "name":

            if not result["name"]:

                result["name"] = entity_text
                field_confidence["name"] = score

        # ----------------------------------------------------
        # DESIGNATION
        # ----------------------------------------------------

        elif field == "designation":

            if not result["designation"]:

                result["designation"] = entity_text
                field_confidence["designation"] = score

        # ----------------------------------------------------
        # ORGANIZATION
        # ----------------------------------------------------

        elif field == "organization":

            if not result["organization"]:

                result["organization"] = entity_text
                field_confidence["organization"] = score

        # ----------------------------------------------------
        # ADDRESS
        # ----------------------------------------------------

        elif field == "address":

            if not result["address"]:

                result["address"] = entity_text
                field_confidence["address"] = score

    # --------------------------------------------------------
    # GLiNER address fallback
    # --------------------------------------------------------

    if not result["address"]:

        gliner_address = merge_address_entities(
            gliner_entities
        )

        if gliner_address:

            result["address"] = gliner_address

            # Use the highest address confidence
            address_scores = [
                entity["score"]
                for entity in gliner_entities
                if entity["label"] == "address"
            ]

            if address_scores:

                field_confidence["address"] = max(
                    address_scores
                )

    # --------------------------------------------------------
    # Final duplicate protection
    # --------------------------------------------------------

    semantic_fields = [
        "name",
        "designation",
        "organization"
    ]

    for i, field_a in enumerate(semantic_fields):

        if not result[field_a]:
            continue

        for field_b in semantic_fields[i + 1:]:

            if not result[field_b]:
                continue

            if similarity(
                result[field_a],
                result[field_b]
            ) >= 0.85:

                # Prefer name over organization
                if field_a == "name" and field_b == "organization":

                    result["organization"] = None
                    field_confidence["organization"] = 0.0

                # Prefer organization over name
                elif field_a == "organization" and field_b == "name":

                    result["name"] = None
                    field_confidence["name"] = 0.0

    # --------------------------------------------------------
    # Confidence levels
    # --------------------------------------------------------

    field_levels = {
        field: confidence_level(score)
        for field, score in field_confidence.items()
    }

    return (
        result,
        field_confidence,
        field_levels
    )
def gliner_supports_field(
    field,
    value,
    gliner_entities,
    threshold=0.40
):
    """
    Check whether GLiNER provides semantic support
    for an existing field value.
    """

    if not value:
        return False

    value_normalized = normalize(value)

    for entity in gliner_entities:

        entity_value = normalize(
            entity["text"]
        )

        if entity["score"] < threshold:
            continue

        # Organization
        if (
            field == "organization"
            and entity["label"] == "organization"
        ):
            if (
                entity_value in value_normalized
                or value_normalized in entity_value
            ):
                return True

        # Name
        if (
            field == "name"
            and entity["label"] == "person name"
        ):
            if (
                entity_value in value_normalized
                or value_normalized in entity_value
            ):
                return True

        # Designation
        if (
            field == "designation"
            and entity["label"] == "job title"
        ):
            if (
                entity_value in value_normalized
                or value_normalized in entity_value
            ):
                return True

        # Address
        if (
            field == "address"
            and entity["label"] == "address"
        ):
            if (
                entity_value in value_normalized
                or value_normalized in entity_value
            ):
                return True

    return False