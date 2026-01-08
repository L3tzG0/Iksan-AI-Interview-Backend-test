import re

def sanitize_name(name: str) -> str:
    """Strip whitespace, collapse spaces, and remove control characters."""
    if not name:
        return name
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", name)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()
