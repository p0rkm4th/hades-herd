"""CLI tool that reads a JSONL log file and prints a JSON summary."""

import json
import re
import sys
from datetime import datetime

VALID_LEVELS = ("INFO", "WARNING", "ERROR")

# ISO 8601 datetime with a required timezone: Z or +HH:MM / -HH:MM.
ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def parse_timestamp(value):
    """Return a valid ISO 8601 datetime, or ``None`` when it is not."""
    if not isinstance(value, str):
        return None
    if " " in value:
        return None
    if not ISO_RE.match(value):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def validate_record(record):
    """Return ``(level, service)`` for a valid record, or ``None`` otherwise."""
    if not isinstance(record, dict):
        return None
    timestamp, service, level, message = (
        record.get("timestamp"),
        record.get("service"),
        record.get("level"),
        record.get("message"),
    )
    if parse_timestamp(timestamp) is None:
        return None
    if not isinstance(service, str):
        return None
    if not isinstance(message, str):
        return None
    normalized = level.upper() if isinstance(level, str) else None
    if normalized not in VALID_LEVELS:
        return None
    return normalized, service


def analyze_file(path):
    """Read *path* and return ``(total, levels, errors_by_service, skipped)``."""
    total = 0
    levels = {name: 0 for name in VALID_LEVELS}
    errors_by_service = {}
    skipped = 0

    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise SystemExit(f"log_analyzer: cannot read '{path}': {exc}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"log_analyzer: '{path}' is not valid UTF-8: {exc}")

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue  # blank lines are ignored

        try:
            record = json.loads(stripped)
        except ValueError as exc:
            skipped += 1
            continue  # malformed JSON

        result = validate_record(record)
        if result is None:
            skipped += 1
            continue  # missing fields, wrong types, bad level

        level, service = result
        total += 1
        levels[level] += 1
        if level == "ERROR":
            errors_by_service[service] = errors_by_service.get(service, 0) + 1

    return total, levels, dict(sorted(errors_by_service.items())), skipped


def main(argv=None):
    if len(argv) != 2:
        print(f"usage: {argv[0]} <log.jsonl>", file=sys.stderr)
        return 2
    path = argv[1]
    total, levels, errors_by_service, skipped = analyze_file(path)
    print(
        json.dumps(
            {
                "total": total,
                "levels": levels,
                "errors_by_service": errors_by_service,
                "skipped": skipped,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))