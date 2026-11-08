# Canonical source and HADES deployment synchronization

## Canonical source

`p0rkm4th/hades-herd` is the only development source for the standalone
`codex-herd` client. Develop and review code here; do not make independent
feature edits in the private infrastructure repository.

## HADES workstation migration — completed 2026-11-07

The workstation helper now resolves to the canonical checkout in
`~/Workspaces/hades-herd/codex_herd.py`. Migration steps and verification:

1. The public repository was initialized, tested, and pushed before changing
   the active launcher.
2. Existing private files remain a read-only import snapshot; preserve
   their current contents and unrelated dirty work.
3. The user-config helper symlink points at the canonical
   `~/Workspaces/hades-herd/codex_herd.py` checkout.
4. The private Herd endpoint is set only in local Fish configuration via
   `CODEX_HERD_URL`; it is not part of public source or documentation.
5. The prior fleet digest evidence is stored in the private
   `~/.config/codex-herd/model-digests.json` with mode `0600`.
6. `codex-herd list` returned 7/7 online, an explicit
   `codex-herd qwen3.6:35b --help` forwarded to Codex without inference, and
   `codex-herd config show qwen3.6:35b` reported it remained the saved default.
   Roll back by restoring the retained helper symlink and Fish function backup.

The old private copy is an archival import snapshot, not an alternate source.
Future changes are made and tested here first; a specific public commit is
pulled into the canonical workspace checkout before use. No production provider
or model default was changed by this migration.

## Reviewed launcher active on workstation — 2026-11-08

The canonical checkout is now on public branch
`codex-herd/launcher-review-fixes` at `56e6ba8` after its 22-test suite passed
and its Python 3.10–3.14 CI matrix succeeded. This branch provides isolated
per-model Codex profiles. The installed Fish command was rechecked against the
live catalog; MiMo and Qwen report their saved 16K Codex context, and an
explicit Qwen `--help` launch reached Codex without starting inference. The
saved default remains `qwen3.6:35b`.

The matched real-inference launch smoke for MiMo and Qwen, plus the separate
0/3 fast-profile diagnostic task result, are recorded in
[`STATUS.md`](STATUS.md) and the linked benchmark reports. Level A is not met;
limit use to supervised, low-risk edits and switch explicitly to hosted Codex
when local work stalls. The review branch is published but not merged into
`main`.
