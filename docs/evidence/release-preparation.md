# Release preparation: development candidate

Task 100 prepares local build/install/demo instructions and an auditable candidate inventory. **Current repair status: both named acceptance checks PASS. Two forced builds reproduce the complete fresh-demo APK byte-for-byte. Historical signing and v2 DEX identity failures remain preserved below.** This is **not an accepted release, bounty submission, superiority claim or physical-device result**. Work and measurements run on LLMRig; private holdout is untouched. No private runner/state/service configuration is modified.

## Reproduction and artifacts

Follow [the release guide](../RELEASE.md) for explicit online provisioning followed by offline builds, local imports and the live demo. [The current manifest](release-v3/manifest.json) records exact candidate APK/model/pack sizes and SHA-256 hashes, every packaged asset and native library, dependency/source pins and build-tool identities. It is an inventory of the tested candidate, not a complete transitive build-tool SBOM. The model is separately imported; weights are not bundled or committed. The larger reference pack contains 186 licensed passages; bundled starter and three-monument assets remain separately identified.

The app is a local-debug-key APK, API 28 minimum, with ARM64 and x86_64 CPU JNI libraries. Only AOSP API 35 x86_64 has run here. Native llama.cpp/ggml is pinned at `bb4caa7540188872173c44d161602d9271386413`; optional backends/network features are disabled by CMake. The Java runtime classpath has no dependencies. NDK static C++/compiler support is covered by the toolchain's separate notices, whose digest is recorded; full distribution-license review remains open.

The production signing key/upgrade path is not established. Reproducibility here means repeated builds using the installed rig toolchain and retained source cache; it does not establish clean-machine byte reproducibility with a different debug signing key, toolchain or source-cache acquisition. Live source pages may change; preserve caches and refuse mismatched pinned content.

## Behavioral verification

`bash tools/verify-release.sh` checks actual candidate hashes, packaged ELF ABI members and license texts, APK permissions and runtime dependency resolution, rebuilds the reference pack twice and compares bytes, executes production retrieval behavior on the host, and validates exact fresh-install demo records. Four damaged-record cases must fail (no inference, substituted question, restored assets in a fresh installation, missing cancellation). This command replays the recorded emulator evidence; it does not represent a new emulator run.

A fresh two-cycle emulator demonstration is separately executed with `bash tools/evaluation/check_offline.sh`. It archives prior app data before uninstalling, performs real SAF model/pack imports, rejects corrupted assets, checks restart/recreation/cancellation, inspects sources and records actual JNI answers. App-data archives and model weights remain ignored. Earlier failed experiments in the task-specific evidence remain preserved and are not superseded into success claims.

## Exact unresolved gates

- Useful research: incomplete comparisons, unnecessary abstention, withheld drafts, general claim entailment, broad synthesis and independent usefulness review remain open. Citation syntax and successful inference do not establish accuracy.
- Coverage: 186 US/history-heavy excerpts and three DC monuments are a bounded sample; broad geographic/scientific coverage, current conditions, routing and tailored travel planning remain incomplete.
- Physical acceptance: no compatible physical Android or GrapheneOS device is attached; ARM64 execution, clean physical install, sustained/offline use and real phone measurements are pending hardware access.
- Resource/performance: the proposed <=12 GB RAM/50 GB installed-asset budget is not physically accepted. Prior emulator swapping, allocation-time OOM, maximum packs, provider blocking, thermals, long sessions, cold/warm latency distributions and full storage accounting remain open.
- Independent evaluation: blind packets have no independent ratings; private frozen release holdout is reserved for a separate evaluator. Named frontier/web comparison requires an authorized configured endpoint and comparable conditions. No external answers or credentials were fabricated.
- Distribution: stable release signing and upgrades, clean-machine build verification, complete transitive build-tool/license review, public artifacts/demo and submission decisions remain separate. No debug private key is published.
- Offline assurance: permission denial and airplane-mode controls are measured on emulator, not packet-level/physical-radio assurance or arbitrary document-provider testing.

Achievable product improvements remain; absence of physical hardware is not a blanket blocker. Builder verification is not independent acceptance. No main advancement or push occurs in this task.

## Preserved first candidate and fresh demo (superseded signer)

