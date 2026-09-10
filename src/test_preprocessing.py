import cv2
from pathlib import Path

from preprocessing import preprocess_image


PROJECT_ROOT = Path(__file__).resolve().parent.parent

image_path = PROJECT_ROOT / "data" / "images" / "image4.jpeg"

output_path = (
    PROJECT_ROOT
    / "data"
    / "debug"
    / "image1_preprocessed.jpg"
)


image = cv2.imread(str(image_path))

if image is None:
    raise FileNotFoundError(
        f"Could not load image: {image_path}"
    )


processed = preprocess_image(image)

cv2.imwrite(
    str(output_path),
    processed
)

print(f"Preprocessed image saved to: {output_path}")