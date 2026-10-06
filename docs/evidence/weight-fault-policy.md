# Owned random-fault policy: bounded native engineering

Current task535 required Android build and synthetic native policy checker both exit 0. This is linked-build and synthetic host acceptance only. No actual model file was opened, hashed, mapped, advised, loaded or executed, and no device command was issued.

## Implementation and lineage

Accepted d34abaa native ownership/build identity remains the base. Scalar scheduling and supervisor source were selectively recovered from failed 7df3445c; generated files and its acceptance narrative were not imported. Current checkpoint implementation adds opt-in `FaultPolicy::Random` to the actual held-file/mmap path. Ordinary JNI/default admission, default prefetch/repack and the 2/3 GiB limits remain unchanged.

The random owner opens a dedicated readonly file description, checks inherited descriptor identity across reopening, acquires a nonblocking file lease, verifies bytes/version, and applies POSIX_FADV_RANDOM. The actual derived llama mmap constructor validates readonly range/identity and applies MADV_RANDOM before exposing the mapping to the loader. Setup errors refuse with cleanup. Existing serial alias/use, cancellation, deadline and teardown restrictions remain; arbitrary concurrent JNI safety is not claimed. All original weights would remain accessible in a future exact-asset diagnostic; no model attempt was made here.

Linux documents both operations as advisory. The retained primary references and exact frozen access policy are in `weight-fault-inputs/api-sources.md` and `policy.json`. Return codes alone are not the effect oracle: current native controls observe mincore and independently compare original bytes.

## Frozen synthetic experiment

Two separately created 64 MiB files contain the same deterministic original bytes; generation uses 1 MiB buffers. A separate 4 MiB lifecycle fixture keeps total new fixture content at 132 MiB, below 256 MiB. No input is a user document, model, dataset or benchmark question. Each default/random file has its own descriptor and lifetime. Both rounds independently require zero cached pages after fsync/write-close and targeted own-file advice before touching the 16 frozen 4096-byte pages.

| Policy | Round | Cached pages after access | Touched | Untouched cached | Adjacent untouched | After release |
|---|---:|---:|---:|---:|---:|---:|
| Default | 1 | 16384 | 16 | 16368 | 32 | 0 |
| Default | 2 | 16384 | 16 | 16368 | 32 | 0 |
| Random | 1 | 16 | 16 | 0 | 0 | 0 |
| Random | 2 | 16 | 16 | 0 | 0 | 0 |

Every accessed page byte matches the independent deterministic oracle (65536 bytes per round), with 16 additional pread/mapped comparisons after advice. Zero released mincore pages describes these fixture mappings at observation time, not universal page-cache eviction or a model working set. RSS, mincore and supervising file-cache accounting are distinct.

Default/random/negative native runs each retained 17 live same-PID samples. Sampled process RSS maxima were 8687616, 8695808 and 9056256 bytes; PSS maxima were 5683200, 5694464 and 5829632. Sampled supervisor current maxima were 1373765632, 1326333952 and 1336979456 bytes. Supervisor lifetime peak was 2342785024 bytes, including earlier build/tool activity; it is not each probe's incremental use. Swap and OOM/max events were zero. Exact raw stat/status/smaps/mount/fd/namespace, mincore lists and kernel records are embedded in the review artifact.

Actual native controls cover setup syscall EPERM (isolated child seccomp), wrong inode/hash/size, offsets/alignment, readonly inheritance, dedicated-OFD independence, double ownership, alias/live-reader refusal, cancellation, deadline, exception, reuse and teardown. Owned hung/read-error controls prove bounded termination and reaping. Twelve mutations against the genuine positive packet reject empty source bindings, altered executable/PID/startticks/namespace/input version/mount, noncold starts, byte mismatch, setup failure, missing round and absent measured effect.

Future-generation source controls retain preflight/capture failure attempts even before a model is accessible; successful receipts must have verified/load/prefill/generation/completed/unmapped chronology and original CPU/wall limits. These algorithm controls are not successful generation receipts. The genuine retained534 case remains rejected.

## Linked artifacts and finalization

Host sparse-host, native-cache-controls and fault-policy-controls, both Android ABI libraries and the APK were built through the current paths. A repeated same-input host/Android build after a normal source checkpoint reproduced all six SHA256 values. Android ELF machines and 16 KiB LOAD/ZIP packaging are checked; this is not Android execution.

* Host sparse-host: `6b6ff7c582e3b214e7ae318d129342ed18a63ce10f1869812251ea969a4844d8`
* Fault controls: `30c202c51dc4a5307781da01897f54a751743010ddc5be8c63faa1d145114726`
* ARM64 library: `a481109f96ba572170173a4252cbfe2b5145a70b5a4fbe91aad44e21a1ecc8a3`
* x86_64 library: `c664317074bfab7504b21a53b60b272b4234f792098dde760862db1b8db6bfa5`
* APK: `a047034450b7ea3ba26e65023ecb17a6d27fabc0ee1801953919e3720cd4bffb`

Inputs, current source text, derivation manifest, pre-spawn and post-stable executables and input versions were frozen before controls. Executed receipts are retained before subsequent parsing; complete raw bytes, build logs, kernel preflights and separate mutation failures are embedded in `weight-fault-policy-review.json`. Ignored downloads retain content-addressed observation history and fixture files. An optional postprocessing display raised AttributeError after successful validation; its exact error is retained separately and did not change observations or acceptance.

## Historical failures and remaining gates

The exact534 receipt SHA12368edf8e3af36229ae3969119f8a4d5966eaf98e9e2ca5c87e7c104ab6807e and prior prose remain unchanged under `weight-fault-inputs`. Clarification: sampled aggregate maximum was 8460570624 bytes, separate postcleanup kernel lifetime peak8479965184, sampled processRSS1995083776 and HWM2007703552. One scalar step completed, the second stopped with zero output; case2 was unrun. This was not kernel OOM and does not establish model-only memory or readahead as sole cause. All531 failures remain failures.

The current synthetic effect cannot establish full-model cache pressure, first-token fit, useful output, speed, expert working set or actual Android behavior. No model or device access occurred. Original500/524/531/534 generation/support/publication, full source, actual Android/noGMS/cancellation/reuse/restart, physical12GB, complete45GB target/50GB installed/provider/temp/update/rollback and unseen matched comparison gates remain open. A separately reviewed future materially changed execution is required; this checker never starts one.

Independent criticism: Frozen synthetic runs show random policy reduced cached pages from 16,384 to 16 with byte preservation and 12 rejected mutations; actual loader integration is present, but model behavior, generation, and Android execution remain untested.
