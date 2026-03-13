import cv2
import numpy as np
from pathlib import Path
from src.config.settings import settings


class ImagePreprocessor:

    def preprocess(self, image_path: str) -> str:
        path = Path(image_path)
        img = cv2.imread(str(path))

        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Resize — keep width in [1000, IMAGE_MAX_WIDTH] for OCR accuracy
        w = gray.shape[1]
        if w > settings.IMAGE_MAX_WIDTH:
            scale = settings.IMAGE_MAX_WIDTH / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        elif w < 1000:
            scale = 1000 / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # 3. Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # 4. CLAHE contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # 5. Deskew
        deskewed = self._deskew(enhanced)

        # 6. Adaptive threshold (binarise)
        thresh = cv2.adaptiveThreshold(
            deskewed,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )

        output_path = path.with_stem(path.stem + "_processed").with_suffix(".png")
        cv2.imwrite(str(output_path), thresh)
        return str(output_path)

    def _deskew(self, gray: np.ndarray) -> np.ndarray:
        coords = np.column_stack(np.where(gray < 128))
        if len(coords) < 10:
            return gray

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle += 90
        if abs(angle) < 0.5:
            return gray

        h, w = gray.shape
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
