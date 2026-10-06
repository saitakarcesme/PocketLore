# Native cache auxiliary raw evidence contract (task 538)

The required Android build and offline cache-reuse checker both return **0** on the final source. This qualifies bounded synthetic evidence controls only. No model file, device or unrelated service was accessed or changed.

## Implemented contract

The checker replaces auxiliary marker searches with ordered native operation records, exact refusal reasons, process stat/status/startticks, namespace and cgroup identity, readonly held-fd identity, and exact mapped inode/device/offset/extent checks. It checks expected owner lifetime and teardown. Lifecycle controls execute 55 refusals (including 33 live-reader scalar boundaries); fault controls execute eight ownership/refusal cases plus two actual seccomp syscall-failure children. Tail, remap, unknown residency, failed advice and bounded no-progress cases retain current linked execution and raw observations.

Hung and read-error processes explicitly require no native mapping. The hung child receives TERM, then KILL and reap (exit -9); the injected read-error child receives TERM and reap (exit -15). These are expected controlled failures, not successful native/model work. Direct-child pidfds and startticks bind supervisor cleanup; nested seccomp children retain their own stat/status and parent wait outcomes.

The shared collector preserves the actual combined stdout/stderr stream, including invalid UTF-8 and read failures. It bounds log/sample growth and preserves exception receipts. All 53 named source inputs, linked artifacts, derivation/configuration, input versions and pre/post identities are frozen. Unknown or inconsistent required fields fail closed.

The final checker rejects **65 corruptions**: 28 targeted semantic/envelope mutations, 24 family-specific mutations and 13 retained main cache mutations. Each corruption follows revalidation of the unchanged actual positive baseline. Semantic mutations rebind byte envelopes, and the recorded guard must equal the intended guard. This is finite coverage, not a claim to reject every possible forged transcript.

## Current measured evidence

Current raw run SHA-256: `ec3fee0c87dc8a1dc3397c303a6f84951452d7f1c6634b3c10fa023fca2f5719`.

The task used three separately retained collections while strengthening guards and reducing packet duplication. They created 140 MiB total synthetic fixture bytes: 132 MiB initially and two additional 4 MiB lifecycle fixtures. Later collections reused unchanged force/retain/fault bytes. Each file remains at most 64 MiB. No historical collection or attempt guard was overwritten.

The final repeated 4 MiB range has 1,024 cached pages and zero major faults under retain, versus zero cached pages and 1,024 major faults under force-drop. Pressure remains within the fixed 8 MiB synthetic budget. These observations establish neither universal speed nor a model working set. The largest sampled supervising aggregate was 4,622,487,552 bytes, including writer/build/history charges; the largest sampled native-control RSS was 26,181,632 bytes. Aggregate cache, process RSS and globally observable file-cache residency are distinct measurements. Raw current/peak/events/swap observations remain in the packet.

Actual host CLI, lifecycle/fault/reuse controls and both Android libraries link successfully. All six native artifacts were byte-identical across forced relinks after a normal checkpoint. Host/x86_64 ELF machine is 62, ARM64 is 183; Android LOAD and packaged ZIP alignment are 16 KiB. Final APK SHA-256: `90cdfad474b016344ae2ef55a9a8d5a14347dd40288eeec108872051cba42f6b`. The supervisor reports 9 GiB, swap 0, CPU 200%, four affinity CPUs and TasksMax 512; pre-heavy-phase availability checks require 11 GiB. Commands have explicit timeouts; no orchestration was changed.

## Packet and review

`cache-auxiliary-contract-review.json` contains the current actual execution, frozen source texts, build receipts, original stream bytes, raw native/kernel observations, exact guard outcomes and independent review. Top-level original file envelopes use `gzip+base64` with original-byte SHA-256. Mutants use `structural-delta-v1`: decompress `patch_gzip_base64`, apply ordered path edits to the canonical `execution` object, and verify `reconstructed_sha256` over sorted-key JSON. Every stored delta was reconstructed and compared with its exact mutant. Native raw envelopes remain separately intact.

The independent reviewer verified all 14 original compressed envelopes in reviewed packet `4cbd00a1b64485cd09fe520f6f97bf02719b28b819bd69682cba5accaee099cc`, bound to auxiliary source `5e5e1182ee06676fa421d0d80a6c18a532683fe42b6d1a63c259d3aace0274e6`; finalization adds that review without changing executed sources or measurements.

> The compact packet preserves verified original receipts and reconstructible mutation evidence for 65 refusals, supporting bounded synthetic contracts without establishing model performance, useful generation, full-device memory fit, or Android execution.

This is independent agent criticism, not human acceptance. Accepted 537, its initial missing-stderr failure, the two earlier 538 collections, and historical 531/534/536 failures remain unchanged. The intermediate oversized review packet is retained outside Git; no generated binaries, model data or CMake output are committed.

## Unqualified gates

No model access or automatic model dispatch is part of this checker. Defaults, original weights, scalar settings, future execution bounds and ordinary JNI admissions remain unchanged. Model usefulness/fit, full-source admission, actual Android JNI/UI/cancellation/restart/no-GMS, physical 12 GB resources, the complete 45 GB target/50 GB installed/provider/temp/update/rollback profile and unseen matched comparisons remain open. The terminal emulator and protected personal records were untouched; current device preservation is not newly observed.
