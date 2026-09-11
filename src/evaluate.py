import json
import re
from pathlib import Path
from difflib import SequenceMatcher

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

REPORT_PATH = OUTPUT_DIR / "evaluation_report.json"

FIELDS = [
    "name",
    "designation",
    "organization",
    "phone",
    "email",
    "website",
    "address"
]


# --------------------------------------------------
# Normalization
# --------------------------------------------------

def is_missing(value):
    """Treat JSON nulls and common text placeholders as absent values."""
    return value is None or str(value).strip().lower() in {"", "none", "null", "n/a"}


def normalize_general(text):
    if is_missing(text):
        return ""

    text = str(text).lower().strip()

    # Remove extra spaces
    text = " ".join(text.split())

    return text


def normalize_phone(text):
    if is_missing(text):
        return ""

    # Keep only digits
    return re.sub(r"\D", "", str(text))


def normalize_email(text):
    if is_missing(text):
        return ""

    return str(text).lower().strip()


def normalize_website(text):
    if is_missing(text):
        return ""

    text = str(text).lower().strip()

    text = re.sub(r"^https?://", "", text)
    text = re.sub(r"^www\.", "", text)

    text = text.rstrip("/")

    return text


def normalize_text(text):
    if is_missing(text):
        return ""

    text = str(text).lower().strip()

    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)

    # Normalize spaces
    text = " ".join(text.split())

    return text


def normalize_field(field, value):

    if field == "phone":
        return normalize_phone(value)

    if field == "email":
        return normalize_email(value)

    if field == "website":
        return normalize_website(value)

    return normalize_text(value)


# --------------------------------------------------
# Similarity
# --------------------------------------------------

def similarity(actual, predicted):

    if not actual or not predicted:
        return 0.0

    return SequenceMatcher(
        None,
        actual,
        predicted
    ).ratio()


# --------------------------------------------------
# Field comparison
# --------------------------------------------------

def compare_field(field, expected, predicted):

    expected_norm = normalize_field(
        field,
        expected
    )

    predicted_norm = normalize_field(
        field,
        predicted
    )

    # Both empty
    if not expected_norm and not predicted_norm:
        return {
            "correct": True,
            "similarity": 1.0,
            "expected": expected,
            "predicted": predicted
        }

    # Expected exists but prediction missing
    if expected_norm and not predicted_norm:
        return {
            "correct": False,
            "similarity": 0.0,
            "expected": expected,
            "predicted": predicted
        }

    # Prediction exists but expected is empty
    if not expected_norm and predicted_norm:
        return {
            "correct": False,
            "similarity": 0.0,
            "expected": expected,
            "predicted": predicted
        }

    score = similarity(
        expected_norm,
        predicted_norm
    )

    # Exact match OR high similarity
    if field in ["phone", "email", "website"]:
        threshold = 0.95
    else:
        threshold = 0.90

    return {
        "correct": score >= threshold,
        "similarity": round(score, 4),
        "expected": expected,
        "predicted": predicted
    }


# --------------------------------------------------
# Evaluate one card
# --------------------------------------------------

def evaluate_file(ground_truth_file):

    image_name = ground_truth_file.stem

    predicted_file = (
        OUTPUT_DIR /
        f"{image_name}.json"
    )

    if not predicted_file.exists():

        print(
            f"Missing prediction: {image_name}"
        )

        return None

    with open(
        ground_truth_file,
        "r",
        encoding="utf-8"
    ) as f:

        ground_truth = json.load(f)

    with open(
        predicted_file,
        "r",
        encoding="utf-8"
    ) as f:

        prediction_data = json.load(f)

    # Support both legacy detailed OCR output and the fields-only JSON output.
    predicted = prediction_data.get("fields", prediction_data)

    results = {}

    for field in FIELDS:

        expected = ground_truth.get(
            field
        )

        actual = predicted.get(
            field
        )

        results[field] = compare_field(
            field,
            expected,
            actual
        )

    return results


# --------------------------------------------------
# Main evaluation
# --------------------------------------------------

def main():

    ground_truth_files = sorted(
        GROUND_TRUTH_DIR.glob("*.json")
    )

    if not ground_truth_files:

        print(
            "No ground truth files found."
        )

        return

    totals = {
        field: 0
        for field in FIELDS
    }

    correct = {
        field: 0
        for field in FIELDS
    }

    similarity_totals = {
        field: 0.0
        for field in FIELDS
    }

    total_cards = 0

    detailed_results = {}

    for ground_truth_file in ground_truth_files:

        results = evaluate_file(
            ground_truth_file
        )

        if results is None:
            continue

        image_name = ground_truth_file.stem

        detailed_results[image_name] = results

        total_cards += 1

        print("\n" + "=" * 60)
        print(image_name)
        print("=" * 60)

        for field in FIELDS:

            result = results[field]

            totals[field] += 1

            similarity_totals[field] += (
                result["similarity"]
            )

            if result["correct"]:

                correct[field] += 1

                print(
                    f"{field:<15} [OK] "
                    f"{result['similarity']:.2f}"
                )

            else:

                print(
                    f"{field:<15} [FAIL] "
                    f"{result['similarity']:.2f}"
                )

                print(
                    f"    Expected : "
                    f"{result['expected']}"
                )

                print(
                    f"    Predicted: "
                    f"{result['predicted']}"
                )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    if total_cards == 0:
        print("No prediction files were available to evaluate.")
        return

    print("\n")
    print("=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    summary = {}

    for field in FIELDS:

        accuracy = (
            correct[field] /
            totals[field] *
            100
        )

        average_similarity = (
            similarity_totals[field] /
            totals[field]
        )

        print(
            f"{field:<15} "
            f"{accuracy:6.2f}% "
            f"({correct[field]}/{totals[field]}) "
            f"Similarity: {average_similarity:.2f}"
        )

        summary[field] = {
            "accuracy": round(
                accuracy,
                2
            ),
            "correct": correct[field],
            "total": totals[field],
            "average_similarity": round(
                average_similarity,
                4
            )
        }

    total_correct = sum(
        correct.values()
    )

    total_predictions = sum(
        totals.values()
    )

    overall_accuracy = (
        total_correct /
        total_predictions *
        100
    )

    print("-" * 60)

    print(
        f"Overall Accuracy: "
        f"{overall_accuracy:.2f}%"
    )

    print(
        f"Cards evaluated: "
        f"{total_cards}"
    )

    # --------------------------------------------------
    # Save report
    # --------------------------------------------------

    report = {
        "summary": summary,
        "overall_accuracy": round(
            overall_accuracy,
            2
        ),
        "cards_evaluated": total_cards,
        "details": detailed_results
    }

    with open(
        REPORT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\nEvaluation report saved to:"
    )

    print(REPORT_PATH)


if __name__ == "__main__":
    main()
