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
