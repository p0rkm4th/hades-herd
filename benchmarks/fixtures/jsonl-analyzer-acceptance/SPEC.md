# Original JSONL analyzer acceptance contract

This is the shared black-box contract for the two independently written analyzer implementations recorded in the 2026-11-09 scorecard. It covers the original one-path CLI only. The separate `jsonl-strict-cli` fixture covers the optional `--strict` extension and is not part of this comparison.

The base check uses UTC `Z` timestamps and tests the shared CLI behavior. A second, separate check asserts that numeric ISO-8601 offsets such as `+00:00` are valid. For a supplied UTF-8 JSONL path, print a JSON object with exactly `total`, `levels`, `errors_by_service`, and `skipped`. Recognize INFO/WARNING/ERROR case-insensitively; count valid records only; count malformed or invalid nonblank records as skipped; ignore blank lines; group ERROR counts by service with deterministic key order. Invalid UTF-8 and unreadable/missing paths must fail nonzero. No input file may be modified.
