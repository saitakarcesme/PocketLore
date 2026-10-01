# Task 201 repair 1 — actual generated citation navigation

**Both required checks now pass on LLMRig/emulator-5560. Answer usefulness remains open.** The failed checkpoint `151ffcf81afccfc6061b0ccd13dad99097c6e49f` and its complete negative matrix are preserved below; recovery cherry-picked its four commits onto the existing repair branch without switching branches or resetting application work.

Two literal citation-link cases were frozen at `1bd9c39`: “What is magma?” and “What are chromosomes made of?”, with pinned source excerpts and unchanged production model. They supplement rather than replace the original eight cases. The first repaired-harness run still failed: magma echoed a question-shaped source title, leaving a following sentence uncited; chromosomes echoed date/URL metadata instead of a factual answer. [Every before-run draft and receipt](multi-pack-answers/repair-before/results.json) remains preserved. There was no seed search or third set of questions.

The bounded product repair, declared before execution at `5657100`, separates model-facing factual evidence from navigational metadata. `EvidencePrompt.build` now supplies source labels, original source dates and verbatim excerpts; titles/URLs remain intact in the actual source dialogs and catalog provenance. Model pin, generation grammar, decoding, context/admission limits and all support/temporal guards are unchanged. This is not post-generation cleanup or a fallback promoted to GENERATED. Titles can convey useful scope, so broader historical/title-dependent behavior needs later evaluation; dates and excerpt qualifiers remain supplied. This narrow result is not a general quality improvement claim.

## Actual repair results

One before/after matrix used exactly the same eleven requests (original eight, cancellation, two frozen literal cases), original pack hashes and active catalog. The after-run has **three GENERATED, five ABSTAINED, two FALLBACK and one CANCELLED**; nine requests invoked JNI, including cancellation. [Raw results](multi-pack-answers/repair-after/results.json), [receipt](multi-pack-answers/repair-after/receipt.json), [summary](multi-pack-answers/repair-after/summary.json) and [separate builder assessments](multi-pack-answers/repair-after/builder-assessments.json) retain all prompts, drafts, actual selected excerpts, source IDs, routes, tokens, timing and memory samples.

| Case | After route | Builder source review |
| --- | --- | --- |
| reference / duplicate / after-reload | ABSTAINED | Model declines despite available hands-free evidence; duplicate prompt and raw answer remain identical. |
| science / after-cancel | GENERATED | Says magma and lava are molten rock that can erupt. Omits underground versus surface; “types” wording is not certified as fully supported. Incomplete comparison; no useful-comparison credit. |
| cross-pack | FALLBACK | Still invents a destination-focus/physical-movement benefit and omits geology; correctly withheld. |
| disabled-science / absent | ABSTAINED | No model invocation; disabled science excluded and cat chromosome count unavailable. |
| cancel-prefill | CANCELLED | Actual native prefill observed; no publication. |
| literal-magma | GENERATED | Exact cited definition of magma underground and lava breaking through the surface; supported and complete for this literal question. |
| literal-chromosomes | FALLBACK | Correct material fact appears in S2, but draft cites S1 etymology; correctly withheld. |

The literal magma raw JNI output is:

> [S1] Scientists use the term magma for molten rock that is underground and lava for molten rock that breaks through the Earth's surface.

S1 is the exact frozen USGS excerpt. This is actual production model generation, with 30 output tokens and 21,766.600 ms first-token / 25,029.083 ms controller-total time; it repeats source wording and does **not** establish explanation or multi-source synthesis quality. Only this one literal request receives builder fully-supported/complete/useful credit. The comparison wording remains uncertain and incomplete; no claim of zero unsupported publication or broad safety improvement is made. Independent source review is pending.

The real answer TextView's ClickableSpan was invoked for science, after-cancel and literal-magma. Three actual dialogs matched full edition-qualified citation, passage, URL, date, rights and collection/source/passage hashes. [Literal magma screenshot](multi-pack-answers/repair-after/literal-magma-citation.png) was visually inspected by the builder and shows the generated answer behind its correct source dialog. Unlike the original supplemental source buttons, this directly exercises generated citation navigation; no synthetic outcome or alternate source-button path satisfies the gate.

## Recovery and limits

Both active packs still provide 18 distinct documents / 210 passages / 2052 vocabulary terms / 6922 postings / 69,818 indexed text characters. Original two-active catalog, saved model and legacy reference bytes are restored unchanged; temporary duplicate aliases do not inflate the index. The production/demo model remains Qwen2.5 0.5B Q4_K_M SHA `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`, not optional Qwen3. Exact active pack hashes remain those in the original protocol and report below.

