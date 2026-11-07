# Contributor instructions

- Keep this repository as the canonical source for the `codex-herd` client.
- Never add private HADES inventories, hostnames, network addresses, credentials,
  local preference files, raw inference transcripts, or unreviewed task artifacts.
- Use `CODEX_HERD_URL` for deployment-specific endpoints; do not hardcode a
  private endpoint in source or examples.
- Preserve the no-download/no-hosted-fallback behavior and generated profile
  isolation. Do not weaken Codex sandbox settings.
- Add offline tests for client changes. Run `python3 -m unittest discover -s
  tests -v` and `git diff --check` before publishing.
- Benchmark claims must link to sanitized evidence and distinguish agent
  completion from a patch that needed human correction.
- Do not change the HADES production provider or default model from this project.
