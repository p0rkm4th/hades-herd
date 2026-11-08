# Concurrent Codex profile generation check

## Question

The source review asked whether simultaneous `codex-herd` launches could mix
model-specific profile settings or leave generated profile/catalog files
incomplete.

## Method

An offline regression test starts two concurrent calls to `sync_catalog` from
a barrier, with the same configured Codex home and distinct models, developer
instructions, profile paths, and catalog paths. It verifies that each profile
references its own model and catalog, and that both generated catalogs and the
shared inventory remain parseable JSON. No inference endpoint is used.

## Result

The synchronized test passed. This exercised concurrent profile generation
in one process and found no cross-model profile mix-up; the model-specific
paths and atomic profile replacement were sufficient, so no implementation
change was needed. The complete client suite passed **21 tests**, and
`git diff --check` passed.

This does not test Codex processes racing during startup or prove behavior for
every filesystem. The generated profile/catalog names are deterministic per
model, and each file is written through a same-directory temporary file plus
atomic replacement.

An earlier bounded Codex attempt to create this regression test timed out and
left an invalid test: it changed module-global paths independently inside
worker threads and registered malformed cleanup callbacks. That candidate was
discarded. The passing test here uses one shared configuration and a
synchronized start; the failed agent attempt is not a product failure or a
model-quality score.
