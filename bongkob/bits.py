"""Bit helpers shared by all carriers.

Every carrier stores:  length (4 bytes, big-endian) | payload
Bits are ordered most significant bit first.
"""

import struct

import numpy as np

LENGTH_BITS = 32


class CapacityError(Exception):
    """The cover is too small for the payload."""


class NothingHidden(Exception):
    """No valid hidden payload was found."""


def frame(payload: bytes) -> np.ndarray:
    """Prefix the payload with its length and return it as an array of 0/1 bits."""
    data = struct.pack(">I", len(payload)) + payload
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def unframe(bits: np.ndarray) -> bytes:
    """Read the length prefix, then return exactly that many payload bytes."""
    if bits.size < LENGTH_BITS:
        raise NothingHidden()
    length = struct.unpack(">I", np.packbits(bits[:LENGTH_BITS].astype(np.uint8)).tobytes())[0]
    end = LENGTH_BITS + length * 8
    if length == 0 or end > bits.size:
        raise NothingHidden()
    return np.packbits(bits[LENGTH_BITS:end].astype(np.uint8)).tobytes()


def capacity_bytes(n_bits: int) -> int:
    """How many payload bytes fit in a carrier with n_bits usable bits."""
    return max(0, (n_bits - LENGTH_BITS) // 8)
