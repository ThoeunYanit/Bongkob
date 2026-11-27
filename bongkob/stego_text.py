"""Text carrier: zero-width characters between words.

U+200B (zero-width space)      = bit 0
U+200C (zero-width non-joiner) = bit 1

The bits are spread evenly across the gaps between words, so the visible
text is exactly the cover the user typed, with no repetition or padding.
"""

import numpy as np

from .bits import CapacityError, capacity_bytes, frame, unframe

ZERO = "\u200b"
ONE = "\u200c"

MESSAGE_LIMIT = 4096  # Telegram's maximum length for one text message


def message_length(text: str) -> int:
    """Length as Telegram counts it (UTF-16 code units; an emoji counts as 2)."""
    return len(text.encode("utf-16-le")) // 2


def capacity(cover: str) -> int:
    """How many payload bytes fit in one Telegram message with this cover (8 characters per byte)."""
    return capacity_bytes(max(0, MESSAGE_LIMIT - message_length(cover.strip())))


def hide(cover: str, payload: bytes) -> str:
    if len(payload) > capacity(cover):
        raise CapacityError(
            f"A Telegram message fits {capacity(cover)} bytes with this cover; the secret needs {len(payload)}."
        )
    bits = "".join(ONE if b else ZERO for b in frame(payload))
    words = cover.strip().split(" ")
    if len(words) == 1:
        return words[0] + bits

    gaps = len(words) - 1
    per_gap = -(-len(bits) // gaps)  # ceiling division
    parts = []
    for i, word in enumerate(words):
        parts.append(word)
        if i < gaps:
            parts.append(bits[i * per_gap:(i + 1) * per_gap])
            parts.append(" ")
    return "".join(parts)


def extract(stego: str) -> bytes:
    bits = np.array([1 if ch == ONE else 0 for ch in stego if ch in (ZERO, ONE)], dtype=np.uint8)
    return unframe(bits)


def visible(stego: str) -> str:
    """The text a human sees (zero-width characters removed)."""
    return stego.replace(ZERO, "").replace(ONE, "")