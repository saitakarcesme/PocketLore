# Task 213: latest candidate audit; final freeze deferred

The approved scale replan is controlling: **defer final release freeze until task300 integrates the chosen model, bulk data and Android lanes**. Task300 reached a measured first-shard browse/import/JNI milestone, not that prerequisite. Qwen3 4B remains host-only, production remains Qwen2.5 0.5B, the full bulk inventory is not installed, and bulk source rights/support remain unqualified. This task therefore does not create a new final release manifest or claim a fresh release demonstration.

## Actual checks on the latest bytes

- `bash tools/android-build.sh`: exit0; APK `3d804882ea576fb5ebdd29144a88fa8002c99efbd97c45323928a7c8a1d2e98f`,15,669,266 bytes. [Build log](broad-candidate-release/build.log).
- `bash tools/verify-release.sh`: exit1. Its two forced builds reproduced this exact latest APK, then strict comparison with historical release-v4 failed on APK identity. [Full failure](broad-candidate-release/release-check.log). The stale manifest was not refreshed merely to make the check pass.
- Fresh dependency resolution succeeded with the absolute init-script path. The first relative-path invocation failed because the build wrapper changes directory into `android`; both logs are preserved.
- `python3 tools/release/audit_current.py --output docs/evidence/broad-candidate-release`: PASS for a **non-release current-byte audit**. [Audit log](broad-candidate-release/audit.log), [machine-readable inventory](broad-candidate-release/current-audit.json). It refuses to overwrite an audit or alter the historical release/inventory files.

This audit checks current installed APK bytes against the built APK, complete APK members (DEX, native, assets and signatures), actual static linker inputs for both inference and the newly packaged SQLite index runtime, immutable SQLite sources and full notice files, resolved build dependencies/toolchain identities, actual model and pack bytes, and installed reference/science/reviewed-broad archives/index. SQLite3.53.4 is separately linked for ARM64/x86_64; existing platform SQLite and llama.cpp remain separate. SQLite's notice is present and byte-matched in the APK. No new dependency was introduced by task213; task300's added public-domain SQLite notice and bulk-source limitations remain in THIRD_PARTY_NOTICES.

Eight regressions modify or remove real isolated copies of the APK, index shared library, component notice and actual JNI receipt; every mutation is rejected. This is artifact integrity, not a semantic-quality test. Original artifacts and records remain untouched. The audit also checks the unchanged SHA of the release-v4 manifest and its distribution inventory, and records those historical hashes. Task210 failed/evaluation-only editions and task211/212/300 evidence remain historical and unmodified.

## Existing installation observed, not a fresh run

All three original collections remain active:

| Edition | Archive bytes | SHA-256 |
|---|---:|---|
| English reference |159,327|`567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`|
| Science supplement |31,183|`c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274`|
| Reviewed broad rendered-v2 |46,339,444|`b8d18801b099402205938979ab2bb44ee9a316f06f030aab789cf93ba3605012`|

The reviewed broad SQLite index is121,401,344 bytes, SHA `9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386`. Saved model SHA remains `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` (491,400,032 bytes). Exact per-edition active state, on-device hashes and current filesystem allocation are retained in `installed_observation` of the audit.

Task300's [exact matching APK run](scale-integration/acceptance-run/run.json) and [JNI output](scale-integration/acceptance-run/native.json) are reused without regenerating the same answer. Its real controller generated the hands-free headlamp explanation with a cited NPS excerpt while the bulk catalog was present. That is a narrow supported small-pack control, not source-bound bulk generation or a newly measured generated citation navigation run. Task300 also preserves actual bulk source dialogs, selection persistence, corrupt/cancelled import rollback, model retention and same-process retry. Task211's reviewed-broad import/source/license checks and task202's old fresh demonstration remain labelled with their original candidates. None is relabelled as this task's fresh installation.

No app data was uninstalled, reset or restored in task213. No service/emulator was restarted. App source, model preferences/admission, production signing keys, private holdout, runner state, branches and main were unchanged. All compilation and hashing occurred on LLMRig; observed Android state is x86_64 emulator-only.

## Storage and memory reconciliation

The three archive files and reviewed-broad index total167,931,298 bytes. The model adds491,400,032 bytes. Task300's two installed bulk collections add2,596,716,782 bytes including their manifests. Together with the latest APK this known subset totals3,271,717,378 bytes, before other retained fixture files, extracted runtime/ART, caches and filesystem overhead. Fresh on-device `du` and `df` values are in the audit; these filesystem allocated bytes differ from logical file lengths.

The complete primary **host-staged** selection plus current model/APK remains about41.46GB before additional overhead. [Task300 budget](scale-integration/joint-budget.json) is not a full installed result. That task measured wiki import staging1,424,169,186 bytes plus its1,424,170,364-byte input archive, and places staging1,172,547,596 bytes plus its1,172,549,792-byte archive. Full-edition update peak remains unmeasured and can exceed the50GB constraint; preserving old assets rather than deleting them is required. The unchanged emulator has approximately1.8GiB free, insufficient for full-scale installation.

Task300's exact-APK memory/timing receipts remain the applicable latest observations: approximately35MiB sampled PSS for the oversized streamed source read and576,000KiB combined baseline-native/index PSS. Raw RSS/swap and timings are preserved there. These are reused measurements, not newly measured task213 opening peaks, selected4B behavior, phone RAM or thermal acceptance. The reviewed broad opening measurement in task211 is historical, not silently assigned to the current APK.

## Work that remains deferred

Final candidate freeze, fresh offline installation of the agreed complete selection, actual generated citation-span navigation, fresh corruption/cancellation/update/temp/cache and combined opening/native measurements must follow the scale prerequisite. A new release version must explicitly cover every current DEX/native component, selected model, data/index/rights disposition and dependency inventory; historical release-v4 and task210 failures must remain intact. Full installed/update≤50GB and selected-model admission require an approved sufficiently provisioned environment, without builder service changes.

Existing queued301 addresses shared shards/full-inventory/update and query coverage;302 addresses reviewed source-bound answers and depends on the separate answer-architecture work. Task213 does not duplicate those tasks or dispatch them. Some prerequisite implementation is still achievable independently on the rig, so this is **not solely a physical-hardware blocker**. Independent clean-machine reproduction, production-signing ownership, unseen matched independent comparison, physical Android/GrapheneOS and human acceptance remain separate open gates. No publication or superiority claim is made.
