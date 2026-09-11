import cv2
from pathlib import Path


def draw_ocr_boxes(
    image_path,
    ocr_items,
    output_path
):

    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

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

    cv2.imwrite(
        str(output_path),
        image
    )

    print(
        f"Debug image saved to: {output_path}"
    )