# Canonical source and HADES deployment synchronization

## Canonical source

`p0rkm4th/hades-herd` is the only development source for the standalone
`codex-herd` client. Develop and review code here; do not make independent
feature edits in the private infrastructure repository.

## HADES workstation migration

The workstation currently reaches the helper through
`~/.config/codex-herd/codex_herd.py`, which historically pointed into the
private `HADES/infra/clients/codex-herd/` snapshot. The migration plan is:

1. Initialize and test this public repository without changing the active
   launcher.
2. Keep the existing private files as a read-only import snapshot; preserve
   their current contents and unrelated dirty work.
3. After the initial public commit is verified, point the user-config helper
   symlink at the canonical `~/Workspaces/hades-herd/codex_herd.py` checkout.
4. Keep the private Herd endpoint only in the workstation's Fish configuration
   via `CODEX_HERD_URL`; it is not part of public source or documentation.
5. Verify `codex-herd list`, an explicit `--help` launch, and the saved default.
   Roll back by restoring the recorded symlink target and Fish function.

The old private copy is then an archival import snapshot, not an alternate
source. Future changes are made and tested in this repository first; a specific
public commit is pulled into the canonical workspace checkout before use. No
production provider or model default is changed by this migration.
