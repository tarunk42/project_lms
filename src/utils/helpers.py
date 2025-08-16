import re
import hashlib

def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def sha256_text(s: str) -> str:
    """Generate a SHA-256 hash of the input string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def short(h: str, n: int = 8) -> str:
    """Shorten a hash to n characters."""
    return h[:n]
