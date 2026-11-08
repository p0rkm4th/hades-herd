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

Apply only in a disposable clone of the exact upstream commit:

```sh
git checkout e0dac345515e8423e385ea2d465573a1e8b5a1bf
git apply /path/to/hades-herd/benchmarks/fixtures/patches/herd-v0.12.3-empty-tools-guard.patch
```

Run the upstream translator tests, then the
[route probe](../probe_herd_empty_tools_route.py) with
`HERD_EMPTY_TOOLS_EXPECTED=guard`. The route probe also passes on unmodified
v0.12.3 with `HERD_EMPTY_TOOLS_EXPECTED=stock`.
