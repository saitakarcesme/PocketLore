# Bootstrap evidence and limitations

The English baseline commit `aa075238571338f79df990fe4c28ffc3d14b6bf9` was pushed to the configured public origin and its hash matched the remote main ref. Independent review accepted repository setup only, under tag `accepted/bootstrap-baseline`.

## Implemented engineering checks

- Native Android source-inspection prototype with a generated eight-passage USGS pack; no model bundled, no INTERNET permission and no Google Play Services dependency.
- Five runner recovery unit checks, including reuse of a completed process receipt and recovery from a completed Codex turn before receipt persistence, plus an actual child-process crash between evidence chmod and atomic replacement.
- Actual systemd service restart with a changed supervisor PID and preserved events; a second writer was rejected by the lock.
- Isolated supervised crash injected after command receipt and before completion event; recovery recorded exactly one command execution and one completion event.
- Separate persisted builder, continuity and clean critic sessions. Continuity read the original visible archive and correctly retained the latest owner instructions. Explicit-ID resumption was exercised. Private roles and history are not repository assets.
- Actual local generation returned model ID `qwen3.8:27b`. The first attempt failed structured-output validation and remains preserved. The second produced 8 development and 8 private holdout cases in 32.366 seconds; structural and hash checks pass. This is local worker latency, not phone inference latency. The service reports `exl3` ownership; the underlying weight revision/checksum has not been independently verified.

Run `python3 tools/orchestration/test_runner.py`, `python3 tools/orchestration/recovery_smoke.py`, `python3 tools/evaluation/verify_freeze.py`, and the Android checks described in [ANDROID.md](ANDROID.md). The service smoke requires a Linux user systemd bus. It creates an isolated temporary fixture and does not invoke Codex or alter the application repository.

## Boundaries

The evaluation pilot is model-authored and its rubrics are not verified factual gold. Holdout questions and raw generation responses are private and unavailable to implementation workers. The critic is an independent Codex session, not a human acceptance authority. Critic isolation is by clean session, separate evidence directory and explicit read scope, not a separate operating-system security principal.

The Android slice is an extractive prototype. Native generation, source-supported synthesis, broad knowledge/travel coverage, robust installation, resource auditing, comparable evaluation and real-device evidence remain open. The supervised task chain advances those independent engineering tasks while physical Android/GrapheneOS acceptance waits for hardware. No bounty completion or competitive superiority is asserted.
