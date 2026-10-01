# Guarded independent linking: task 222 repair 1

Both required commands pass: `bash tools/android-build.sh` and `bash tools/evaluation/check_independent_evidence_linking.sh`. This is a bounded retrospective development repair, not independent acceptance or held-out generalization. Builder source review records **5/40** fully supported, complete, useful old answers, **zero unsupported eligible outputs** across103 records, and all **8+1 absent controls withheld**. Only **1/16** previously frozen new generated answers remains useful and eligible. The independently trained classifier alone still fails, with eight unsupported eligible records.

## What changed

Recovered checkpoint `231c686f36f9a3abb64de429b1ae334edb86d78c` by cherry-pick on the current checkpoint branch; its failed checks, APK mismatch, raw scores and conclusions are preserved. The resumed branch already contained task221 repair2's finite source-frame implementation. A first edit helper assumed the reuse commit was present and stopped before writing; [setup failure](guarded-linking/setup-failure.txt) records that recovery mistake.

Commit `2b5b64b` declares the composition protocol before its replay. `GuardedEvidenceLinker` now requires both stages:

1. The unchanged independently trained classifier controller must admit every complete claim and sentence at its fixed thresholds and token bound.
2. The separately implemented finite semantic parser must ground every full generated clause in exact source relations, including subject, direction, formula meaning and material conditions/time. Unknown or unsupported tails withhold the entire answer.

Final typed citations come from the semantic proof, not the classifier's chosen neighboring passage. The controller records classifier-selected references separately from final references; those are not interchangeable approvals. For example, the classifier still chooses the wrong mixture definition for the correct vermicast output probe p01; the final semantic proof binds the actual end-product definition. A positive classifier score does not establish that final source's entailment. No classifier-rejected answer can bypass the first stage, and no semantic rejection can be overridden by high classifier scores. The generated text, obligation and visible subject headings remain unchanged. This architecture does not drop extra sentences or convert quotes, W or fallback into generated success.

No old or new generation, classifier inference, threshold, prompt, seed, model, frozen fixture or manual expectation was changed. All60 old drafts,11 historical wrappers,16 new generated cases and16 constructed probes are reused, with994 exact real scores. The independently trained Apache-2.0 DeBERTa artifact and CPU runtime remain as pinned in [the historical report](independent-evidence-linking.md). The16 new questions were frozen before the original inference, but this repair sees their outcomes: its result is explicitly retrospective. Constructed probes remain tests, not corpus or generated successes.

The semantic implementation itself is unchanged from task221 repair2 and hash-checked against that replay. It is a narrow corpus-informed controlled-English adapter, not general natural-language entailment. The safety improvement belongs to this additional semantic veto and source binding, not improved classifier accuracy. This is materially different from merely updating an APK receipt or replacing a failing check with the frame-only result: the acceptance script actually executes the composed shared controller with real classifier scores, confirms both stages remain necessary, and evaluates its final prose and references.

## Actual result and source review

| Population | Classifier-only eligible | Guarded eligible | Guarded useful generated answers |
| --- | ---: | ---: | ---: |
| Old48, including8 absent |10|5|5/40 supported questions |
| Previous new12, including1 absent |5|1|1 |
| Frozen new16 |5|1|1/16 |
| Historical11 wrappers |3|1|Not fresh generation |
| Constructed16 probes |6|1|Not generation |
| Total |29|9|Do not combine these denominators |

Seven of the eight previously unsupported records now withhold: s10, s22, n02, n07, r01, r09 and p08. The eighth, p01, retains correct prose with a repaired definition binding; its old incorrect classifier binding remains in `classifier_claims`. The old useful eligible answers are s16, s19, s31, s40 and s46. Previous-new n10 and new l11 retain the correct fifth-root interpretation; historical r06 binds products and temperature to their proper sources. All remaining94 records withhold. There is no extractive route.

Each of the nine eligible final outputs and attached spans was rechecked during this repair. They match the already source-reviewed frame outputs byte-for-byte, including visible question/subject headings and typed links. [Builder review](guarded-linking/review.json) preserves claim-level reasons and binds them to exact current records. Codified-versus-written wording is evaluated with its explicit single-or-set definition; the2.512 magnitude ratio is evaluated as a finite displayed rounding of the fifth root, not exact real-number equality. Independent reviewers should assess these interpretations directly, not accept proof labels or builder labels as ground truth.

[Raw final output](guarded-linking/replay/results/linked.json) includes both classifier and final bindings; [original raw prose/scores](independent-linking/scoring) remains immutable. [Review input map](guarded-linking/independent-review-inputs.json) supplies sources and expectations without builder judgments. The n08 Athens renderer case remains a behavioral context regression, not a published success. Supported false-premise corrections and useful paraphrases rejected by the finite parser remain explicit coverage losses: new useful coverage falls5/16 to1/16 and old coverage8/40 to5/40. No broad product-quality improvement is claimed.

## Validation and resources

The required check performs the complete historical artifact/runtime/source validation and103-record replay first, reporting the historical quality failure as diagnostic evidence. It then compiles and replays the new composed controller and enforces the final zero-unsupported, >4/40 and nine-absent gates. Historical diagnostic mode is only a reusable check stage; the top-level acceptance command cannot pass on it alone. It verifies actual model, classifier, runtime installed files, source index/provenance, scores, drafts and current APK, and rejects changed/missing classifier, generator and result artifacts.

The77 behavioral tests comprise29 original linking/renderer tests,39 semantic tests and9 composition tests. Composition controls show that missing, over-budget or NaN scores cannot be bypassed; perfect mocked classifier scores cannot approve reversed subjects, negation or an unsupported extra sentence; cancellation aborts and a fresh transaction retries. The inherited suite covers source namespace/corruption and formula/article bracket links. Constructed scores are unit tests only; the full replay uses real immutable scores. Real JNI/ONNX execution was not repeated and these tests do not establish in-flight ONNX cancellation, OS OOM safety or Android selected-model execution.

Current APK:11,937,577 bytes, SHA256 `2d04838f2bf676b474e355d93e5228b775acc4d444a17f8eee1542b6bd51b1db`. [Build log](guarded-linking/android-build.log) and [check log](guarded-linking/check.log) record actual successful checks. The103-record composed replay took0.314 seconds with a declared Java `-Xmx256m` limit, excluding compilation; no new RSS/PSS or native memory measurement was taken. The historical classifier file remains568,032,787 bytes, classifier HWM1,030,778,880 bytes and generator HWM4,999,811,072 bytes, measured in separate serial stages. They must not be summed or presented as a measured co-resident Android budget.

Qwen3 4B SHA256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5` remains a host candidate; production0.5B, model.env, Android admission and native runtime are unchanged. No new assets or licensing terms were introduced. This controller compiles in Android source but is not wired into production, and the independent verifier has no qualified mobile runtime. No service, private context/holdout, orchestration state, main, publication or model preference changed.

## Remaining work

The existing [224 source-plan generation task](fact-frames/proposed-follow-up.json) remains the precise next independent product step: ground question obligations before prose to address avoidable W and correct paraphrases without adding a new hand-tuned grammar variant per failed question. No duplicate task or repeated inference was queued. The source-frame223 strategy is already measured and should be reused. Selected-model/verifier Android admission, load/cancel/reload and combined memory, integrated release identities, clean-machine reproduction, signing ownership, physical Android/GrapheneOS and human acceptance remain open. Independent source review of this bounded repair is pending.
