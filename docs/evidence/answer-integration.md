# Answer integration evidence — task 020

Implementation checkpoint, validation in progress on LLMRig. No physical-device
or useful-research acceptance is claimed.

The coordinator-supervised `emulator-5560` is booted and reachable from the scoped
sandbox. Missing `/dev/kvm` inside that sandbox is no longer a blocker: the builder
neither launched another emulator nor altered a service. The existing native
verification passed again, with raw evidence in ignored
`downloads/runtime/verify-20260930T222004-6`. Prior failures remain untouched.

Public development cases were frozen before prompt changes in
`tools/answers/development-cases.json`, SHA-256
`1209c55fea82f39ebe2d22004b3b6cff259e55442d6f255a7dd9b884ee94ae75`.
They are integration cases, not a holdout or a research quality benchmark.

The implementation routes the main Answer offline action through retrieval,
coverage-based abstention, a real model chat template, and citation integrity
checks. Generated output, partial drafts, extractive fallback, abstention and
cancellation have distinct visible states. Invalid citations are not fabricated
or repaired by appending source IDs. Source inspection remains available.
Citation integrity checks do not establish semantic support for a claim.

The initial build and 12 synthetic-generator routing checks pass. The real-model
UI/Activity acceptance suite is running; no final pass is claimed yet.