Run `downloads/offline/run-20261001T021631Z` completed two fresh uninstall/install cycles on the existing `emulator-5560`. Both started without saved model/pack; both imported the local model and larger pack through SAF, reloaded after process restart, rejected a corrupted pack and inspected imported NPS sources. The first cycle also rejected a corrupt GGUF, checked import cancellation, ran real JNI answers, cancelled after streamed output, and successfully recreated/reloaded the Activity. Airplane mode remained enabled, Wi-Fi/mobile data disabled; app-UID socket access failed with EPERM. No Play Services/Play Store was installed.

The source-dialog screenshot was visually inspected and records passage text, source URL, date and rights with airplane mode visible: [actual source inspection](release/cycle-1-model-ui/source-dialog.png). Original app data was archived under the ignored run directory before uninstall and was not restored. The final app is the second fresh imported installation.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `app-debug.apk` | 17,794,384 | `27f9d7824be8b843db7b7238c39c56893005c09f808267cf72e765c87fe0789b` |
| `qwen2.5-0.5b-instruct-q4_k_m.gguf` | 491,400,032 | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| `english-reference.plpack` | 159,327 | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |

The installed APK has no requested permissions. Debug signer certificate SHA-256: `c6e24cd03828235e27a96a7b11303b27e40f38d1140c644d927707052af5e577`. This public certificate fingerprint identifies the test key; no private key is included.

Actual answer phase (bundled eight-passage starter corpus, imported Qwen2.5-0.5B; not the later reference-pack comparison):

| Exact question | Published route | Tokens | AnswerEngine total ms |
| --- | --- | ---: | ---: |
| Compare evaporation and condensation | GENERATED | 62 | 26676.464 |
| What is groundwater? | FALLBACK | 39 | 29410.177 |
| quasar supernova | ABSTAINED | 0 | 0.127 |
| Does evaporation cure diabetes? | ABSTAINED | 0 | 1.922 |

These timings cover AnswerEngine processing after retrieval, excluding app launch, model loading, import and UI rendering. They are one emulator pass, not phone latency or percentiles. Cancellation acknowledgement was 50 ms after actual streamed output.

The generated comparison jointly describes the two processes as changing liquid to gas “and vice versa,” then repeats evaporation in its own definition; that is imprecise and incomplete. The groundwater draft incorrectly describes an unobstructed surface-to-underground flow and is withheld. Both raw drafts and final routes are [preserved verbatim](release/cycle-1-loaded-result.json). Neither is relabeled as accepted research quality. The two absent-evidence questions abstain without model invocation.

The named release verifier passes actual byte/permission/dependency checks, two independent pack rebuilds, eight host retrieval/abstention/corruption/citation assertions, fresh-demo record integrity and four negative mutations. The new fresh emulator demonstration also passes. No failure was suppressed, and no independent critic/human acceptance is claimed.

## Build reproducibility failure and repair

The first candidate passed cached normal builds and its fresh demo, but forcing build tasks with `assembleDebug --rerun-tasks` failed at `validateSigningDebug`: Gradle attempted to create a debug key in read-only `/home/isa/.config/.android`. A surviving prior APK hash was initially printed by a follow-up command; that hash did **not** prove a successful rebuild. The [actual failure log](release-failures/debug-signing-readonly.log) is authoritative.

The scoped build wrapper now creates/retains a project-local development keystore under ignored `downloads/android-debug`, and a Gradle init hook selects it before Android configuration is finalized. The first hook attempt ran too late; [that failure](release-failures/signing-hook-order.log) is retained too. No global configuration, preexisting private key or service was modified. This creates a new debug signing identity, so the original candidate and evidence remain in `release/` while the current candidate receives separate `release-v2/` measurements. Stable production signing remains open.

## Preserved candidate v2 and its failed check status

The project-local-key candidate completed a new two-cycle clean offline demonstration at `downloads/offline/run-20261001T022501Z`. Both cycles passed fresh absence/import/restart/source-inspection checks. The first also passed corrupted assets, real generation, cancellation and recreation. The final emulator retains the second fresh imported installation, airplane mode on. No model weights or app-data backups were committed.

