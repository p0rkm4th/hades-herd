# Header merge protocol control

A compact isolated Codex task used as a protocol control, not as a model
benchmark. The baseline intentionally fails three of six tests. The task asks
for a case-insensitive merge that preserves the first spelling and position,
adds regression coverage, and runs the suite.

Run the baseline with:

```sh
python3 -m unittest discover -s tests -v
```

Initial source snapshot SHA-256:

- `AGENT_TASK.md`: `9a4eb092665a4224d037ddbe12ead6da0328c2ba0f596966c356e8436c088ef7`
- `headerlib.py`: `c74a8659455f52be4c978dd13d3863ec8e1b87c16d71d0a68f779ee347ce9ad0`
- `tests/test_headerlib.py`: `e56b5ec08126141e20b27f3b113e3bee2819a95e2938e4289160acef280474c2`

The observed run is documented in
[`full-tools protocol control`](../../../results/2026-11-08-full-tools-protocol-control.md).

The task fixture contains no external source code or private infrastructure
configuration. Its result is recorded separately and is not included in any
model leaderboard or daily-driver score.