After-run prefill cancel click-to-idle is **106.506249 ms**; startup-to-ready **1422.371024 ms**, explicit reload-to-ready **441.019101 ms**. The largest prompt is 498 tokens, plus the fixed 256 output budget, within 2048; largest actual output is 30. Native contexts release after each request, and model lease reaches zero on unload then one after reload. No allocation failure observed. These are single emulator observations with warm OS caches, not phone or isolated load benchmarks.

Sampled process peaks: **684,231 KiB PSS**, **771,412 KiB RSS**, **23,900 KiB VmSwap**, **26,737,536 Java used bytes**. Native buffer maximum remains **589,327,360 bytes** (model 485,452,288 + KV 25,165,824 + compute 78,709,248). Samples include combined index, model, Activity and instrumentation; they do not isolate index costs or prove natural OOM safety. No host RAM is relabeled as phone RAM.

## Checks, identity and remaining work

- `bash tools/android-build.sh`: **exit 0**, [standalone log](multi-pack-answers/repair-after/android-build.log).
- `bash tools/evaluation/check_multi_pack_answers.sh`: **exit 0**, [actual JNI log](multi-pack-answers/repair-after/check.log). The generated-span gate remains mandatory. Original failed runs are retained separately.
- Existing CompleteClaimCheck and TemporalScopeCheck: **exit 0**, [log](multi-pack-answers/repair-after/guard-regressions.log): eleven unsupported historical drafts remain withheld, fourteen malformed/absent regressions and complete-clause boundaries pass, and the rejected temporal transfer remains withheld. These are controller replays, not new generated quality evidence.

The new APK is 11,921,193 bytes, SHA-256 **`934147a471c948ea77de51d89663759a2925351c382f5412287535017e67a1f5`**. Task202 must revalidate this changed identity and model-facing context in its release/offline checks; old release receipts do not cover it. No model asset, attribution or admission limit changed. Broad answer coverage, citation support, multi-part completeness, title-derived scope, independent review, physical/GrapheneOS and human acceptance remain open. No services, runner/state, private holdout/context, task dispatch, branch switch, push or main advancement occurred.

---

## Preserved original task 201 failure report (historical)

The following section describes the original pre-repair APK and negative run, not the latest check status.

# Production JNI against the multi-pack catalog — task 201

**Negative result; behavioral acceptance check fails.** The current production model published no generated answer on this frozen matrix, leaving actual generated citation-span navigation unexercised. This is neither product acceptance nor proof that fallback retrieval is useful synthesis. All compilation and inference ran on LLMRig; actual JNI ran serially on the existing x86_64 Android emulator-5560, offline. No physical or GrapheneOS device was tested.

## Frozen inputs and identity

Commit `8373938` froze [protocol.json](../../tools/evaluation/multi-pack-answers/protocol.json), eight public cases, exact source blocks, hashes and expectations before generation. Harness commit `b4223cf` used actual MainActivity controls, retrieval, NativePanel, EvidencePrompt, AnswerEngine and native runtime. There was one matrix, with no prompt/seed/model search, no evidence substitution and no controller bypass. Two recovery repetitions and the duplicate repetition are not independent quality cases. No private holdout, private context, services or orchestration were accessed/changed.

