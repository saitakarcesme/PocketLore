# Multi-pack development candidate — task 202

**The new development candidate is frozen and revalidated on LLMRig and the existing emulator-5560. It is not a published or accepted release.** Both required commands pass: `bash tools/android-build.sh` and `bash tools/verify-release.sh`. The latter performs same-rig forced-build reproduction and exact evidence replay; the separately executed fresh demonstration performed real installation, local SAF imports and JNI inference. No physical Android/GrapheneOS device was attached.

## Exact candidate and reproducibility

[Release-v4 manifest](release-v4/manifest.json) pins the full signed APK, **every APK ZIP member**, all DEX/native/asset bytes, imported model and both pack bytes, build/source recipe hashes, public debug signer fingerprint, refreshed distribution inventory digest and each public demonstration record. It records source checkpoint `ee4e3a7` at freeze; subsequent changes are evidence/documentation only. Old release/v2/v3 manifests and failed identities remain unmodified. The initial old-verifier failure is preserved in [stale-release-check.log](release-v4-history/stale-release-check.log): the current APK differs from the old release-v3 APK, as it must after product changes. That failure was not turned into a historical pass.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| app-debug.apk | 11,921,193 | `934147a471c948ea77de51d89663759a2925351c382f5412287535017e67a1f5` |
| classes.dex | 129,128 | `1e34b17a4c2ec459555f74d7ffda1a36a78f66de393ff041735bc49ed3f7e553` |
| ARM64 libpocketlore.so | 5,597,736 | `c96d261ff54d05b43473da9ebecf9d849dbe4c366d2aa7ee296752f6ec1685c8` |
| x86_64 libpocketlore.so | 6,077,192 | `28ce62513468da1b4c766751f296409e5ce124ff04e51a28d665c95d0f4babcc` |
| Qwen2.5 0.5B Q4_K_M GGUF | 491,400,032 | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| Reference edition | 159,327 | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |
| Science edition | 31,183 | `c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274` |

Public debug certificate SHA-256: `283b9d4b43c98e005181f85b13fd923664f856e7a6ca2d65a34444a1b7401fad`. No private signing material was published or production key generated. Native llama.cpp remains `bb4caa7540188872173c44d161602d9271386413`, CPU ARM64/x86_64; production/demo GGUF remains revision `9217f5db79a29953eb74d5343926648285ec7e67` of Qwen/Qwen2.5-0.5B-Instruct-GGUF. Optional Qwen3 measurements remain optional, not a deployment rename.

Two forced builds in each release-verification invocation reproduce the complete signed APK exactly using installed rig tooling/key and retained caches. No DEX identity is excluded; classes.dex is the sole DEX member in this candidate. This does not establish independent clean-machine reproduction, a portable signing identity or source-cache acquisition on another machine. [Build log](release-v4-history/android-build.log), [freeze verification](release-v4-checks/freeze-check.log) and [required final release command](release-v4-checks/release-check.log) preserve actual outcomes and paths to ignored build artifacts.

## Fresh offline demonstration

The declared [task202 protocol](../../tools/release/multi-pack/protocol.json) was committed at `3c4041d` before the fresh run. `python3 tools/release/multi-pack/fresh.py` ran once, under ignored `downloads/release-multi-pack/run-20261001T071547515600Z`. It archived only the known PocketLore fixture app data, validated safe tar member paths and preserved its hash/size receipt before uninstalling PocketLore and its test package. The ignored archive is retained; no archived data was restored and no unrelated data/package was removed.

1. Fresh installation asserted no saved GGUF and no retained catalog entries in process 12487. Bundled starter data is not counted as an imported pack. [Fresh record](release-v4/fresh.json).
2. Real Android DocumentsUI/SAF selection imported the local pinned model with its copy-size confirmation, then reloaded it after process restart. [Model UI receipt](release-v4/model-ui/result.json) and XML/screenshots record the actual controls; this was not direct replacement of `files/model.gguf`.
3. Separate real DocumentsUI/SAF imports installed reference and science. [Reference](release-v4/reference-ui/result.json) and [science](release-v4/science-ui/result.json) receipts and archive hashes agree with the frozen assets. Both remain installed.
4. Process 13175 loaded both active editions: **18 distinct documents and 210 passages**. It ran actual JNI for “What is magma?”, then inspected source buttons for both reference and science with the model deliberately unloaded for that separate UI check. It disabled science through **Choose collections / Apply**, leaving 186 active passages.
5. Process 13282 restarted with the saved model ready and science still disabled; `magma lava` retrieved no science evidence. It re-enabled science through the same real controls.
6. Process 13334 restarted with both collections active, 18 documents/210 passages and saved model ready. It performed a second real JNI request and source-dialog checks. Final catalog and saved model/archive hashes match the expected pinned assets. The fixture ends with both collections enabled; the saved model loads on next app launch.

