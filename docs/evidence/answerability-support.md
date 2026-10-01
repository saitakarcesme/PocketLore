# Answerability support: bounded public development repair

Measured on LLMRig on 2026-10-01. Current pre-model routing blocks **12/20 supported cases**, down from a fresh **14/20** pre-change baseline; all **10/10 absent cases remain blocked**. The two recovered questions produce real JNI-generated, source-contained sentences on the existing x86_64 Android emulator. This is a narrow development improvement, not useful-research, independent-review or physical-device acceptance.

## Frozen inputs and change

Commit `9a00e18` froze the current [baseline](answerability-support/baseline.json) and [additional public controls](../../tools/evaluation/answerability-cases.json) before the application edit. Baseline SHA-256 is `38743d8e47c433a3bc79d05f50c0ca86fc3b216a125bb5b2288114fbaeb35539`; control fixture SHA-256 is `9358ed5398460e9fde4e8e11fb30211b35a554b51cd27ae92e1cd251b8169f98`. The existing 30-question public retrieval fixture stays unchanged at SHA-256 `045270377a2cc1792cef27842147a770404eb3da32123aa9a702378a6313130c`. Private holdout was not accessed.

Production EvidencePrompt now treats the isolated coverage token `UV` as `ultraviolet` and contiguous `back up` as `backup` (existing plural normalization handles `backups`). These equivalences apply only to question/excerpt coverage checking. Original excerpts, retrieval ranking, source selection, prompts and AnswerEngine claim/temporal validation are unchanged. No broad qualifier removal or model-specific expected answers were added.

| Host production routing, null generator | Before | After |
| --- | ---: | ---: |
| Supported blocked before model availability | 14/20 | 12/20 |
| Supported reaching model availability | 6/20 | 8/20 |
| Absent blocked | 10/10 | 10/10 |

All previously eligible cases remain eligible. The [final host rows](answerability-support/final/after.json) preserve exact questions and measurements. This host test excludes model inference and does not measure answer correctness. Three additional frozen negative questions about ultraviolet diabetes treatment, Nepal legal requirements and live road closures also remain blocked on host and emulator.

## Actual Android JNI results

The existing `emulator-5560` was booted, x86_64 API 35, airplane mode enabled; its [fingerprint](answerability-support/final/fingerprint.txt) is preserved. No emulator or service was launched or restarted. Instrumentation calls the production retrieval, AnswerEngine and JNI runtime using the existing saved GGUF and an isolated test pack directory. Both recovered questions have nonempty raw drafts and prompts, positive token counts and `invoked_model=true`; all 13 absent controls abstain without invocation or tokens.

| Exact question | Route | Tokens | First token (ms) | End to end (ms) |
| --- | --- | ---: | ---: | ---: |
| What helps protect skin and eyes from ultraviolet rays? | GENERATED | 29 | 21,456.071 | 24,141.212 |
| What navigation backups should I bring? | GENERATED | 13 | 22,136.299 | 23,344.532 |

Final pack load was 195.291 ms and model load 169.299 ms. First-token timing runs from entry to AnswerEngine.answer through its first JNI token callback, including evidence selection and context budgeting; end-to-end includes retrieval and answer processing, excluding model/pack loading, UI and import. These single-pass CPU emulator timings are not phone latency, p50/p95 or thermal evidence.

Actual final text:

> [essentials-f1c425461e39b7df] Sun protection is necessary to protect your skin and eyes against harsh UV rays that are responsible for sunburns and skin cancer.

> [essentials-73b0434df1921710] Bring a physical map as a back up.

Both are copied sentences from the supplied NPS Ten Essentials excerpts, whose URLs, dates, rights and complete supplied text are retained in [raw results](answerability-support/final/results.json). They were produced by the real model, not inserted templates or the extractive fallback route. The sun answer is weakly actionable: it omits the sunglasses, sunscreen and hat suggestions in its source. The map answer supplies one supported backup recommendation. Source-contained generation does not establish useful explanation or synthesis.

The final checker verifies that each published sentence occurs in its cited source and in the supplied prompt, and that cited IDs cover the frozen required evidence group. This conservative audit accepts these verbatim outputs; it is not a general paraphrase-entailment evaluator and can reject otherwise supported paraphrases. The checker preserves and distinguishes fallback or model abstention if those occur, rather than counting invocation as generated support.

## Identity and raw evidence

| Artifact | SHA-256 |
| --- | --- |
| Measured app APK, 11,769,461 bytes | `2457ee6c474d1d6b8f6447ed2a698b2b491ea1f03208ab7b78ab5eec9796fd7d` |
| Test APK, 233,402 bytes | `fac25093ef95576bd8c9971d1eeca7681f34c2e8ddd37d59aea5dc23172d3053` |
| Qwen2.5-0.5B Q4_K_M GGUF, 491,400,032 bytes | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| English reference pack, 159,327 bytes / 186 passages | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |
| Final raw results | `6bc29cb2855e58b11f9c1cf0b58746af980cab5fe6498c778c37a2b218eea43e` |
| Exact test protocol | `399c102282521162a2998931ee2cc9286b1675341d1d6c8f5837c09900b0c0d8` |

Runtime reports llama.cpp `bb4caa7540188872173c44d161602d9271386413`, CPU, 2,048-token context, one sequence/session, FP16 KV and two threads. Its full identity and system prompt are in each result file. The identity also describes Qwen3 settings; this run uses the saved Qwen2.5 model, not Qwen3. No new assets or licenses were introduced; existing attribution remains intact. APKs and model/pack assets stay ignored.

The first complete JNI run is preserved separately: [raw results](answerability-support/first/results.json), [summary](answerability-support/first/summary.json). Its outputs were identical, with end-to-end times 26,208.005 ms and 23,298.734 ms. The second run added the discriminating source-contained sentence audit after inspecting the first output; no app, fixture or prompt tuning occurred between runs. Neither run failed. Prior rejected temporal-transfer drafts and earlier project failures remain preserved, not replaced by these results.

## Checks and remaining limits

Both requested checks exited 0:

- `bash tools/android-build.sh`: [standalone build log](answerability-support/standalone-build.log).
- `bash tools/evaluation/check_answerability.sh`: [final summary](answerability-support/final/summary.json), [build](answerability-support/final/build.log), [instrumentation](answerability-support/final/instrumentation.txt), [15 coverage controls](answerability-support/final/coverage-controls.txt), [temporal regression](answerability-support/final/temporal-regression.txt).

The behavioral checker reruns all 30 frozen host questions, enforces the current baseline and strict improvement, preserves all previous eligible cases, tests 13 absent controls through real Android production routing, and invokes real JNI for both recovered cases. The existing rejected groundwater speed transfer must still be withheld while the corrected comparison remains generatable. Current APK bytes were checked against the final measured hash after validation.

Twelve supported cases remain blocked. Wider paraphrase coverage, qualifier-sensitive reasoning and useful multi-source answers remain unresolved. Retrieval still supplies off-topic context (including a historical Declaration passage for the navigation question); it was not cited in the generated answer. Lexical checks and this two-case verbatim audit do not prove general factual entailment or independent quality. No UI lifecycle, fresh install, physical ARM64/GrapheneOS or unseen release evaluation was newly claimed by this task.

The prior v3 release APK/manifest is a historical freeze and does not describe this changed app. A new candidate freeze and release-identity validation are required after subsequent product work; the old exact-identity check has not been weakened. Release work and external hardware/human review gates remain open. No orchestration, private state, branch switch, push or main advancement occurred.