The measured APK is 11,822,564 bytes, SHA-256 `45b9d7f8851b015c04c3f885303e25ef32a289fa9d52de38c532642a472826ea`; model and pack identities are unchanged from the table above. Current debug signer SHA-256 is `283b9d4b43c98e005181f85b13fd923664f856e7a6ca2d65a34444a1b7401fad`. The [v2 manifest](release-v2/manifest.json) freezes 67 source-file identities, 14 packaged asset/library identities, the signer and artifact hashes. Its candidate APK remains archived at the ignored fresh-demo run path.

| Exact question | Route | Tokens | AnswerEngine total ms |
| --- | --- | ---: | ---: |
| Compare evaporation and condensation | GENERATED | 62 | 26560.236 |
| What is groundwater? | FALLBACK | 39 | 29425.595 |
| quasar supernova | ABSTAINED | 0 | 0.097 |
| Does evaporation cure diabetes? | ABSTAINED | 0 | 1.429 |

The raw drafts repeat the imprecise comparison and withheld groundwater error described above; [current raw results](release-v2/cycle-1-loaded-result.json) preserve them. Streamed cancellation acknowledgement was 72 ms. Timing excludes retrieval/loading/import/UI and is emulator-only. The initial freeze verifier passed artifact and behavior checks, including negative mutations.

A subsequent successful `bash tools/android-build.sh assembleDebug --rerun-tasks` produced a different APK hash: `1e8032b80ee45024c131bd4512f32ccc0d76eb4bd18ecb770d142bc1436beff8` (same size). `bash tools/android-build.sh` also passes, but the final exact command `bash tools/verify-release.sh` exits 1 because this rebuilt APK differs from the measured candidate. This is the final status; initial verifier passes do not supersede it.

[Rebuild comparison](release-v2/rebuild-comparison.json) identifies only `classes2.dex` as a changed ZIP payload. Embedded class checksums differ for six synthetic ResearchEngine lambdas; dexdump disassembly is equal after stripping the two input-filename headers. All other ZIP payloads, including native libraries and licensed assets, match. This diagnostic does not prove complete binary/behavioral equivalence. The exact-hash gate was not relaxed, the rebuilt APK was not substituted into the measured manifest, and the newly rebuilt bytes have not received another fresh-install demo.

This is an unresolved build-tool reproducibility issue under the cached rig toolchain, not a hardware or private-coordinator blocker. A follow-up must determine deterministic DEX metadata generation and remeasure the resulting exact APK before freezing a later candidate. Normal cached builds and source/data reproducibility are not clean-build byte reproducibility. The application APK size changed between the historical 17,794,384-byte artifact and the regenerated 11,822,564-byte candidate while the recorded asset/native payload identities remained equal; the current verifier binds the exact measured artifact rather than assuming historical packaging equivalence.

Evidence: [passing build log](release-v2/build.log), [forced-build log](release-v2/forced-rebuild.log), [initial pre-rebuild verification](release-v2/initial-verification.txt), [final failed identity check](release-failures/rebuilt-apk-identity.txt). Signing/read-only and hook-order failures remain preserved separately. Product, physical, independent review and distribution gates remain open.

## Repair 100-release-preparation-repair-1

Recovered the three scoped implementation/evidence commits ending at failed checkpoint `ef02824667e6a145cdfa19cf8925a878783aac1e` onto the current checkpoint branch without changing application code, branches, orchestration or private state. The user-supplied critic result was invalid; no acceptance is inferred from it, and no private critic/builder logs were read.

Inspection of the installed AGP builder bytecode confirmed `setIncludeClassesChecksum(debuggable)` in its D8 archive builder and debug-mode checksum inclusion in the merger. The repair adds a final D8 compiler pass using the same installed compiler: D8 8.9.35, embedded in AGP builder 8.9.2, JAR SHA-256 `7dc1d36d12ee81300c5b1672aaae336d1c3cfe90a7b26b2b551389604150e53b`. The finalizer refuses a different JAR. D8 CLI `--debug --min-api 28` does not opt into incremental class checksums. This re-emits actual DEX, combines indexed DEX inputs, retains debug mode and leaves the application manifest debuggable for the emulator harness; it does not binary-patch or ignore unstable fields in the verifier.

