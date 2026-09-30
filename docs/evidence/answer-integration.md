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

The first complete Activity tests passed cancellation, recreation, reuse and
unsupported abstention, but the 135M model produced no answer passing the unchanged
citation gate. Qwen2.5-0.5B-Instruct Q4_K_M (491,400,032 bytes, pinned separately in
`tools/answers/model.env`) was then tested against the same frozen questions;
it also omitted citations and produced inaccurate text under a user-only prompt.
Both raw failures are preserved under `docs/evidence/answer-integration/`.
The next implementation separates trusted system instructions from evidence and
question content using the model's own chat template. Citation checks are unchanged.

The first UI script also exposed two test-harness issues: the additional
instrumentation manifest entry was not registered, and a repeat file-picker run
selected the background Downloads breadcrumb instead of the open drawer item.
Those failed runs remain in ignored `downloads/answers/smoke-20260930T222713-2`
and `downloads/answers/smoke-20260930T222814-2`. Explicit runner selection and drawer
selection are implemented. Native import/restart/source-dialog checks have passed.

The system-role change passed the production Activity suite and the full acceptance
script for APK `522de75783f6bd1d798aa47de0f30ce656e8ba9ab91a8b6ec247366c9d53b372`.
One source-cited condensation answer was generated; the groundwater draft correctly
became fallback. Its comparison remains incomplete and is not research acceptance.
A subsequent code review found and fixed a late-cancel UI publication race. A
regression guard now discards a completed result if cancellation arrives before
its UI callback. Empty-draft detection also uses the API-28-compatible trim/empty
check rather than the newer String.isBlank API. Final rerun is pending at this
checkpoint. Earlier successful traces and failed experiments remain preserved.
