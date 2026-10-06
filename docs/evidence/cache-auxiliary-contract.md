# Native cache auxiliary raw evidence contract (task 538)

Current status: implementation checkpoint, unvalidated. No model file or device is accessed by this task.

Accepted 537 (e340f0b25e6f09f3358756937da893a118e4c30a) is retained unchanged. Its independently reviewed synthetic cache measurements do not establish model fit. Its auxiliary marker checks were weaker than its primary cache checks. The historical missing-stderr collection failure remains retained; the real shared helper combines stdout and stderr.

The new task-specific collection is `downloads/cache-auxiliary-538`. Native controls record ordered operations, exact refusals, process stat/status/namespaces, held readonly descriptor identity and matching raw smaps. Parent-supervised records retain pidfd ownership, resources and bounded termination. Synthetic seccomp children retain their own process records and parent wait outcomes. No-mapping process-only controls are explicitly distinguished from native mapping tests.

The frozen synthetic access pattern and cache budgets are unchanged. The current implementation adds named semantic guards and revalidates a genuine positive baseline before each mutation. Byte envelopes are rebound for semantic mutations; envelope corruption is tested separately. Results will be reported from executed current-code checks, not marker presence or historical execution credit.

Open gates include model execution and usefulness, actual Android runtime/JNI/UI, full source admission, the complete 50 GB installed/update/provider/rollback profile, physical 12 GB/no-GMS and independently matched unseen comparison. This work cannot qualify any of them.
