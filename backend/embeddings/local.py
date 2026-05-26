import hashlib
import math
import re

from backend.core.config import settings

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def embed_text(text: str) -> list[float]:
    vector = [0.0] * settings.vector_dim
    for token in TOKEN_RE.findall(text.lower()):
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % settings.vector_dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

