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
