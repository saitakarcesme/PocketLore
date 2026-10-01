# Scale Android builder evidence

Date: 2026-10-01. Environment: LLMRig host, isolated checkout and private lane. UX cases were frozen in commit `7e42073` before implementation. Independent criticism is pending against the sealed handoff; no self-review is presented as acceptance.

## Executed checks

- `ScaleImportCheck`: 16 host assertions pass against production `ModelImport`, `ResourceStorage` and `ImportRecovery`: exact SHA-256, unknown/oversized/truncated/cancelled/bad-magic rejection, reserve boundary, overflow, persistent intent, stage-only cleanup and idempotent marker completion.
- Existing `tools/android-check.sh`: eight retrieval, abstention, corruption and citation contracts pass using the freshly acquired hash-verified starter data.
- Existing `tools/answers/check.sh`: FAIL at “Valid citation route failed” (line 30). The same failure reproduces using all five Java files extracted from the untouched supplied baseline `9f064df6f472a56dddf15e86d12f5d2c6a14f7e1`; they are byte-identical to this lane. Both logs and a diagnostic probe are preserved. This is an unresolved baseline regression, not a passing answer suite; no test expectation or answer guard was changed.
- Full Gradle compilation and APK identities are recorded in the private `HANDOFF.json`, along with raw logs. Compilation is not execution or UI verification.

No inference, GPU scheduling, model downloads, ADB command, emulator installation, screenshots or physical-device test was performed. The Android instrumentation test is compiled for later execution, not reported as passing. No holdout, canonical source checkout, coordinator state, service or global configuration was changed.

## Build reproduction

Existing toolchain: `/home/isa/Android/atlas-toolchain`, JDK, Gradle 8.13, Android SDK 35, NDK r27c and CMake 3.22.1. Its Gradle cache was copied into the private lane and only the copy was writable. Pinned llama.cpp source was fetched into ignored local downloads at revision `bb4caa7540188872173c44d161602d9271386413`; its MIT license matches the packaged copy.

```
PATH=/home/isa/Android/atlas-toolchain/jdk/bin:$PATH \
ANDROID_USER_HOME=/home/isa/PocketLore-control/scale-workers/android/android-user \
GRADLE_USER_HOME=/home/isa/PocketLore-control/scale-workers/android/gradle-user \
POCKETLORE_BUILD_JOBS=2 JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=2 \
OMP_NUM_THREADS=2 bash tools/android-build.sh --max-workers=1 assembleDebug assembleDebugAndroidTest
```

This invokes CPU compilation only. Build artifacts, signing material, dependency cache and source datasets remain ignored or outside Git. The existing deterministic APK finalizer remains unchanged.

## Acquisition and date limits

Actual network acquisition completed using the existing source verification tools: eight pinned USGS paragraphs and 25 pinned Wikidata records. Exact downloaded-byte hashes, sizes and counts are in `acquisition.json`; exact Wikidata revisions/URLs/dates are in the hash-bound `tools/packs/regional-sources.lock.json`. USGS paragraph identities and policy are in `android/knowledge-sources.json`; upstream page revision timestamps are unknown. Embedded historical retrieval dates were preserved, with this lane's new download date recorded separately. These are build inputs, not a scale milestone or newly accepted rights review.

## Preserved failures and limitations

The first Git operation failed because `.git` is read-only. A copied private `lane-git` now holds commits bound to this worktree; the original metadata remains unchanged. A second setup failure required setting author identity only inside that private Git directory. The first build completed all 63 Gradle tasks in 5m 49s, but the finalizer failed because apksigner could not find java on PATH. Its log and pre-finalization APK are preserved. A command-local JDK PATH correction completed the build/finalizer in a second invocation (Gradle: 13s). The resulting app SHA-256 is `b7cf6a7e541970d19154e84da25b37fe9a49c38e00e3ce2c32642dcfdc8c2d0f`. The manifest reports no requested permissions. A nonfatal read-only Android analytics-settings warning remains preserved in both build logs. Raw failure descriptions remain in the private evidence directory. Reviewers must use the handoff's explicit Git directory and commit, not the read-only worktree HEAD.

Durable markers do not resume byte offsets. Failed imports require the original source to restart. Filesystem power loss and directory-fsync behavior remain untested. Model reload hashes the file using a bounded buffer but has no publisher-authentication or user-supplied expected-hash contract. The retained broad reader rehashes its database on load and does not support arbitrary bulk schemas. Its large-shard import/startup latency, storage, Java/native peaks and whole-install budget are unmeasured. Model profiles above the existing 2 GiB ceiling are not enabled.

Remaining device checks and exact reader contracts are in `ux-freeze.md` and `reader-contracts.md`. UI accessibility, process-kill recovery, real disk-full behavior, sustained phone resources, GrapheneOS compatibility, answer usefulness and rival comparisons are open.

Baseline diagnostic: the synthetic draft is withheld as FALLBACK with “No complete clause predicate recognized; draft withheld.” This lane leaves the clause guard and historical fixture unchanged for the answer-quality owner.
