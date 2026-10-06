# Native owned mapping and cache lifecycle — repair 2

Current builder validation: Android build **0**, native lifecycle checker **0** (`PASS_BOUNDED_NATIVE_LIFECYCLE_ONLY`). Independent read-only criticism supports this bounded scope. Runner acceptance remains separate. No full model load, prefill, generation or Android execution occurred.

## Recovery and repaired failure

Recovered useful native/control code selectively from c4615b220665376146690779f97589d52e726302, preserving accepted 532 mapping code and excluding generated build artifacts. Local checkpoints 2f4fde8, 75dacf6 and cccc287 retain the implementation and control progression. The previous canonical build passed but lifecycle check failed ARM64 binding; its passing narrative was incorrect. Its complete negative packet remains byte-for-byte in `native-cache-inputs/repair-2/prior-c4615b2-review.json`. Prior a958 and repair-1 failures remain historical evidence.

Both upstream metadata generators discovered enclosing PocketLore Git state from isolated archives. An owned repository reproduced changed ggml/llama metadata under parent commits. The derived source now explicitly identifies pinned bb4caa7540188872173c44d161602d9271386413 plus modified derivation c5f4ff52cdb616744ffcd3e010465cf3c5be35a563fe7dd87d930721a11ec1d5. Patched metadata remained identical under parent commits and dirty state. This proves the mechanism, not that it explains every historical binary difference. The shared pinned checkout is unchanged.

The first metadata test failed because `cmake` was absent from PATH; using the installed canonical absolute path fixed it. Its owned fixture and observed failure fields remain retained. No global configuration changed.

Evidence collection now retains both original receipt byte streams before validation, including malformed UTF-8. Per-log failures are recorded; atomic content-addressed observations preserve prior packets. Genuine positive fixture/model copies with altered source or binary identity fail through the actual validator while retaining complete model evidence. Missing model inputs fail. The historical model and fixture receipts were recovered; the recovered builder packet differs from the independently reviewed 462630... hash, so that exact old positive packet remains unavailable.

## Linked reproducibility and controls

Both host executables and both Android libraries are byte-identical across normal checkpoint changes and forced recompilation of metadata, loader and executable translation units using the same build paths/toolchains. Configuration text, input hashes, actual build logs and machine/LOAD/APK checks are embedded in the review packet. This is not cross-toolchain or arbitrary-path reproducibility.

| Artifact | SHA-256 |
|---|---|
| Host native controls | 217982c07d5a1d69c70a80eb4ec73652f906c78eb2a7f979d7e78305eddee1c5 |
| Host diagnostic CLI | 09efb0a3117183829433644e32271e5f9103bff6b6e34381d87daa56baf6d992 |
| Android ARM64 library | 83096873a9f2981be0851b5b9c507dfd591724193b03851af3f9ba774469092d |
| Android x86_64 library | d0b9f8c71014169d475d3c4ff43fa434ff907d8419008de9f7e721259230ec17 |
| Packaged APK | 7196f730fc608ca0d40697f7cd282fde78dae589449011f75543f997b5cfc23f |

Actual ELF machines and 16 KiB LOAD/ZIP alignment passed. Eighteen pre-sample groups cover owned hung/error child reaping, native cancellation/expiry cleanup, identity/cache refusal, ELF checks and real native fixture behavior. The final gate refused 15 receipt mutations for each genuine fixture/model baseline and two source/binary failure-finalization cases. Default prefetch/repack and normal model admissions remain unchanged; diagnostic ownership is cooperative and serial, not arbitrary concurrent JNI safety.

## Exact-model window observation

Candidate source, executables, derivation, checker, tensor selection and resource preflight were frozen before the sole repair-2 model attempt `model-25fcd3b8`. One bounded streaming SHA pass verified all 12,290,628,576 bytes against 96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7. The fixed window begins at 10,993,664 inside the first stored `output.weight` tensor, not metadata: 4 MiB window, 12 MiB cumulative charged payload. Prior 532/533/repair-1 counters and guards remain untouched.

The run lasted 37.783 seconds with 684 live samples, namespace PID 5/startticks 48904025. Raw status/stat, namespaces, mount, held fd, smaps, monotonic phases and cgroup readings are frozen in the review artifact. VMA resident bytes fell from 4,194,304 to zero; mincore pages for this window fell from 1,024 to zero. This is targeted advisory release of the observed window, not proof of complete file-cache eviction or model working-set fit.

Synchronous smaps sums before/after advice: RSS 13,209,600 / 9,515,008; PSS 10,048,512 / 6,127,616; anonymous 4,476,928 / 4,714,496; private-clean 4,706,304 / 512,000 bytes. Swap remained zero. Separate status snapshots report VmRSS 13,414,400 / 9,527,296 and HWM 13,414,400 / 13,529,088 bytes; these sequential kernel reads are not one atomic sample. Maximum sampled aggregate cgroup current was 1,880,014,848 bytes; unit lifetime peak was 2,575,425,536, which includes build/tooling history and is not model RSS. The 9 GiB/swap-zero supervisor and 7.5 GiB execution stop remain unchanged.

## Independent criticism and limits

The frozen packet consistently supports reproducible linked artifacts, bounded fixture/model-window lifecycle, and lossless failure retention; full model loading, generation, working-set fit, Android execution, and physical-device acceptance remain untested.

The declared review JSON embeds current raw fixture/model bytes, executed source, live observations, build/configuration receipts, exact identities, corrupted-receipt outcomes and independent criticism. Original 500/524/531 useful generation, source entailment, actual JNI/UI lifecycle, full-source admission, complete 45 GB target/50 GB installed-update profile, physical 12 GB/no-GMS and unseen comparative gates remain open. The terminal emulator and all original source/model assets were untouched.
