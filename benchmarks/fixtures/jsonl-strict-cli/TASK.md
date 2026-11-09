# Local coding smoke fixture: strict JSONL mode

## Task

Add an optional `--strict` CLI flag to `log_analyzer.py` while preserving the
existing one-path invocation and JSON summary. Strict mode must return status 1
when one or more malformed or invalid nonblank records were skipped, and status
0 when all records are valid. Missing/unreadable files and invalid UTF-8 must
remain nonzero errors. Do not change analysis/counting behavior or unrelated
files.

## Independent verification

```sh
python3 -m unittest discover -s . -v
python3 log_analyzer.py valid.jsonl
python3 log_analyzer.py --strict valid.jsonl
python3 log_analyzer.py --strict malformed.jsonl  # expected exit status 1
```

`baseline/log_analyzer.py` is the task starting point; `log_analyzer.py` is the
verified acceptance implementation. The Codex smoke used an equivalent
disposable fixture, baseline-failing strict checks, and an isolated local Codex profile. The recorded completion metrics
are in `../../results/2026-11-09-agent-profile-context.md`.
