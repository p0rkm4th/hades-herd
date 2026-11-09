"""Command-line JSONL log analyzer.

Reads one JSON object per line from a JSONL file, validates each record,
and reports severity counts, ERROR counts grouped by service, and the
number of records that had to be skipped.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VALID_LEVELS = ("INFO", "WARNING", "ERROR")

#: ISO 8601 timestamps with a required timezone designator.  ``Z`` and
#: ``+HH:MM``/``-HH:MM`` forms are accepted; naive timestamps are rejected.
_TIMESTAMP_PATTERN = re.compile(
    r"""^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?[zZ]$"""
)


def _is_valid_timestamp(value: object) -> bool:
    """Return whether ``value`` is a valid ISO 8601 timestamp with timezone."""
    if not isinstance(value, str):
        return False
    if not value.endswith(("Z", "z")):
        return False
    if not _TIMESTAMP_PATTERN.fullmatch(value):
        return False
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        datetime.fromisoformat(normalized)
        return True
    except (ValueError, OverflowError):
        return False


def _parse_timestamp(value: object) -> datetime:
    """Parse a validated timestamp string into a :class:`datetime`."""
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    if value.endswith("Z"):
        normalized = value[:-1] + "+00:00"
    else:
        normalized = value
    return datetime.fromisoformat(normalized)


def _is_valid_record(record: object) -> Tuple[bool, Optional[dict]]:
    """Validate one parsed JSON record.

    Returns ``(is_valid, normalized_record)``.  ``normalized_record`` is
    ``None`` when the record is invalid; otherwise it contains the
    validated fields with the severity normalized to uppercase.
    """
    if not isinstance(record, dict):
        return False, None

    timestamp = record.get("timestamp")
    service = record.get("service")
    level = record.get("level")
    message = record.get("message")

    if not _is_valid_timestamp(timestamp):
        return False, None
    if not isinstance(service, str):
        return False, None
    if not isinstance(level, str):
        return False, None
    if not isinstance(message, str):
        return False, None
    if level.upper() not in VALID_LEVELS:
        return False, None

    return True, {
        "timestamp": timestamp,
        "service": service,
        "level": level.upper(),
        "message": message,
    }


def analyze_jsonl(path: str) -> Dict[str, object]:
    """Analyze a JSONL file and return the summary dictionary."""
    counts = {level: 0 for level in VALID_LEVELS}
    errors_by_service: Dict[str, int] = {}
    skipped = 0

    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except ValueError:
                skipped += 1
                continue

            _, normalized = _is_valid_record(record)
            if normalized is None:
                skipped += 1
                continue

            counts[normalized["level"]] += 1
            if normalized["level"] == "ERROR":
                errors_by_service[normalized["service"]] = errors_by_service.get(
                    normalized["service"], 0
                ) + 1

    return {
        "total": sum(counts.values()),
        "levels": counts,
        "errors_by_service": dict(sorted(errors_by_service.items())),
        "skipped": skipped,
    }


def _write_summary(summary: Dict[str, object]) -> None:
    print(json.dumps(summary, indent=2, sort_keys=True))


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for ``log_analyzer``."""
    if not argv:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("usage: log_analyzer <jsonl_file>", file=sys.stderr)
        return 2

    path = Path(argv[0])
    try:
        summary = analyze_jsonl(str(path))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 1

    _write_summary(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
