"""Hashing utilities for entropy generation."""
import hashlib
import struct
import time


def hash_text(text: str, algorithm: str = "sha256") -> bytes:
    """Hash a text string using the specified algorithm.
    
    Args:
        text: The input text to hash.
        algorithm: The hashing algorithm to use (default: sha256).
        
    Returns:
        The raw hash bytes.
    """
    h = hashlib.new(algorithm)
    h.update(text.encode("utf-8"))
    return h.digest()


def hash_combined(*args, algorithm: str = "sha256") -> bytes:
    """Hash multiple arguments together.
    
    Args:
        *args: Arguments to hash (str, int, float, or bytes).
        algorithm: The hashing algorithm to use (default: sha256).
        
    Returns:
        The raw hash bytes.
    """
    h = hashlib.new(algorithm)
    for arg in args:
        if isinstance(arg, str):
            h.update(arg.encode("utf-8"))
        elif isinstance(arg, (int, float)):
            h.update(struct.pack("!d", arg))
        elif isinstance(arg, bytes):
            h.update(arg)
    return h.digest()


def hash_to_int(hash_bytes: bytes) -> int:
    """Convert hash bytes to an integer.
    
    Args:
        hash_bytes: The raw hash bytes.
        
    Returns:
        The integer representation of the hash.
    """
    return int.from_bytes(hash_bytes, byteorder="big")


def hash_to_range(hash_bytes: bytes, low: int, high: int) -> int:
    """Map hash bytes to a number within a specified range.
    
    Args:
        hash_bytes: The raw hash bytes.
        low: The minimum value (inclusive).
        high: The maximum value (inclusive).
        
    Returns:
        A number between low and high.
    """
    val = hash_to_int(hash_bytes)
    return low + (val % (high - low + 1))


def generate_seed(question: str, timestamp: float | None = None) -> int:
    """Generate a deterministic seed from a question and optional timestamp.
    
    Args:
        question: The input question text.
        timestamp: Optional timestamp for additional entropy.
        
    Returns:
        A deterministic seed integer.
    """
    if timestamp is None:
        timestamp = time.time()
    combined = f"{question}|{timestamp}"
    h = hash_text(combined)
    return hash_to_int(h)


def text_to_numeric_vector(text: str) -> list[int]:
    """Convert text to a list of character codes.
    
    Args:
        text: The input text.
        
    Returns:
        List of Unicode code points for each character.
    """
    return [ord(c) for c in text]


def text_to_bitstream(text: str) -> list[int]:
    """Convert text to a binary bitstream.
    
    Args:
        text: The input text.
        
    Returns:
        List of bits (0s and 1s).
    """
    bits = []
    for byte in text.encode("utf-8"):
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def hash_timestamp(timestamp: float) -> bytes:
    """Hash a timestamp value."""
    return hash_combined(str(timestamp))
