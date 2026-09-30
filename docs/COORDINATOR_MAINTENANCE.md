# Coordinator compliance maintenance

This change is developed in an isolated worktree based on accepted main; it does not alter the active native-runtime builder checkout.

The runner now resumes the canonical critic and builder IDs, snapshots explicit approval/sandbox/add-directory policies, validates one English critic sentence of at most 35 words, and publishes each completion to a durable continuity ledger and notification outbox. A separate notifier resumes the canonical continuity chat; delivery failure cannot block application dispatch. Interrupted delivery and partial completion publication are replayable.

Repair ordinals remain stable across process restarts and status changes. Three failures of the initial approach require a strategy-change artifact and a different approach; a failed alternative blocks that branch as strategy-exhausted while independent tasks remain ready. Existing product task contracts and meaningful in-task checkpoint instructions remain in place.

Eleven regression tests cover repair exhaustion, independent scheduling, canonical role invocation, policy persistence, review length/sentence/language guards, interrupted evidence writes, process receipts, ledger/outbox recovery and failed notification retry. An isolated real systemd crash/recovery smoke additionally verifies one execution and one completion event. These are orchestration checks, not application-quality acceptance.

The private full research and planning translations retain 5,740 and 2,879 words, with verified source/output hashes, original links, commit IDs, headings and tables recorded in translation validation. Original private conversation history and immutable past critic evidence remain unchanged; mutable summaries explicitly distinguish English translations from those historical outputs.

Deployment records live privately in state/coordinator-followup.json. The intended deployment uses a commit-pinned private runtime copy and exact active-session resumption. Main integration is a separate queued task after the active task reaches a safe boundary. No physical Android or GrapheneOS acceptance is implied.

The initial maintenance runtime was deployed from commit `8f045216782c8cf3c77a6e5230638cd0fe61d5e4`. The native task resumed with the same session, and its preserved dirty file hash matched after restart. Bootstrap and maintenance notifications reached the canonical continuity chat. The workspace-write sandbox hid KVM, so a separate PocketLore emulator service restored the existing AVD through adb without weakening that sandbox. Exact live status and delivery receipts remain in the private follow-up record.

## Safe-boundary integration — task 005

On October 1, 2026, the builder inspected a clean working tree on the existing
`checkpoint/005-integrate-coordinator-compliance` branch, based on application
checkpoint `f596b1a`. Neither requested maintenance commit was already present
by ancestry or equivalent patch. Both were cherry-picked in the requested order,
without conflicts or application edits:

| Reviewed source commit | Integrated checkpoint commit |
| --- | --- |
| `8f045216782c8cf3c77a6e5230638cd0fe61d5e4` | `1d1be4b` |
| `7c36334041a4ebcd8af48062d754520e260ec410` | `c1c3b7f` |

The two changes remain separate commits. No branch switch, reset, push, service
restart, live runner-state change or main advancement was performed. The builder
did not inspect private context or deployment receipts.

Validation on LLMRig:

```text
python3 -m unittest discover -s tools/orchestration -p 'test_*.py'
Ran 11 tests in 0.042s
OK
```

A Git comparison against `f596b1a` confirmed no changes to `android`,
`tools/runtime`, `THIRD_PARTY_NOTICES`, `FINDINGS.md`, native evidence, or the
Android/runtime/release-gap documents. The unchanged application tree identities
are `android`: `fa32e69c597f96f2965f0a7917cc354ec8b8690c` and `tools/runtime`:
`7beace349fc435c3f10195ab3d46a018d9c000ea`.

These regression tests exercise temporary test state and mocked external process
interactions. They do not revalidate live deployment, continuity delivery, systemd
crash recovery, emulator readiness, application inference, or physical hardware.
The deployment and supervision statements above are preserved from the reviewed
maintenance commits, not newly verified against private live state by this task.
Native validation remains a separate task; no old emulator launcher was restarted.
