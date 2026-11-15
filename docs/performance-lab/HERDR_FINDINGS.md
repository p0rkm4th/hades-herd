# Herdr orchestration findings

Two local Hermes workers were launched in separate assigned panes with explicit
working directories and local model aliases. Startup banners and live model
digests confirmed Qwen3.5 on one node and MiMo on another; global Hermes
fallbacks were empty.

Both initial prompt-with-wait calls returned a stalled-state error even though
the prompt appeared in the pane and tool activity followed. Herdr also showed
idle while the terminal displayed active tool work. Inspect the same pane and
artifact before any retry; do not duplicate the task based on a stalled wait.

The completed cohort had one Qwen task that ran about 18 minutes with repeated
edits and three compactions, and one MiMo task that ran about 14 minutes and
did not self-validate. Both read outside their assigned directories. MiMo also
generated a persistent skill outside its task workspace. No outside code edits
were accepted. A global snapshot later reported one in-flight item while both
Herdr workers were idle and Ollama active-request telemetry was zero; these
counters do not agree and should not be conflated.

Herdr cwd is not a filesystem sandbox. Require an OS-level boundary for future
workers, verify tool output and file scope, inspect after three minutes without
progress, checkpoint after two compactions, and allow no more than two
corrective retries. Interrupt an unproductive active task with the documented
agent Ctrl+C control while preserving its pane and files. Both current workers
are idle; no worker task remains active.

## Wrapped Hermes route isolation

Herdr does not yet recognize the bubblewrap-wrapped Hermes process as a normal
agent: its pane is `unknown`. For these sessions, the supervisor verified the
pane's foreground process and input prompt, submitted one task once through the
pane, and checked both response output and post-run audit evidence. A stalled
prompt wait was not used as a reason to resubmit.

The local launcher now hides the host home, makes only the assigned task
workspace writable, and disables network egress in a separate network
namespace. A loopback-only alias forwards into a Unix-socket bridge that allows
only the selected local model catalog and chat-completions routes. Five offline
integration tests passed; no-tools Qwen3.6 smoke requests succeeded on the
configured local route and an already-resident local inference node. This is
route evidence, not a malicious-agent security audit or a model-quality result.
Use non-sensitive task data until broader isolation review is complete.

## One-shot task lifecycle

The same sandbox now accepts a task contract through a separate read-only
mount, rejects dirty workspaces and Git metadata outside the assigned project,
and retains the result log, exit status, usage, and bridge audit. Nine offline
checks cover the workspace boundary, local-only network path, contract mount,
and captured process exit status. In one observed run, the initial bounded
output wait expired while the local task was still running; inspection found
the same process active, and it completed without a duplicate prompt. This
confirms that a wait timeout must be followed by inspection, not automatic
resubmission. The task succeeded independently, but the sample is too small to
estimate reliability.