[Summary](release-v4/summary.json) and [combined](release-v4/combined.json), [disabled](release-v4/disabled.json), [enabled](release-v4/enabled.json) records preserve outcomes. Counts in mode records describe the state **after** that mode's selection changes: combined ends reference-only; disabled ends re-enabled; enabled ends with both active. Distinct PIDs establish process restart rather than only Activity recreation.

Airplane mode remained 1, Wi-Fi 0 and mobile data 0. Actual APK permissions contain no `uses-permission` entries; debugRuntimeClasspath has no dependencies; Google Play Services and Play Store packages are absent. This is emulator permission/radio-state evidence, not packet capture or physical-radio certification. There is no research-time network fetch or remote inference. Source URLs remain provenance labels.

## Actual generated output and source inspection

Both actual JNI requests used the unchanged production controller/model on the combined catalog and produced GENERATED with 30 tokens:

> [S1] Scientists use the term magma for molten rock that is underground and lava for molten rock that breaks through the Earth's surface.

S1 resolves to `pc69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274_science-magma-b214c1cb4647b3fc`. The prompt includes the exact USGS definition, and the builder finds this literal answer supported by that cited excerpt. It repeats source wording; it is not evidence of useful comparison or multi-source synthesis. No canned answer, null generator or extractive fallback was substituted. Independent source/human review remains open.

First-token/AnswerEngine-total times were **21,346.846 / 24,487.777 ms** and **21,277.429 / 24,402.536 ms**. Definitions match production controller timing after retrieval; these exclude import/model-load/startup and are two emulator observations with retained OS caches, not percentiles or physical performance.

Eight actual source-button dialogs (four in each combined-catalog process) match exact passage, namespace, URL, dates, rights and collection/source/passage hashes. The builder visually inspected [the final science dialog](release-v4/enabled-combined-1.png). Those source-button runs are explicitly FALLBACK with model unloaded and receive no generated-answer credit; task201 separately measured real generated ClickableSpan navigation on the same APK. Neither UI path nor structural citation checks establish broad factual entailment.

## Release verification and distribution inventory

The release checker retains the existing checks for forced APK reproduction, actual permission/dependency/license/native audit, deterministic reference-pack rebuilds and host retrieval behavior. It now binds both editions, all APK members and the fresh multi-pack records. It additionally rebuilds science twice, checks active-selection persistence and actual source dialog provenance, and rejects seven damaged demo variants: absent inference, substituted question, restored fresh assets, lost disabled selection, wrong model hash, wrong science edition and missing dialogs. These are executed data-corruption controls, not manually asserted success flags.

The refreshed [distribution inventory](../distribution-inventory.json) matches the candidate and records 123 resolved build artifacts,13 static link inputs per ABI, all required notices, exact model/data licenses and source locks, and installed toolchain identities. Five existing negative inventory tests reject missing notice, changed native artifact, changed build artifact, missing component and false redistribution-readiness. Historical inventory is preserved [before refresh](release-v4-history/distribution-inventory-before.json). No new dependency or license was introduced, so THIRD_PARTY_NOTICES needs no attribution change. The inventory now explicitly distinguishes the imported production/demo 0.5B from optional evaluated/smoke models.

Sixty-four build artifacts have no detected embedded plain-text notice; local POM declarations exist, but that is not a redistribution clearance. Full terms review remains necessary before distributing build tools; they are not APK runtime dependencies. No toolchain bundle, weights, APK, private key or app-data archive was added to Git or published.

## Remaining gates and scope

This task changes tools/docs/inventory only; APK identity remains task201 repair's candidate. The [updated guide](../RELEASE.md) gives reproducible local import, selection and actual-output demo steps; README now reports both editions and the 25-POI catalog accurately.

Open gates: useful comparisons/multi-part completeness, claim-to-source support, broader title-derived scope evaluation, independent criticism and human usefulness; separate clean-machine reproduction; owner production signing/key custody/upgrade decision; physical Android/GrapheneOS installation and sustained RAM/disk/thermal behavior. Existing corruption/cancellation and two-cycle experiments remain historical, not falsely rerun for this new one-cycle demo. Task201's narrow literal success does not close those product gates. No release publication, bounty submission, push, main advancement, private holdout/context access, orchestration/state change or service restart occurred.
