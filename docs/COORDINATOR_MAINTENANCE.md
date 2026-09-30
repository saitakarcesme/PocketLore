# Coordinator compliance maintenance

This change is developed in an isolated worktree based on accepted main; it does not alter the active native-runtime builder checkout.

The runner now resumes the canonical critic and builder IDs, snapshots explicit approval/sandbox/add-directory policies, validates one English critic sentence of at most 35 words, and publishes each completion to a durable continuity ledger and notification outbox. A separate notifier resumes the canonical continuity chat; delivery failure cannot block application dispatch. Interrupted delivery and partial completion publication are replayable.

Repair ordinals remain stable across process restarts and status changes. Three failures of the initial approach require a strategy-change artifact and a different approach; a failed alternative blocks that branch as strategy-exhausted while independent tasks remain ready. Existing product task contracts and meaningful in-task checkpoint instructions remain in place.

Eleven regression tests cover repair exhaustion, independent scheduling, canonical role invocation, policy persistence, review length/sentence/language guards, interrupted evidence writes, process receipts, ledger/outbox recovery and failed notification retry. An isolated real systemd crash/recovery smoke additionally verifies one execution and one completion event. These are orchestration checks, not application-quality acceptance.

The private full research and planning translations retain 5,740 and 2,879 words, with verified source/output hashes, original links, commit IDs, headings and tables recorded in translation validation. Original private conversation history and immutable past critic evidence remain unchanged; mutable summaries explicitly distinguish English translations from those historical outputs.

Deployment records live privately in state/coordinator-followup.json. The intended deployment uses a commit-pinned private runtime copy and exact active-session resumption. Main integration is a separate queued task after the active task reaches a safe boundary. No physical Android or GrapheneOS acceptance is implied.
