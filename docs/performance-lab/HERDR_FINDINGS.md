# Herdr orchestration findings

Two local Hermes panes were created with separate, explicit project working directories and model aliases routed to separate local inference nodes. The Herdr panes reported the assigned cwd and the Hermes startup banners showed the requested model aliases.

Both initial `agent prompt --wait` calls returned a stalled-state error even though the prompt text appeared in the terminal and tool activity followed. Herdr continued to report `idle` while the visible terminal showed active work. Treat `idle` and a stalled wait as insufficient completion evidence; inspect pane output and verify the artifact before deciding whether a task is finished. Do not resubmit the same task blindly.

A fleet snapshot during worker execution showed two in-flight agent tasks while Ollama active-request telemetry was zero. These counters have different semantics and should not be conflated.

The first workers also attempted to read outside their assigned task directories; no out-of-scope edits were observed. Provide the needed input schema in the task prompt and audit filesystem scope independently. Results remain pending until supervisor acceptance.
