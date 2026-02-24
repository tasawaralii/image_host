import io
import json
import os
import uuid
from ast import literal_eval
from typing import Dict, Tuple

from PIL import Image


def save_image_variants(contents: bytes, upload_dir: str, resolutions: Dict[str, int]) -> Tuple[str, int, int, Dict[str, int]]:
    try:
        img = Image.open(io.BytesIO(contents))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
    except Exception:
        raise ValueError("Invalid image file")

    file_id = f"{uuid.uuid4()}.webp"
    original_width, original_height = img.size
    file_sizes: Dict[str, int] = {}

    for label, width in resolutions.items():
        target_width = min(width, original_width)
        w_percent = target_width / float(original_width)
        h_size = int(float(original_height) * float(w_percent))

        resized_img = img.resize((target_width, h_size), Image.Resampling.LANCZOS)
        file_path = f"{upload_dir}/{label}/{file_id}"
        resized_img.save(file_path, "WEBP", quality=80)
        file_sizes[label] = os.path.getsize(file_path)

    return file_id, original_width, original_height, file_sizes


def serialize_file_sizes(file_sizes: Dict[str, int]) -> str:
    return json.dumps(file_sizes)


def parse_file_sizes(raw_value: str) -> Dict[str, int]:
    try:
        return json.loads(raw_value)
    except Exception:
        return literal_eval(raw_value)


def build_urls(file_id: str, resolutions: Dict[str, int]) -> Dict[str, str]:
    return {label: f"/uploads/{label}/{file_id}" for label in resolutions.keys()}
