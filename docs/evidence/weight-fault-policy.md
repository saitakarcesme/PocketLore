# Owned random fault policy — task 535

Current status: implementation and linked validation in progress. No model bytes, header, hash, mapping, advice, load or generation are accessed by this task. Synthetic fixture controls are the only execution planned.

Useful scalar/supervisor source was recovered selectively from failed 7df3445c50dae524e4a6e7a795bc7d4a52bb63f8 on accepted d34abaa2a76a8d90141cb7bf569c493cb95d1bf5. The old screen remains failed: sampled aggregate maximum 8,460,570,624 bytes, separately observed post-cleanup kernel lifetime peak 8,479,965,184, processRSS 1,995,083,776 and HWM 2,007,703,552. Those different observations are not interchangeable, a model-only requirement, or proof that readahead was the sole cause. Exact old receipts and independent manifests are retained under weight-fault-inputs; their bytes are unchanged.

The new policy is opt-in to the exact diagnostic or an explicit bounded synthetic owner. It obtains a dedicated readonly open-file description, takes an exclusive policy-owner lock, verifies full identity, applies POSIX_FADV_RANDOM to that dedicated description, and applies MADV_RANDOM after actual mmap creation but before returning access to the loader. Registration failure unmaps before propagation. Ordinary/default policy behavior remains conservative; no default admission cap changes.

The frozen synthetic plan uses two new identical 64 MiB files, 16 fixed sparse pages, two cold rounds per policy, independent full-page byte oracles, and measured mincore/smaps/cgroup observations. Success requires actual reduction of untouched cached pages, not syscall return alone. No-effect/unsupported/cold-start failure remains failure. No adaptive fixture selection or global cache manipulation is allowed.

Primary API references and advisory limitations are in weight-fault-inputs/api-sources.md. No native policy result can establish model residency, useful generation, Android runtime, physical12GB/no-GMS, full-source/50GB profile or comparative acceptance.
