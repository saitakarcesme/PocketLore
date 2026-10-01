# Task 224 repair 2: compositional formula proof, usefulness still fails

Recovered failed checkpoint `6a7ddf6c5b81f690ded91e5b21717ad8a9a78c37` on the existing checkpoint branch. The previous complete-sentence adapter and whole-dependency experiment remain intact. This repair replaces neither historical evidence nor the deployed controller. It adds a separate Java proof compiler for a bounded mathematical relation family, replaying the existing 24 source-plan records without new model or classifier calls.

## Declaration and implementation

Commit `0e22c95` froze the execution-only protocol and 12 constructed mathematical operator controls before implementation. Commit `60b0370` records the initial unvalidated compiler. The controls use a cube root of eight and level/intensity dimensions, not the original astronomy answer. They are synthetic regression tests, not corpus content or generated successes. There are no question IDs, entity lists, expected-label lookups or source-specific answer templates in the compiler. Its finite mathematical vocabulary and supported productions are explicit in `EquationProof.java`; this is a narrow formal language, not general natural-language entailment.

The compiler consumes every token of every sentence, derives dimensions and ratio constraints from selected source grounds, parses root degree and radicand, and checks their identity against actual source TeX. Decimal approximations use the existing half-last-displayed-digit tolerance; exact numeric equality uses absolute tolerance 1e-12. Correspondence, representation and calculation compose with the same source quantity. Unknown operators, negation, foreign dimensions, changed root structure and factual tails reject the whole claim. Cancellation is checked throughout. The original FactFrames proof remains unchanged for other relations.

The binder preserves generated text, obligation identity, full source spans and typed renderer links. After reviewing the initial replay, a metadata guard was added requiring visible subject context to agree with the cited mathematical source title. This is a generic subject guard, not an inference rerun or label change. Both earlier deterministic replay outputs/receipts are preserved separately. The final 16 behavioral checks include the frozen controls, cancellation, text preservation, wrong visible subject rejection and typed citation navigation. Historical chain checks still exercise missing/changed model artifacts and namespace/corruption controls; the new verifier also rejects changed or missing replay results and regenerates identical results from the sealed original stages.

## Actual result and source assessment

| Measure | Original plan experiment | This deterministic repair replay |
| --- | ---: | ---: |
| New questions | 24 | 24, unchanged |
| Source-supported candidate answers | 0 eligible | 1 |
| Unsupported candidates under builder source review | 0 | 0 |
| Complete useful answers | 0 | 0 |
| Absent controls withheld | 4/4 | 4/4 |

The only candidate is q21. All three unchanged generated claims cite the exact sentence defining a one-magnitude brightness ratio as the fifth root of 100, about 2.512. Complete raw prose, edition/document/passage hashes and UTF-16 offsets are in `run/results.json`. The three claims express the equation, its calculation and its approximate value. They **do not explain why a fifth root is used**, which the frozen question explicitly asks. The answer is repetitive and incomplete. `builder-review.json` therefore grades support true but completeness and usefulness false. No quotation, deterministic explanation or fallback replaces the model prose. This manual source review is builder assessment, not independent criticism or held-out evaluation.

The other 23 records retain their failures; no unsupported clause is silently deleted. Old143 fact-frame and127 parser records, including unsafe historical outputs and 994 classifier pairs, remain preserved and validated by the prior check chain. The mathematical extension is exercised on the 24 source-plan records and constructed controls, not claimed as a new scoring run over every prior population.

## Checks and identities

- `bash tools/android-build.sh`: exit 0; raw `android-build.log`, exact APK receipt `build.json`. APK SHA-256 `98c094cf67b56d978947e5d25927d59f32e21b83314baeee06ce9375c1c902b0`.
- `bash tools/evaluation/check_source_plan_generation.sh`: exit 1, after successful historical checks, 16 new behavioral checks, exact replay and artifact mutations. The final failure is **zero complete useful answers**, not an artifact or build failure. Raw `check.log`.
- Java host deterministic replay took 0.175811 seconds, excluding compilation and behavioral controls. This is not model latency, Android JNI execution or a speed comparison. No new native-memory measurement is claimed.
- Original selected Qwen3 4B host artifact remains SHA-256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`; production model.env remains unchanged. No additional model/parser download or inference job occurred.
- `SHA256SUMS` seals run, build, assessment, protocol/source receipt and check artifacts. Replay recompiles the exact Java sources and consumes unchanged original plan/prose stages.

## Remaining concrete boundary

This repair removes one syntax rejection but does not meet the objective of useful generated explanations. The next independent architecture work is obligation completeness: represent which source relations jointly answer a requested “why,” distinction or comparison before prose, and withhold if the plan contains only a restatement. Missing source relations still require a broadly applicable semantic extraction design; more finite answer-wording rules or repeated generation of this matrix are not justified. No external hardware dependency explains this quality failure.

Production integration, selected 4B mobile admission/load/cancel/reload, combined memory qualification, integrated release identity, physical Android/GrapheneOS, clean-machine reproduction and human acceptance remain open. No model role was changed, no service restarted, and no task queue, runner state, branch or main was modified. This is a negative development checkpoint, not completion or acceptance.
