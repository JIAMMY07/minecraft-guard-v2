from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VisualFeatures:
    average_brightness: float
    very_dark_ratio: float
    greenish_ratio: float
    gray_ratio: float
    red_text_ratio: float
    orange_text_ratio: float
    bright_text_ratio: float
    bottom_red_ratio: float
    bottom_dark_ratio: float
    bottom_gray_ratio: float
    bottom_slot_score: float
    chat_band_score: float
    right_scoreboard_score: float
    edge_density: float | None
    dominant_bucket: str

    def as_dict(self) -> dict[str, Any]:
        return {key: round(value, 3) if isinstance(value, float) else value for key, value in asdict(self).items()}


def extract_visual_features(image_path: str | Path, sample_size: tuple[int, int] = (160, 90)) -> VisualFeatures:
    from collections import Counter

    from PIL import Image  # type: ignore

    with Image.open(image_path) as image:
        image = image.convert("RGB").resize(sample_size)
        width, height = image.size
        pixels = list(image.getdata())

    if not pixels:
        raise ValueError("empty_image")

    brightness = [sum(pixel) / 3 for pixel in pixels]
    very_dark = ratio(brightness, lambda value: value < 35)
    greenish = ratio(pixels, lambda pixel: pixel[1] > pixel[0] + 25 and pixel[1] > pixel[2] + 10)
    gray = ratio(pixels, lambda pixel: abs(pixel[0] - pixel[1]) < 12 and abs(pixel[1] - pixel[2]) < 12 and 60 < pixel[0] < 200)
    red_text = ratio(pixels, lambda pixel: pixel[0] > 150 and pixel[1] < 95 and pixel[2] < 95)
    orange_text = ratio(pixels, lambda pixel: pixel[0] > 175 and 60 < pixel[1] < 160 and pixel[2] < 95)
    bright_text = ratio(pixels, lambda pixel: pixel[0] > 180 and pixel[1] > 180 and pixel[2] > 180)
    bottom_pixels = crop_pixels(pixels, width, height, 0.0, 0.72, 1.0, 1.0)
    bottom_red = ratio(bottom_pixels, lambda pixel: pixel[0] > 140 and pixel[1] < 85 and pixel[2] < 85)
    bottom_dark = ratio(bottom_pixels, lambda pixel: pixel[0] < 55 and pixel[1] < 55 and pixel[2] < 55)
    bottom_gray = ratio(bottom_pixels, lambda pixel: abs(pixel[0] - pixel[1]) < 16 and abs(pixel[1] - pixel[2]) < 16 and 50 < pixel[0] < 210)
    chat_pixels = crop_pixels(pixels, width, height, 0.0, 0.70, 0.55, 0.96)
    right_pixels = crop_pixels(pixels, width, height, 0.72, 0.18, 0.99, 0.75)
    color_bucket = Counter("green" if pixel[1] > pixel[0] + 25 and pixel[1] > pixel[2] + 10 else "gray" if abs(pixel[0] - pixel[1]) < 12 and abs(pixel[1] - pixel[2]) < 12 else "other" for pixel in pixels)
    return VisualFeatures(
        average_brightness=sum(brightness) / len(brightness),
        very_dark_ratio=very_dark,
        greenish_ratio=greenish,
        gray_ratio=gray,
        red_text_ratio=red_text,
        orange_text_ratio=orange_text,
        bright_text_ratio=bright_text,
        bottom_red_ratio=bottom_red,
        bottom_dark_ratio=bottom_dark,
        bottom_gray_ratio=bottom_gray,
        bottom_slot_score=slot_score(bottom_pixels),
        chat_band_score=text_band_score(chat_pixels),
        right_scoreboard_score=text_band_score(right_pixels),
        edge_density=edge_density(image_path),
        dominant_bucket=color_bucket.most_common(1)[0][0],
    )


def ratio(values: list[Any], predicate: Any) -> float:
    if not values:
        return 0.0
    return sum(1 for value in values if predicate(value)) / len(values)


def crop_pixels(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    left: float,
    top: float,
    right: float,
    bottom: float,
) -> list[tuple[int, int, int]]:
    x0 = max(0, min(width, int(width * left)))
    x1 = max(0, min(width, int(width * right)))
    y0 = max(0, min(height, int(height * top)))
    y1 = max(0, min(height, int(height * bottom)))
    return [pixels[y * width + x] for y in range(y0, y1) for x in range(x0, x1)]


def slot_score(pixels: list[tuple[int, int, int]]) -> float:
    dark = ratio(pixels, lambda pixel: pixel[0] < 55 and pixel[1] < 55 and pixel[2] < 55)
    gray = ratio(pixels, lambda pixel: abs(pixel[0] - pixel[1]) < 18 and abs(pixel[1] - pixel[2]) < 18 and 45 < pixel[0] < 210)
    red = ratio(pixels, lambda pixel: pixel[0] > 140 and pixel[1] < 90 and pixel[2] < 90)
    return min(1.0, dark * 1.8 + gray * 1.1 + red * 1.5)


def text_band_score(pixels: list[tuple[int, int, int]]) -> float:
    bright = ratio(pixels, lambda pixel: pixel[0] > 175 and pixel[1] > 175 and pixel[2] > 175)
    colored = ratio(
        pixels,
        lambda pixel: (pixel[0] > 150 and pixel[1] < 100 and pixel[2] < 100)
        or (pixel[0] > 170 and 70 < pixel[1] < 170 and pixel[2] < 100)
        or (pixel[2] > 145 and pixel[0] < 110),
    )
    dark = ratio(pixels, lambda pixel: pixel[0] < 45 and pixel[1] < 45 and pixel[2] < 45)
    return min(1.0, bright * 2.0 + colored * 2.0 + dark * 0.25)


def edge_density(image_path: str | Path) -> float | None:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        from PIL import Image  # type: ignore

        with Image.open(image_path) as image:
            gray = np.array(image.convert("L").resize((160, 90)))
        edges = cv2.Canny(gray, 80, 160)
        return float((edges > 0).sum() / edges.size)
    except Exception:
        return None
