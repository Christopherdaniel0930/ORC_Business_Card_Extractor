import cv2


def draw_ocr_boxes(image, ocr_items, output_path):

    # If image is a file path, load it
    if isinstance(image, (str, bytes)):
        image = cv2.imread(image)

        if image is None:
            raise FileNotFoundError(
                f"Could not read image: {image}"
            )

    # Make a copy so the original image is not modified
    output = image.copy()

    for item in ocr_items:

        box = item["box"]
        text = item["text"]
        confidence = item["confidence"]

        # Convert box to OpenCV integer format
        points = [
            (int(x), int(y))
            for x, y in box
        ]

        # Draw OCR bounding box
        for i in range(len(points)):
            cv2.line(
                output,
                points[i],
                points[(i + 1) % len(points)],
                (0, 255, 0),
                2
            )

        # Label position
        x, y = points[0]

        label = f"{text} ({confidence:.2f})"

        cv2.putText(
            output,
            label,
            (x, max(y - 5, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA
        )

    cv2.imwrite(
        str(output_path),
        output
    )