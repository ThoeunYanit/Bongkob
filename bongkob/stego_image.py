"""Image carrier: least significant bit (LSB) of each R, G, B value.

Changing the lowest bit moves a colour value by at most 1 out of 255, which
the eye cannot see. Output is always PNG, because lossy formats such as JPEG
would destroy the hidden bits.
"""

import io

import numpy as np
from PIL import Image

from .bits import CapacityError, capacity_bytes, frame, unframe

MAX_SIDE = 4000  # larger covers are scaled down to keep memory use bounded


def _load_cover(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    has_alpha = img.mode in ("RGBA", "LA") or "transparency" in img.info
    img = img.convert("RGBA" if has_alpha else "RGB")
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE))
    return img


def capacity(cover: bytes) -> int:
    img = _load_cover(cover)
    return capacity_bytes(img.width * img.height * 3)


def hide(cover: bytes, payload: bytes) -> bytes:
    img = _load_cover(cover)
    pixels = np.array(img)
    rgb = pixels[..., :3].reshape(-1)        # alpha channel is left untouched

    bits = frame(payload)
    if bits.size > rgb.size:
        raise CapacityError(
            f"This image holds {capacity_bytes(rgb.size)} bytes; the secret needs {len(payload)}."
        )
    rgb[:bits.size] = (rgb[:bits.size] & 0xFE) | bits
    pixels[..., :3] = rgb.reshape(pixels[..., :3].shape)

    out = io.BytesIO()
    Image.fromarray(pixels, img.mode).save(out, format="PNG", optimize=True)
    return out.getvalue()


def extract(stego: bytes) -> bytes:
    img = Image.open(io.BytesIO(stego))
    img = img.convert("RGBA" if img.mode in ("RGBA", "LA") else "RGB")
    rgb = np.array(img)[..., :3].reshape(-1)
    return unframe(rgb & 1)
