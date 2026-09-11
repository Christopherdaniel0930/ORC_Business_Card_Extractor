import cv2
from pathlib import Path


def draw_ocr_boxes(
    image_source,
    ocr_items,
    output_path
):
    """Draw OCR boxes on an image array or on an image loaded from a path."""
    if isinstance(image_source, (str, Path)):
        image = cv2.imread(str(image_source))

        if image is None:
            raise FileNotFoundError(
                f"Could not read image: {image_source}"
            )
    else:
        if image_source is None or getattr(image_source, "size", 0) == 0:
            raise ValueError("image_source must be a readable image path or non-empty image array")

        # Do not modify the preprocessed image used by OCR.
        image = image_source.copy()

    for index, item in enumerate(ocr_items):

        box = item["box"]

        # Convert box to OpenCV format
        points = [
            [int(point[0]), int(point[1])]
            for point in box
        ]

        # Draw polygon
        for i in range(len(points)):

            start = tuple(points[i])

            end = tuple(
                points[
                    (i + 1) % len(points)
                ]
            )

            cv2.line(
                image,
                start,
                end,
                (0, 255, 0),
                2
            )

        # Label
        x = item["x1"]
        y = max(item["y1"] - 5, 15)

        label = f"{index}: {item['text']}"

        cv2.putText(
            image,
            label,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            1,
            cv2.LINE_AA
        )

    # Create output directory
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not cv2.imwrite(str(output_path), image):
        raise OSError(f"Could not save debug image: {output_path}")

    print(
        f"Debug image saved to: {output_path}"
    )
