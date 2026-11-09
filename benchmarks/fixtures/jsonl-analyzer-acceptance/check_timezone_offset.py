#!/usr/bin/env python3
"""Independent acceptance check: ISO-8601 numeric timezone offsets are valid."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
script = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "offset.jsonl"
    path.write_text('{"timestamp":"2024-01-01T00:00:01+00:00","service":"api","level":"INFO","message":"ok"}\n', encoding="utf-8")
    run = subprocess.run([sys.executable, str(script), str(path)], capture_output=True, text=True, timeout=10)
    assert run.returncode == 0, run.stderr
    summary = json.loads(run.stdout)
    assert summary["total"] == 1 and summary["skipped"] == 0, summary
print("numeric timezone offset acceptance: PASS")
