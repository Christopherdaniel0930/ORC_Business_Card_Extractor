import cv2
import numpy as np


def order_points(points):
    """
    Order four points as:
    top-left, top-right, bottom-right, bottom-left
    """

    points = np.array(points, dtype=np.float32)

    s = points.sum(axis=1)
    diff = np.diff(points, axis=1).flatten()

    top_left = points[np.argmin(s)]
    bottom_right = points[np.argmax(s)]

    top_right = points[np.argmin(diff)]
    bottom_left = points[np.argmax(diff)]

    return np.array(
        [top_left, top_right, bottom_right, bottom_left],
        dtype=np.float32
    )


def four_point_transform(image, points):
    """
    Apply perspective correction using four corner points.
    """

    rect = order_points(points)

    tl, tr, br, bl = rect

    # Width
    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)

    max_width = int(max(width_top, width_bottom))

    # Height
    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)

    max_height = int(max(height_left, height_right))

    destination = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(
        rect,
        destination
    )

    warped = cv2.warpPerspective(
        image,
        matrix,
        (max_width, max_height)
    )

    return warped


def _quad_score(quad, contour_area, image_shape):
    """Return a score for a plausible card-shaped quadrilateral."""
    height, width = image_shape[:2]
    image_area = height * width
    quad_area = cv2.contourArea(quad)

    if quad_area < image_area * 0.12 or quad_area > image_area * 0.92:
        return None

    rect = cv2.minAreaRect(quad.astype(np.float32))
    rect_width, rect_height = rect[1]

    if rect_width < 1 or rect_height < 1:
        return None

    aspect_ratio = max(rect_width, rect_height) / min(rect_width, rect_height)

    # Standard business cards are rectangular and usually wider than tall.
    if not 1.2 <= aspect_ratio <= 3.2:
        return None

    rectangularity = contour_area / quad_area

    if rectangularity < 0.55:
        return None

    # A contour touching multiple frame edges is normally the background, not
    # a card. Rejecting it avoids an incorrect perspective warp.
    margin = max(4, int(min(height, width) * 0.01))
    touches_edge = np.logical_or.reduce((
        quad[:, 0] <= margin,
        quad[:, 0] >= width - 1 - margin,
        quad[:, 1] <= margin,
        quad[:, 1] >= height - 1 - margin,
    ))

    if np.count_nonzero(touches_edge) >= 2:
        return None

    area_ratio = quad_area / image_area
    return (area_ratio * 100) + (rectangularity * 20)


def _candidate_masks(gray):
    """Build masks for light and edge-defined card boundaries."""
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, light = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    median = np.median(blurred)
    lower = int(max(0, 0.66 * median))
    upper = int(min(255, 1.33 * median))
    edges = cv2.Canny(blurred, lower, max(lower + 1, upper))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)

    # A dark mask is deliberately not used here: on two-tone cards it often
    # selects one dark design panel instead of the whole card.
    return (("contrast", light), ("edges", edges))


def detect_card(image):
    """Find the most likely card boundary using contrast and edge evidence."""
    if image is None or image.size == 0:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    best_quad = None
    best_score = -1.0

    image_area = image.shape[0] * image.shape[1]

    for source, mask in _candidate_masks(gray):
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            contour_area = cv2.contourArea(contour)

            minimum_area = 0.35 if source == "edges" else 0.10

            if contour_area < image_area * minimum_area:
                continue

            perimeter = cv2.arcLength(contour, True)

            for epsilon_factor in (0.01, 0.02, 0.03, 0.04):
                approx = cv2.approxPolyDP(
                    contour, epsilon_factor * perimeter, True
                )

                if len(approx) != 4 or not cv2.isContourConvex(approx):
                    continue

                quad = approx.reshape(4, 2)
                score = _quad_score(quad, contour_area, image.shape)

                if score is not None and score > best_score:
                    best_score = score
                    best_quad = quad

                break

    return best_quad


def enhance_for_ocr(image):
    """Improve local contrast and text edges without converting the card to B/W."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lightness, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced_lightness = clahe.apply(lightness)
    enhanced = cv2.cvtColor(
        cv2.merge((enhanced_lightness, a_channel, b_channel)),
        cv2.COLOR_LAB2BGR,
    )

    # A restrained unsharp mask improves small printed characters while
    # avoiding the blur that previously softened OCR features.
    softened = cv2.GaussianBlur(enhanced, (0, 0), 1.0)
    return cv2.addWeighted(enhanced, 1.35, softened, -0.35, 0)

def preprocess_card(image):

    if image is None or image.size == 0:
        raise ValueError("A non-empty image is required for preprocessing.")

    card_corners = detect_card(image)

    if card_corners is None:
        print("WARNING: Card boundary not confidently detected; using full frame.")
        corrected = image
    else:
        print("Business card detected; applying perspective correction.")
        corrected = four_point_transform(image, card_corners)

    height, width = corrected.shape[:2]

    target_width = 1600

    if width < target_width:

        scale = target_width / width

        new_width = int(width * scale)
        new_height = int(height * scale)

        corrected = cv2.resize(
            corrected,
            (new_width, new_height),
            interpolation=cv2.INTER_CUBIC
        )

    return enhance_for_ocr(corrected)


def preprocess_image(image):
    """Backward-compatible name for card preprocessing."""
    return preprocess_card(image)