Final packaging sorts ZIP entries with fixed timestamps, retains asset/library bytes and compression, removes old signature entries, applies SDK zipalign with 16 KiB native-page alignment and signs with the existing project-local debug key. Complete signed APK hashes remain the gate. Two initial forced builds and a second finalization produced SHA-256 `65edeb6553d8f2efc69dd6787e2ed9c6b8dab0f979324f21efa970b8fcafe89e`; the non-DEX/non-signature payloads match the measured v2 artifact. See [initial reproduction](release-repair/initial-reproduction.json) and its retained build logs. No global/compiler binary configuration was changed.

`tools/verify-release.sh` now executes two real forced builds on every invocation before exact frozen artifact and behavior checks. The reproduction helper preserves both APKs, logs and comparison records under ignored `downloads/release-repro/run-*`; unequal hashes or incremental class-checksum metadata fail the check. Earlier failed candidates and failures remain in `release/`, `release-v2/` and `release-failures/`; the replacement candidate receives a separate `release-v3/` manifest and fresh emulator measurement.

### Fresh v3 emulator evidence

Run `downloads/offline/run-20261001T023855Z` completed two fresh uninstall/install cycles on the existing AOSP API35 x86_64 emulator. Both verified no restored model/pack, real local SAF import, saved hashes and restart, corrupted-pack rejection and NPS source inspection. The first also rejected corrupt GGUF, invoked actual JNI generation, cancelled after streamed output and recreated/reloaded the Activity. Airplane mode remained on, Wi-Fi/mobile data off, Play Services absent, and application UID socket access denied with EPERM. The second fresh installation remains installed with imported assets. Original app data is archived only in the ignored run directory.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `app-debug.apk` | 11,769,461 | `65edeb6553d8f2efc69dd6787e2ed9c6b8dab0f979324f21efa970b8fcafe89e` |
| `qwen2.5-0.5b-instruct-q4_k_m.gguf` | 491,400,032 | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| `english-reference.plpack` | 159,327 | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |

The signer remains the v2 project-local debug certificate (`283b9d4b43c98e005181f85b13fd923664f856e7a6ca2d65a34444a1b7401fad`). The v3 manifest records 69 application/build-source hashes and 14 packaged asset/library identities.

| Exact question | Route | Tokens | AnswerEngine total ms |
| --- | --- | ---: | ---: |
| Compare evaporation and condensation | GENERATED | 62 | 26593.608 |
| What is groundwater? | FALLBACK | 39 | 29331.696 |
| quasar supernova | ABSTAINED | 0 | 0.115 |
| Does evaporation cure diabetes? | ABSTAINED | 0 | 2.024 |

Timing covers AnswerEngine after retrieval and excludes loading, imports and UI; it is one emulator pass, not phone performance. Streamed cancellation acknowledgement was 51 ms. The raw comparison remains imprecise/repetitive, and the unsupported groundwater draft is withheld. Two absent questions abstain without inference. See [verbatim raw drafts and published answers](release-v3/cycle-1-loaded-result.json) and [actual source inspection](release-v3/cycle-1-model-ui/source-dialog.png), visually inspected during this task. These outputs are real and are not template demo answers or quality acceptance.

### Final repair checks and limits

Both exact commands pass: `bash tools/android-build.sh` and `bash tools/verify-release.sh`. The latter independently repeats two forced builds, which both match the fresh-demo APK SHA-256 `65edeb6553d8f2efc69dd6787e2ed9c6b8dab0f979324f21efa970b8fcafe89e`; it then checks exact artifact/source/license/ABI/signer identities, permissions and dependencies, two deterministic pack builds, eight host behavior assertions, recorded real offline behavior and four rejected damaged-evidence mutations. See [final verifier output](release-v3/verification.txt), [build output](release-v3/build.log) and [two-build result](release-v3/reproduction-result.json). The verifier repeats the build tests, but replays the freshly recorded emulator evidence rather than uninstalling on every invocation.

This repairs the bounded failed byte-identity gate without weakening it. It establishes repeatability on the installed rig toolchain with the retained local debug key, not universal clean-machine reproducibility, production signing, physical Android/GrapheneOS behavior or useful-answer acceptance. The stated quality, coverage, resource, rival, independent review, release-holdout and distribution gates remain open. No private holdout, runner state or service was touched; no push, main advancement or bounty submission occurred.
