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


def detect_card(image):
    """
    Detect a bright business card against a darker background.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Smooth small texture variations
    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    # --------------------------------------------------
    # BRIGHT REGION DETECTION
    # --------------------------------------------------

    # For this type of image, the white card is much
    # brighter than the dark background.
    _, mask = cv2.threshold(
        gray,
        160,
        255,
        cv2.THRESH_BINARY
    )

    # IMPORTANT:
    # Do NOT use morphological closing here.
    # It can connect the card to bright background regions.

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    image_area = image.shape[0] * image.shape[1]

    best_quad = None
    best_area = 0

    for contour in contours:

        area = cv2.contourArea(contour)

        # Ignore small objects
        if area < image_area * 0.10:
            continue

        perimeter = cv2.arcLength(
            contour,
            True
        )

        # Try several approximation levels
        for epsilon_factor in [0.01, 0.015, 0.02, 0.03]:

            approx = cv2.approxPolyDP(
                contour,
                epsilon_factor * perimeter,
                True
            )

            if len(approx) != 4:
                continue

            if not cv2.isContourConvex(approx):
                continue

            quad_area = cv2.contourArea(approx)

            if quad_area > best_area:
                best_area = quad_area
                best_quad = approx.reshape(4, 2)

            break

    return best_quad

def preprocess_card(image):

    card_corners = detect_card(image)

    if card_corners is None:
        print("WARNING: Business card boundary not detected.")
        return image

    height, width = image.shape[:2]

    # Check whether detected card is basically the entire image
    x_min = card_corners[:, 0].min()
    y_min = card_corners[:, 1].min()
    x_max = card_corners[:, 0].max()
    y_max = card_corners[:, 1].max()

    detected_width = x_max - x_min
    detected_height = y_max - y_min

    width_ratio = detected_width / width
    height_ratio = detected_height / height

    if width_ratio > 0.95 and height_ratio > 0.95:
        print("Detected contour is the full image.")
        print("Skipping perspective correction.")
        return image

    print("Business card detected.")
    print("Corners:")

    for point in card_corners:
        print(f"  {point}")

    corrected = four_point_transform(
        image,
        card_corners
    )

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

    corrected = cv2.GaussianBlur(
        corrected,
        (3, 3),
        0
    )

    return corrected