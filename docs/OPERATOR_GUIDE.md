# Operator guide

## Configure the endpoint

Set `CODEX_HERD_URL` in local shell startup. Do not put a private endpoint in a
public config file. The helper rejects non-HTTP(S) origins, embedded
credentials, query strings, and fragments.

## Daily use

- `codex-herd list` shows live model names, hosting nodes, availability,
  loaded state, context metadata, tool evidence, and the saved default.
- `codex-herd MODEL` launches the exact live model through Herd.
- `codex-herd role fast|balanced|complex` launches that locally configured role.
- `codex-herd role long` launches the explicitly assigned Hecate MiMo 64K
  profile for longer inputs and bounded coding tasks.
- `codex-herd config` edits the default and supported per-model preferences.
- `codex-herd config role ROLE MODEL` maps a role to a live, tool-capable local model.
- `codex-herd config show MODEL` distinguishes the Codex context budget from
  observed backend allocation and model metadata.
- `codex-herd refresh` refreshes discovery and generated profile state.

Hermes aliases are configured locally, separately from its saved default.
Hermes Agent v0.23.0 requires at least 64K backend context, so `mimo-code`
selects the validated MiMo 64K profile. `hades-mimo-long` remains as a
compatibility alias:

```sh
hermes -m mimo-code chat
hermes -m hades-mimo-long chat
```

The previous `hades-mimo-fast` shortcut selected the 16K alias and failed
Hermes' 64K minimum-context check; it has been removed from active Hermes
configuration. The Codex 16K profile remains available through Codex-Herd.
The Codex catalog uses concise names such as `MiMo 9B | Coding (4/5) | 16K`;
the canonical backend slug remains the model ID used for requests. Neither
these names nor aliases change the saved Hermes/Codex model default.

The 64K shortcuts use the same canonical Hecate model ID. A bounded Codex task
completed with shell tools, a source edit, and 17 independently passing tests
in 41.27 s (first tool action 3.44 s). This is one task, not a broad reliability
claim; inspect the diff and test results. Codex command: `codex-herd role long`.

Unknown, offline, embedding-only, or ineligible models produce an error. The
helper does not download or substitute a model. User config is isolated under
`~/.config/codex-herd/`; hosted Codex settings remain separate.

Role assignments are stored only in local preferences and do not change the
saved default. Explicit model and role launches use model-isolated local
Responses profiles with Herd's no-fallback header.

The scoped local reliability benchmark selected MiMo-V2.6 9B Q4 at 16K: 4/5
verified fixture tasks, 100% GPU residency, and 23–107 seconds per full task.
Qwen3.8 27B Q4 at 64K failed to complete its smoke within 180 seconds and used
about 33% CPU residency. Its 32K/64K tag manifests were removed on 2026-11-10,
but the 64K runner remained loaded and appears in Herd without advertised tool
capability; do not select that stale entry. The Q4 base and 8K/16K tags remain.
Q3_K_M passed one same-task 8K coding screen faster than Q4 (63 s vs. 102 s),
but this is only a short-context Codex candidate and does not meet Hermes'
64K minimum. Map FAST, BALANCED, and bounded COMPLEX tasks to MiMo if desired;
this evidence does not establish long-context or broad repository reliability.
MiMo has failed separate diagnostic maintenance tasks in prior campaigns, so
inspect every diff and test result. See the [local reliability
scorecard](../benchmarks/results/local-model-reliability.md) and [Qwen3.8
cleanup result](../benchmarks/results/2026-11-10-qwen38-profile-cleanup.md).

## Recovery

If the saved default no longer exists, refresh reports the stale preference and
does not silently replace it. Select a discovered model explicitly or set a
new default with `codex-herd config MODEL`. For router outages, use a direct
Ollama endpoint only when that backend is reachable and allowed by local
policy. The helper itself does not change networking or services.

If a local session stalls or loops, press `Ctrl-C` to stop that Codex process,
review any partial work with `git diff` and the project tests, then start the
hosted Codex command explicitly with `codex` if you want to continue there.
The launcher never redirects a local task to hosted inference. Hosted Codex
configuration remains unchanged.

Stop a session that repeats inspections without editing, reaches two failed
test corrections, or approaches its 180-second task budget without a verified
change. These are operator stop cues, not automatic timeouts. Unsupported
tool errors and context exhaustion are reasons to stop and review the partial
diff rather than retry blindly.

For a locally enforced Codex-Herd run, use the supervisor from an isolated
worktree. It stops on wall time, tool count, repeated commands, consecutive
failed tools, or cumulative token usage reported by Codex events. JSONL logs
and a mode-0600 recovery checkpoint remain in a mode-0700 directory; inspect
the partial worktree before resuming. Token limits can only be enforced when
the backend reports usage events.

```sh
python3 /path/to/hades-herd/scripts/codex_herd_supervisor.py \
  --workspace "$PWD" --goal "Fix the fixture defect" \
  --acceptance "pytest passes and only the target file changes" \
  --wall-seconds 180 --max-tool-calls 24 --max-identical 2 \
  --max-failures 2 --max-tokens 500000 -- \
  codex-herd role balanced exec --json --sandbox workspace-write \
  "Fix the defect and run the focused test."
```

The checkpoint records started/completed tool actions, changed paths, and the
latest failed test output. It does not restore an agent session or certify
completion; independently inspect the diff and rerun acceptance tests.

## Verify

```sh
python3 -m unittest discover -s tests -v
codex-herd list
codex-herd MODEL --help
```

`--help` forwarding checks Codex argument routing, not inference or task
completion. Use the acceptance definitions in [benchmark methodology](../benchmarks/README.md).

## Opt-in Hermes profiles

The matched five-fixture comparison found MiMo 9B 64K faster (4/5, mean 36.7 s) and Qwen3.5 9B 64K slower but passing all external checks (5/5; strict terminal-tool compliance 4/5). These are supervised candidates, not unattended-driver qualifications. Launch explicitly with `hermes -m mimo-code --provider localherd` or `hermes -m qwen35 --provider localherd`. Do not change the saved default based on this small sample. The Qwen alias uses existing weights and is 100% GPU resident at 64K; its 128K profile offloaded to CPU and failed marker retrieval. Full evidence: [matched report](../benchmarks/results/2026-11-09-hermes-qwen35-mimo-comparison.md).

The HADES environment also has an explicit opt-in `qwen36` Hermes alias for
`qwen3.6:35b` (`hermes -m qwen36 chat`). Herd currently reports a 65,536-token
allocation, but this model has not passed a Hermes coding acceptance run and
is not assigned a qualified coding role. Keep the saved default unchanged.

No local model is currently qualified as a SECURITY-LAB profile. Do not treat
uncensored behavior or a benign tool smoke as evidence of security expertise;
use no model for security analysis without a passing evidence-based accuracy
fixture. The latest DeepHat candidate failed its CVE and Sigma checks; see the
[screen report](../benchmarks/results/2026-11-09-deephat-security-screen.md).
