# Experimental Ollama Herd patch

`herd-v0.12.3-empty-tools-guard.patch` is a change-only prototype against
Ollama Herd commit `e0dac345515e8423e385ea2d465573a1e8b5a1bf` (v0.12.3).
It preserves whether the offered-tool set is explicitly empty, suppresses
unadvertised tool calls in both streamed and non-streamed Responses, and adds
translator regression tests. It does not change routing, model selection, or
Ollama configuration.

The upstream project is distributed under the MIT license. Its notice is
included in [`OLLAMA-HERD-MIT-LICENSE.txt`](OLLAMA-HERD-MIT-LICENSE.txt).
The patch remains experimental and has not been submitted upstream or applied
to the production router.

`herd-v0.12.3-empty-response-failure.patch` is a separate candidate for a
different adapter behavior. When Ollama reports `done:true` without visible
text or tool calls, stock Herd returns a successful empty Responses object;
Codex 0.166.0 treats that as a successful blank turn. The candidate instead
returns a failed Responses result with an explicit empty-output error, while
preserving the existing `incomplete` status for length-limited generations.
It changes no routing or Ollama settings. Tests show Codex surfaces the error
and exits the turn with status 1 rather than silently completing, but it does
not recover or retry automatically. The patch is not applied to production and
has not been submitted upstream.

Apply it only in a disposable checkout of the exact v0.12.3 commit, then run:

```sh
git apply /path/to/hades-herd/benchmarks/fixtures/patches/herd-v0.12.3-empty-response-failure.patch
uv sync --extra dev
HERD_EMPTY_RESPONSE_EXPECTED=failure PYTHONPATH=src:. uv run pytest \
  tests/test_server/test_responses_translator.py \
  tests/test_server/test_responses_empty_completion_diagnostic.py \
  /path/to/hades-herd/benchmarks/fixtures/probe_herd_thinking_only_route.py -q
HERD_EMPTY_RESPONSE_EXPECTED=failure PYTHONPATH=src:. uv run pytest -q
```

Apply only in a disposable clone of the exact upstream commit:

```sh
git checkout e0dac345515e8423e385ea2d465573a1e8b5a1bf
git apply /path/to/hades-herd/benchmarks/fixtures/patches/herd-v0.12.3-empty-tools-guard.patch
```

Run the upstream translator tests, then the
[route probe](../probe_herd_empty_tools_route.py) with
`HERD_EMPTY_TOOLS_EXPECTED=guard`. The route probe also passes on unmodified
v0.12.3 with `HERD_EMPTY_TOOLS_EXPECTED=stock`.
