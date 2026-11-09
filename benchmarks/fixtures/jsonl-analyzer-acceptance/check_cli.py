#!/usr/bin/env python3
"""Independent black-box checks for the original JSONL analyzer contract."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

script = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    data = root / "mixed.jsonl"
    data.write_text("\n".join([
        '{"timestamp":"2024-01-01T00:00:00Z","service":"zeta","level":"ERROR","message":"e"}',
        '{"timestamp":"2024-01-01T00:00:01Z","service":"api","level":"info","message":"i"}',
        "not-json", "", '{"timestamp":"bad","service":"x","level":"WARNING","message":"w"}',
    ]), encoding="utf-8")
    before = data.read_bytes()
    result = subprocess.run([sys.executable, str(script), str(data)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    assert set(actual) == {"total", "levels", "errors_by_service", "skipped"}, actual
    assert actual == {
        "total": 2,
        "levels": {"INFO": 1, "WARNING": 0, "ERROR": 1},
        "errors_by_service": {"zeta": 1},
        "skipped": 2,
    }, actual
    assert data.read_bytes() == before, "input changed"

    missing = subprocess.run([sys.executable, str(script), str(root / "missing.jsonl")], capture_output=True, text=True, timeout=10)
    assert missing.returncode != 0, "missing path unexpectedly succeeded"
    invalid = root / "invalid.jsonl"
    invalid.write_bytes(b"\xff")
    bad_utf8 = subprocess.run([sys.executable, str(script), str(invalid)], capture_output=True, text=True, timeout=10)
    assert bad_utf8.returncode != 0, "invalid UTF-8 unexpectedly succeeded"
print("original JSONL CLI acceptance: PASS")
