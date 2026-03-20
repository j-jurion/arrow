from typing import NamedTuple

import numpy as np


class ImageBundle(NamedTuple):
    source_image: np.ndarray
    processed_images: dict[str, np.ndarray]
    filename: str = ""

    def __str__(self) -> str:
        return f"ImageBundle(filename={self.filename}, source_image_shape={self.source_image.shape}, processed_images_keys={list(self.processed_images.keys())})"
