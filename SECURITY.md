# Security policy

## Data handling

Do not commit API keys, passwords, access tokens, SSH keys, `~/.config/codex-herd`
contents, generated Codex profiles/catalogs, raw prompts, or raw inference logs.
Use placeholders and sanitized, task-level summaries in public reports. Review
all changed files and the Git diff before pushing.

The client generates local configuration with mode `0600`. That configuration
can contain model inventory and the selected endpoint. Keep it on the trusted
client and do not publish it.

## Network boundary

This client does not authenticate to Herd. Restrict the Herd API to authorized
clients with the deployment's firewall or reverse-proxy allowlist. Prefer a
trusted LAN or authenticated private tunnel. Do not expose the API directly to
the public Internet. The fallback URL is loopback; operators must set
`CODEX_HERD_URL` explicitly for a remote router.

## Inference safety

The helper does not pull weights or silently switch to hosted inference. Keep
Codex sandboxing enabled. Review model-generated changes before applying them
outside a disposable workspace.

## Reporting

For a vulnerability in this client, do not publish credentials or sensitive
network details in an issue. Contact the repository owner privately through
GitHub's security reporting mechanism if one is enabled; otherwise request a
private channel before sharing exploit details.