- **Production/demo:** Qwen2.5-0.5B-Instruct Q4_K_M; repository `Qwen/Qwen2.5-0.5B-Instruct-GGUF`, revision `9217f5db79a29953eb74d5343926648285ec7e67`, SHA-256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`, 491,400,032 bytes. Optional Qwen3 task190/200 results do not describe this deployment.
- **Native:** llama.cpp `bb4caa7540188872173c44d161602d9271386413`; CPU, two threads, single session/sequence, 2048-token context, 256 output tokens, f16 KV, default greedy for this model. The generic identity string also names Qwen3 settings, which are not this model's role.
- **App:** SHA-256 `2d1588d0f9ddc1227621ad28afe3fcb329f7619599368d9357ac6c10d145b26a`, 11,921,193 bytes, unchanged from task200-multi-pack-library. No production source or admission/model setting changed in task201. Runtime/controller source hashes and test APK identity are in the [receipt](multi-pack-answers/failed-matrix/receipt.json).
- **Reference:** `english-reference-2026-10-01`, 159,327 archive bytes, SHA-256 `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`, ten documents/186 passages.
- **Science:** `science-supplement-2026-10-01-v1`, 31,183 archive bytes, SHA-256 `c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274`, eight documents/24 passages.

Both active editions yield 18 distinct documents, 210 passages, 2052 vocabulary terms, 6922 postings and 69,818 indexed text characters. These are narrow licensed excerpts, not broad research coverage. IDs are `p<full edition SHA>_<original citation ID>`. Exact source hashes, dates, rights and original IDs are retained in the frozen protocol and every retrieved record. Duplicate test archive changes only the reference manifest edition ID; unchanged real passages do not create factual coverage. Its hash and bytes are in the ignored run and receipt.

## Actual results and builder source review

Raw [results](multi-pack-answers/failed-matrix/results.json) include every draft, resolved citations, selected excerpts, prompt, output route, active hashes and timing; individual case JSON files provide smaller review inputs. [Builder assessments](multi-pack-answers/builder-assessments.json) are explicitly separate from pending independent source review. Citation syntax and lexical overlap are not entailment evidence.

| Frozen case | Route | Prompt/output tokens | First token / controller total ms | Builder assessment |
| --- | --- | --- | --- | --- |
| reference: why headlamps at night | FALLBACK | 504 / 35 | 25892.132 / 29765.496 | Draft cites S2 Constitution and says it recommends headlamps. Its excerpt does not; the hands-free fact is in uncited S1 NPS. Unsupported attribution. |
| science: compare magma/lava | FALLBACK | 551 / 25 | 28426.318 / 31112.312 | “Distinct terms … different types of molten rock” omits underground versus surface; different rock types are not established by the definition. No fully supported useful comparison credit. |
| cross-pack: geology plus headlamps | FALLBACK | 418 / 29 | 21448.103 / 24599.269 | Hands-free is supported, but “without the need for physical movement” and added focus benefit are not. Entire magma/lava part omitted despite its selected excerpt. |
| disabled-science: compare magma/lava | ABSTAINED | 0 / 0 | 0 / 0.159 | No model call and no disabled science evidence in retrieval/prompt/answer. |
| absent: domestic cat chromosome count | ABSTAINED | 0 / 0 | 0 / 2.007 | Generic chromosomes passages do not establish a cat count; safely withheld before JNI. |
| duplicate: repeat headlamps | FALLBACK | 504 / 35 | 25685.424 / 29547.170 | Identical original prompt and raw output; duplicate alias neither improves nor degrades this output. Same wrong attribution. |
| cancel-prefill: headlamps | CANCELLED | 504 / 0 | 0 / 57.097 | Actual observed native phase 4 before cancellation; no published partial draft. |
| after-cancel: magma/lava | FALLBACK | 551 / 25 | 28381.404 / 31076.530 | Same incomplete comparison; successful operational recovery is not quality. |
| after-reload: headlamps | FALLBACK | 504 / 35 | 25642.401 / 29578.543 | Same unsupported attribution after actual model unload/reload. |

There were seven invoked requests (six finished drafts and one cancelled prefill), two non-invoked abstentions, **zero GENERATED**, six FALLBACK and one CANCELLED. Zero supported/complete/useful generated publications were observed; zero unsupported generated publications were observed because nothing was published as generation. The six drafts have complete surface sentences, yet do not satisfy requested semantic support/completeness. The final-word guard rejects the headlamp drafts with a surface-word reason; this is not evidence it diagnosed the actual incorrect source binding. The science drafts are rejected for weak lexical support. All raw failures remain intact.

The cross-pack prompt includes the NPS hands-free excerpt and exact USGS underground/surface definition. Failure here cannot be explained solely by retrieval missing the geology source. The production small model and controller remain an internal product limitation. Next concrete repair: coverage-aware evidence selection and explicit per-part completeness/source binding, evaluated against these preserved failures; do not infer that deploying an optional model alone solves it.

## Recovery, budgets and memory

- Actual prefill state was `[4,0,2,504,5,0,485452288,25165824,78709248]` before the real Cancel button. Click-to-idle including record/persistence overhead: **107.807322 ms**. One sample, no universal latency guarantee.
- Startup-to-ready: **1421.934141 ms**, including Activity/catalog/model setup. Explicit reload-button-to-ready: **434.422840 ms**. These are not isolated load benchmarks or storage-cold measurements; OS caches remain.
- Model lease reaches zero on unload and one after reload; all completed rows show zero retained native contexts. After-cancel and after-reload both invoke JNI and finish normally as fallback.
- Largest prompt 551 tokens plus fixed 256 output budget = 807, below 2048. Largest actual output 35 tokens. No budget/admission alteration; no real allocation failure observed. This small catalog does not test admission boundaries again.
- 652 samples, nominal 250 ms interval plus explicit unload snapshot: peak PSS **684,041 KiB**, RSS **772,296 KiB**, VmSwap **23,900 KiB**, Java used **26,770,304 bytes**; Java maximum 201,326,592 bytes. Largest sampled VmHWM 789,264 KiB (OS high-water mark differs from sampled RSS maximum).
- Active native buffers: model 485,452,288 + KV 25,165,824 + compute 78,709,248 = **589,327,360 bytes**. These reported buffers are not total process footprint. After unload, a sample records PSS 110,549 KiB, RSS 198,308 KiB and zero native leases/contexts/buffers.

PSS/RSS/Java values include Activity, catalog, model, instrumentation, stored rows and source strings; they are not isolated index allocations. They are sampled emulator process memory, never host RAM relabeled as phone memory. No OS OOM, natural low-memory pressure, thermal or long-session claim follows. Original two-active catalog bytes, saved GGUF and legacy reference hashes match before/after; fixture cleanup removed only the duplicate archive through the existing library manager.

## Source inspection separately from generated links

The strict generated-link assertion fails because there is no GENERATED outcome. It was not weakened and no outcome was fabricated. After preserving that failure, commit `5bd387c` declared a separate [source-button plan](../../tools/evaluation/multi-pack-answers/source-inspection-plan.json). The same frozen cross-pack question ran with the model unloaded, using real Search, Inspect source and Choose collections controls. This is a discriminating UI test, not another inference attempt or quality success.

[Supplemental records and screenshots](multi-pack-answers/source-buttons/results.json) show six actual source dialogs: four with both editions, then two reference-only after disabling science. Each asserts exact text, URL, date, rights, full citation and edition/source/passage hashes. Combined route FALLBACK; disabled route ABSTAINED; no model invocation. The builder visually inspected [the science dialog](multi-pack-answers/source-buttons/combined-1.png); the namespace and full provenance are displayed. Model unload is fixture-only; saved bytes/catalog remain retained. The JNI matrix, not this supplemental test, supplies load/cancel/reload readiness evidence. Generated citation-span navigation remains unverified for this production model/catalog.

## Checks and reproduction

- `bash tools/android-build.sh`: **exit 0**, [log](multi-pack-answers/android-build.log).
- `bash tools/evaluation/check_multi_pack_answers.sh`: **exit 1**, [original log](multi-pack-answers/failed-matrix/check.log), full actual instrumentation and receipts preserved. It loads the already provisioned two pinned packs and model, builds/installs the test APK, executes actual JNI, records and restores fixtures. It does not download or select a model.
- The verifier was subsequently arranged to evaluate the remaining assertions before reporting the final gate failure. `bash tools/evaluation/check_multi_pack_answers.sh --verify-recorded downloads/multi-pack-answers/run-20261001T064046900406Z`: **exit 1**, [log](multi-pack-answers/recorded-verification.log). Recorded artifact/source hashes, source provenance, bounds, disabled/absent routes, duplicate equality, cancellation/recovery and native sampling assertions pass; generated-link gate still fails. No second matrix was run to improve outcomes.
- Supplemental SourceLibraryInstrumentation: **INSTRUMENTATION_CODE -1**, PASS with six dialogs. Compile via `bash tools/android-build.sh assembleDebug assembleDebugAndroidTest -I "$PWD/tools/evaluation/multi-pack-answers/source.gradle" -PpocketloreTestRunner=org.pocketlore.app.SourceLibraryInstrumentation`, install the generated androidTest APK, force-stop only the fixture app, then `adb -s emulator-5560 shell am instrument -w org.pocketlore.app.test/org.pocketlore.app.SourceLibraryInstrumentation`. Results are `files/multi-pack-source-tests/results.json` under app run-as. Do not launch another emulator/service. The core check builds its own runner when next invoked.

No raw measurement was edited. Original receipt references the ignored duplicate `.plpack`; it is not a missing committed artifact: binary fixture/model/APKs remain ignored as required. Public raw JSON, logs and screenshots are retained; source identity is the committed harness at b4223cf, and the source-only supplement at 5bd387c. The revised verifier adds recorded-run inspection without changing generation inputs or production code.

Task202 release identity/offline revalidation remains dependent work. A generated answer-quality/source-binding repair and successful actual generated-link test are achievable rig work; hardware absence is not their blocker. Independent canonical criticism is pending; physical/GrapheneOS, human usefulness and release acceptance remain open. No push, branch switch, main advancement or task dispatch occurred.
