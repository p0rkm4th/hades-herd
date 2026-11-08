"""Small HTTP header utilities."""

def merge_headers(headers):
    """Merge repeated header names while preserving insertion order."""
    merged = {}
    for name, value in headers:
        merged[name] = value
    return list(merged.items())
