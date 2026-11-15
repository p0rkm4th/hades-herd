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
and retains a live run status, result log, exit status, usage, and bridge audit.
Fourteen offline checks cover the workspace boundary, local-only network path,
contract mount, model selection, node queue checks, and captured process exit
status. In one observed run, the initial bounded
output wait expired while the local task was still running; inspection found
the same process active, and it completed without a duplicate prompt. This
confirms that a wait timeout must be followed by inspection, not automatic
resubmission. The task succeeded independently, but the sample is too small to
estimate reliability.

Automatic selection uses task role, Herd's per-node queues and free slots, exact
resident model state, and digest verification. Per-node locks prevent this
sandbox from running two tasks against one node while permitting independent
nodes. It selects only warm models and uses the local router; it does not retry
failed work on another model after inference begins. A quick Qwen3.5 task and a
documentation MiMo task were selected without choosing a model manually. The
MiMo run exposed a token-accounting gap: chat responses succeeded but its usage
report contained no token counts. Current task-type classification is a small
keyword heuristic, and simultaneous multi-node task execution remains
unverified.

One later validation-heavy Qwen3.6 task produced 13 local chat-completion
requests (12 upstream HTTP 200) over 7.4 minutes but no terminal output or
finalized usage report. The worker created a large draft whose 47-test suite
had 32 failures. Independent review rejected the result; this is a local-model
task failure, not evidence of a Herdr submission failure. Do not confuse the
launcher heartbeat with work progress: the operator view reports heartbeat age
separately from last worker-output age. A SIGINT exit of `-2` is now normalized
to terminal state `interrupted` with exit 130.

## Acceptance and intervention

One-shot tasks can carry a strict manifest of bounded argv commands. Checks
run only after the worker exits successfully, in a copied workspace with
network access disabled; status shows each check as it runs. On the tested
fixture, all 12 tests passed and the source task workspace remained unchanged.
Inspect after three minutes without an artifact change, stop repeated repair
loops, checkpoint after two context compactions, and cap corrective retries at
two. Close finished panes while retaining their workspace and run artifacts.

The one-shot status view originally exposed a heartbeat but no sign of silent
file edits. It now samples Git's changed-path list on existing heartbeat
intervals and reports only a bounded set of relative paths, total count, and
last-change time. It excludes file contents and workspace roots. Offline tests
cover a silent writer and path redaction. This is evidence of workspace
activity, not a completion or quality signal; continue checking acceptance
results and the actual task diff.

In a separate bounded shim change, the local worker edited one file and then
exited with code 2 after reporting an iteration limit. The status artifact
showed the edit despite silent output; post-task acceptance correctly remained
pending because the worker did not exit successfully. The supervisor inspected
the exact diff, made a small correction, and ran the manifest in an isolated
networkless snapshot. Treat worker exit and acceptance state as separate
signals; do not infer successful completion from observed file activity.

## Second bounded engineering pair

Two local workers ran in a single row beneath the supervisor, on separate
verified local inference nodes and in OS-isolated assigned workspaces. The
Qwen3.6 classifier worker completed in 185 seconds and its six tests passed;
independent review found a regression that treated “patch” as implementation
intent. The supervisor added a narrow fix and regression check; the corrected
seven-test worker suite and 49-test lab suite passed. The Qwen3.5 natural
language CLI worker stopped at its 12-turn limit after 163 seconds, before its
acceptance manifest ran. Its partial implementation failed review and remains
preserved without a rewrite.

Herdr's generic agent list still reports wrapped Hermes panes as unknown. The
sandbox status artifact and pane output established terminal state, while the
heartbeat alone did not. Both panes were closed after preserving evidence and
confirming terminal states. Continue checking pane output and sandbox status,
inspect after three minutes without meaningful progress, and do not resubmit on
a stalled or unknown lifecycle result.

## Worker recovery checkpoint

Independent mock checks reconfirmed the Qwen3.5 prefix probe's privacy,
ordering, and append defects. The corrected MiMo summarizer passed a synthetic
offline acceptance check; its completion remains supervisor-assisted. A
separate Qwen3.6/Tartarus CLI task made three successful local completion
requests but produced no output or workspace edits. After checking bridge
activity and preserving run evidence, the supervisor interrupted it at
281.9 seconds. The sandbox recorded exit 130 and pending acceptance. Cause is
uncertain; this is not classified as a model failure. The worker pane was
closed after the process returned to shell, leaving the supervisor alone.

Provisional lifecycle: verify model/digest/capacity/workspace, submit once,
inspect artifacts after three minutes without meaningful progress, stop
repeated same-issue edits, checkpoint after two context compactions, and allow
at most two evidence-backed corrections. Close a pane only after terminal
state and evidence are preserved. These are starting guardrails, not calibrated
model timeouts.

## Inference activity versus task progress

Two wrapped Hermes runs showed a mismatch between Herdr/Herd in-flight counts
and serving-runtime active-request telemetry. The sandbox bridge audit
confirmed that local completion requests had occurred, but its event log was
only finalized at task end. The lab status tool now exposes aggregate local
completion and upstream-response counts plus age of the latest request. It
never includes prompts, responses, endpoints, or raw event data. Request age
does not reset the productive-output staleness clock; acceptance and workspace
changes remain the completion signals. Fifty-five offline tests pass for the
private harness implementation. Do not treat queue counters, heartbeats, or
request activity alone as proof of task progress.
