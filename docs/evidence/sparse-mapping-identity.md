# Exact owned mapping identity and bounded cache controls

Task532 qualifies a serial host helper and its bounded controls only. It does not accept failed531/524/500, actual Android, useful generation, the full distribution or superiority.

## Recovery and protected state

The current branch began at `a152508`. Only `tools/runtime/sparse` and `tools/evaluation/strong-native-host` were recovered from `608533da01c170faa4fc4b7b56a600b40e5a3c92`; the exact per-path hashes/base are in `sparse-mapping-inputs/recovery.json`. The recovered profile/patch/parser retain their earlier `9e90921` lineage and pinned llama.cpp `bb4caa7540188872173c44d161602d9271386413`. No historical acceptance report was edited or promoted.

No `android/native-build` content was recovered or staged. `.gitignore` now excludes that generated tree; current Git tracks zero files there. New outputs are under ignored `downloads/sparse-mapping`. No Android source, default2GiB/3GiB admissions, generation behavior, model bytes, services, source downloader, emulator or protected user records changed. No push or branch change occurred.

The original failure is retained byte-for-byte in the review packet: receipt SHA256 `acc6df50c95cd5af63236adaa001d46eb86aaf7a3e876bfb452e6279f506327c`; independent manifest SHA256 `ba1cec4daeddbc08ebc448ce4fac1ac46aff56315636851b8db7cf862569829d`. Its8.42GB aggregate,3.38GB processRSS, no kernelOOM, namespacedPID5 and zero output remain historical failure evidence.

## Actual identity explanation and bounded contract

The fresh live probe again observed descriptor `st_dev=57` (`00:39`) and mapping device `00:1d`. The held descriptor has mount ID799. Its exact namespace-local mountinfo row identifies Btrfs `/@home`, subvolume257, with mount device `0:29` (hex `00:1d`). These are genuinely different kernel representations, not a decimal/hex conversion mistake. The raw values are preserved. Pathname or inode alone is not used to erase the difference.

`mapping.py` opens a readonly descriptor, computes and checks the full identity once, and keeps that descriptor alive across its own mmap syscall and all inspections. It binds PID/startticks, mount/user/PID namespaces, descriptor size/device/inode/mtime/ctime/link count, fdinfo mount ID, complete mapping address/offset/permissions/inode and the mount device. Source paths are additional replacement/rename checks, never sole identity proof. Changed/deleted/renamed files and partial, replaced, mixed or unexpectedly coalesced VMAs fail closed. Closed mappings cannot be inspected. Descriptor release while a mapping is live is refused.

`map_files` readlink is observable, but following its stat returns actualEPERM. This restriction is frozen, not bypassed. The positive route is therefore **same-process mappings created by this helper from a held, full-hash-verified descriptor**, with independently matching pread bytes. It cannot adopt arbitrary foreign/native mappings or retrospectively qualify old531 smaps. That old strict residency parser is preserved unchanged and its historical attribution failure remains unresolved for that execution. No hostPID is invented from namespacePID or zero entries in cgroup.procs.

The helper allows at most128MiB total live owned mapping windows in its serial prototype, with aligned in-file ranges, bounded64KiB copy chunks, cancellation/deadline checks and explicit close. It does not cache or prune experts. Caller-owned output copies and Python bookkeeping are separate allocations, not magically covered by a mapped-window count. It is not yet a multithreaded native loader or a general model working-set manager.

## Real measurements and discriminating controls

Live probe `20261006T103656Z` ran for8.97seconds in namespacePID3/startticks48239171. It performed **one** fresh full hash of the exact12,290,628,576-byte file, confirming SHA256 `96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7`. The pinned identity remains qwen35moe/733 tensors; this task did not repeat the header parser or load a model. The hash used4MiB reads with targeted own-file DONTNEED advice and183 live resource observations, not a system-wide cache drop.

Before execution, the fixed policy selected4MiB windows at offsets16MiB and64MiB. As of canonical run `20261006T104417Z`, model pread/copy/reread consumed24MiB payload and three separately recorded checker oracle passes read8MiB each, for **48MiB cumulative payload**, below64MiB; later invocations report their own cumulative total. Subsequent checker reads have a persistent cumulative guard; no repeated full hashing occurs.

Both windows produced identical pread/mmap/reread SHA256 values. Each observed mincore count changed0→1024→0 across before/touch/targeted madvise+DONTNEED. Each touched readonly VMA had4,194,304bytes RSS/PSS and0anonymous bytes; after advice its RSS/PSS were0. These are small-range observations, not whole-model zero residency, guaranteed eviction under contention, coverage loss, generation speed or a model working-set estimate.

Process rollup RSS/PSS after the second touch were49,504,256/41,416,704bytes, anonymous34,402,304; its subsequent after-advice RSS/PSS were45,314,048/37,226,496. Clean file pages reported as Private_Clean are not thereby anonymous or transformed allocations. Caller buffers/bookkeeping persisted after close, so total process RSS did not return to baseline. Cgroup current/peak after close were255,954,944/286,449,664bytes; aggregate includes the supervisor/tooling/cache and is not model-only RSS. Swap/OOM counters remained0.

The actual kernel group enforces4,294,967,296bytes, swap0, CPU200000/100000, Tasks512, and the process affinity is CPUs0–3. Observed source-job ownership and host memory are retained. The probe uses a180second outer timeout and120second operation deadline; checker timeout is90seconds. The parent-described one-hour service limit was not independently readable: the own-unit user-bus probe failed and is preserved. None of this proves device12GB safety or changes the older7.5GiB stop/9GiB containment limits.

There are19 real controls: three positive fixture/model windows and16 refusals covering expected digest/inode, another descriptor, wrong hash, oversized/unaligned/out-of-file ranges, cancellation/deadline, partial/closed/mixed mappings, rename/delete/version changes and a same-size path-like sparse distractor. The latter has12,290,628,576logical bytes but only4096allocated bytes; it contains no model, is never loaded or fully hashed, and is not a distribution asset. Engineered fixture bytes use a frozen independent formula and pread oracle. Only newly owned deletion fixtures were unlinked; protected/original files were untouched.

Independent review found an initial checker defect: changing a reported RSS without changing raw smaps was accepted. That red control and executed validator are retained. The repaired checker independently reconstructs complete VMA fields/counters from raw smaps, checks rawstatusPID/fdinfo inode, and rejects11 stale/hash/inode/PID/missing/range/mount/residency/kernel/raw-field mutations against the real positive baseline. Final required command `bash tools/evaluation/check_sparse_mapping_identity.sh` exits0 in run `20261006T104417Z`, classification `BOUNDED_OWNED_MAPPING_CONTROLS_PASS`.

## Unchanged gates

There was no model load, prefill, generation, Android build/deployment, device restart or lifecycle action. Cache advice is advisory; concurrent actors and native tensor scheduling need separate controls. A future materially changed generation route must integrate exact owned-fd provenance and validate its real working set, cancellation and support quality under unchanged budgets; this helper cannot establish that such a route fits.

Original531 useful generation,524/500 independent entailment/publication, actual AndroidJNI/UI/reuse/restart, noGMS, physical12GB/50GB, complete45GB-target/50GB provider/temp/update/rollback, rights and unseen matched rival gates remain open. The sealed40.950GB bundle plus12.290GB model still exceeds50GB before other assets; no corpus reduction or arithmetic waiver was made.

Independent final criticism: “The final checker preserves chronology, source identity, and raw-smaps consistency checks across 11 rejected mutations, with 48 MiB cumulative payload evidence limited to owned mappings and no generation, historical attribution, or Android acceptance.”
