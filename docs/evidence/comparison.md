# Comparable development evaluation v1

Task 090 implements a versioned same-emulator comparison harness, with real production JNI answers and a deterministic production retrieval baseline. This is development evidence, not competitive acceptance. External frontier/web rivals and independent blind ratings remain unrun; no credentials or external answers were fabricated. Private holdout was not read.

## Protocol and reproduction

See [frozen protocol](../../evaluation/comparison-v1/protocol.json) and [reproduction and review instructions](../../evaluation/comparison-v1/README.md). Run `python3 tools/evaluation/run_comparison.py`, then `python3 tools/evaluation/verify_comparison.py RUN_DIRECTORY`. The default verification command checks the archived `comparison/run-v1` evidence. Run `bash tools/android-build.sh` separately for the application build gate.

Five exact questions were inherited from the existing frozen public synthesis development fixture. This set has already informed development and is not a statistically representative or unseen test. The comparator is PocketLore's deterministic extractive retrieval response, not an independent commercial rival. Both systems receive the identical licensed 186-passage corpus and exact question on the same AOSP API35 x86_64 emulator, airplane mode enabled. System order alternates by question. One sequential pass, no warmup, no concurrent inference jobs, no confidence intervals.

Pack/index and model loading are excluded from request latency and recorded separately. End-to-end milliseconds use `System.nanoTime`, starting before retrieval and ending when the final response is available, excluding UI rendering and JSON recording. The model is resident; request contexts are recreated. Token-first timing is the production AnswerEngine stage measurement, not whole-request time to first content. Extractive zero tokens/first-token time means not applicable. Shared OS caches and emulator scheduling are uncontrolled; these numbers are not phone or cold-start performance.

## Preserved artifacts

The archive contains exact raw drafts, final responses (including fallback/abstention), prompts, source IDs/text/provenance, per-stage timings, runtime identity and model/pack/app/test-APK hashes. APK copies remain ignored under `downloads/comparison/apks`. The full native model is not in Git. The run manifest hashes source files; the initial run began with uncommitted harness changes, so source hashes supplement its recorded checkout commit.

The verifier checks protocol hashes, exact pairs/questions and order, shared retrieved evidence, source metadata, real generated-token records, timing validity, citation membership, and deterministic blind packet reconstruction. Five deliberate corruptions must fail: changed question, unmatched sources, negative time, no generation and invented citation. These checks establish structural measurement integrity, not semantic correctness or proof against fabricated device logs.

Give independent reviewers only `blind.json`. Keep `identity-key.json`, raw results and timing out of the review packet. Ratings remain null. Text is unchanged, so wording can reveal extractive style; blinding is imperfect. Raw model drafts withheld by the application are for diagnostic review, not presented as published answers.

## Failures and limitations

Both initial harness build failures are preserved in [failures](comparison/failures): Gradle init-script project lookup, then unsupported Android Java file convenience APIs. The hook and API calls were corrected without application changes. The Android analytics settings warning is caused by a read-only home directory and does not require global configuration changes.

A frontier/web comparison needs a named authorized endpoint and reproducible model, search/source, timing and cost conditions. No such endpoint was supplied for this task. Independent scoring, broader questions, unseen release evaluation, actual rivals, physical Android/GrapheneOS performance and useful supported synthesis remain open. Citation syntax is not entailment. No winner or superiority claim follows from this run.

## Measured results and checks

Run `20261001T020919Z` on LLMRig, emulator-5560. Both named acceptance commands passed. The verifier also rejected all five deliberate corruptions. App code and app APK are unchanged from task 080. Loading the pack/index took 198.942 ms and the resident model 169.755 ms (warm filesystem conditions, not cold storage).

| Question ID | PocketLore route | Generated tokens | PocketLore end-to-end ms | Extractive end-to-end ms |
| --- | --- | ---: | ---: | ---: |
| comparison | GENERATED | 44 | 27722.342 | 0.145 |
| explanation | ABSTAINED | 5 | 23003.093 | 0.135 |
| synthesis | FALLBACK | 68 | 35878.021 | 0.275 |
| conditions | GENERATED | 57 | 25077.029 | 0.205 |
| absent | ABSTAINED | 0 | 1.811 | 0.177 |

The generated comparison states opposite processes and gives evaporation’s direction, but does not explicitly explain condensation’s direction. The explanation declines despite retrieved heat-removal evidence. Groundwater/runoff generation is withheld for weak lexical support and exposed only as an extractive fallback. The generated recharge comparison retains the substantial-precipitation qualifier. The diabetes question abstains before inference. These observations are builder inspection, not independent quality ratings or comprehensive entailment verification. The baseline supplies passages even for partial evidence, which is not a supported answer to the absent-evidence question.

Exact SHA-256 identities:

- `model_sha256`: `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`
- `pack_sha256`: `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`
- `protocol_sha256`: `1c8b1439e40457bf9c141653d7f72fcbb552805a8269e4f64ff8e95861694510`
- `results_sha256`: `244a7de58ec4eba43d56c05dc4061fab6895154c151eb6c69a6c1bc821036425`
- `apk_sha256`: `27f9d7824be8b843db7b7238c39c56893005c09f808267cf72e765c87fe0789b`
- `test_apk_sha256`: `38ba1528e5fbfa68767ba70b8511c11334ca8dfcf8bff9cbd4b9ed270df88c3d`

Runtime: `llama.cpp bb4caa7540188872173c44d161602d9271386413; CPU; context=2048; sequences=1; KV=f16; sessions=1; threads=2; greedy default; Qwen3 claims: non-thinking, t=0.7, k=20, p=0.8, presence=1.5/256, seed=42`. The Qwen2.5-0.5B model and USGS-containing reference pack retain the existing model/data notices. See [raw results](comparison/run-v1/results.json), [manifest](comparison/run-v1/manifest.json), [blind review inputs](comparison/run-v1/blind.json) and the separately held [identity key](comparison/run-v1/identity-key.json). No blind ratings have been obtained.
