# Bounded Hermes Qwen3.5 profile smoke — 2026-11-10

This is separate from the five-task Hermes model comparison and long JSONL
benchmark. An opt-in profile selected Qwen3.5 9B Q4 at the existing 64K
Charon alias, used the local Herd provider, disabled fallback providers, and
enabled hard tool-loop stops. Its run budget was 180 seconds and its
per-conversation iteration limit was 30.

The profile ran the existing independent `bug_fix` fixture in a disposable
repository. It changed only the allowed `billing.py` implementation file;
independent pytest passed 6/6. The turn completed in 31 seconds with 11 tool
calls. First-tool latency and token usage were unavailable. This single smoke
does not qualify the profile for unattended work or prove the hard-stop
thresholds fire as configured. A separate harmless repeated-failure probe
stopped after 17 s with Hermes reporting `identical_call_streak_halt` (6 tool
calls). The runtime blocked its first command as dangerous, then halted the
identical-call streak. This verifies that runtime guard on this fixture, not
the profile's separate thresholds or 180 s deadline. No files were changed.

The backend reported 65,536 context, 100% GPU residency, and no CPU offload.
Herd had zero queued/in-flight requests after the run. The Hermes default
stayed MiMo 64K. The profile is local and user-specific; its launch wrapper is
`hadesqwen35 chat`, with explicit local routing and no hosted fallback.

Full private evidence, including invocation errors and rollback procedure, is
in the HADES infra acceptance report.
