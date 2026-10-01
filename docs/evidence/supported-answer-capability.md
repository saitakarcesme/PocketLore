# Supported-answer capability — task 190

Status: frozen public development comparison running; no model selection or acceptance yet.

The 24 new queries and verbatim evidence were committed before generation at `d1cc857`. They cover geology, genetics, geomagnetism, historical civics, outdoor preparation and travel. Cases include comparison, explanation, multi-source synthesis, qualifiers, five absent-evidence requests and four premises contradicted by the supplied sources. Contradiction cases test false user premises against real sources; they do not claim to test disagreements between independently conflicting source documents. No synthetic factual passages were added.

Sources are exact passages from the current English reference and science supplement editions, with stable IDs, URLs, dates and rights in [protocol.json](../../tools/evaluation/model-capability/protocol.json). This is an oracle-evidence capability test across those editions. The application currently loads one research pack at a time; this fixture does not demonstrate automatic retrieval or combined-pack support. Historical constitutional excerpts are source-reading tasks, not current legal advice.

## Models and execution

| Role | Immutable model revision | Quantization | File bytes | SHA-256 |
|---|---|---|---:|---|
| Current baseline: Qwen2.5 0.5B Instruct | `9217f5db79a29953eb74d5343926648285ec7e67` | Q4_K_M | 491400032 | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| Larger: Qwen2.5 1.5B Instruct | `91cad51170dc346986eccefdc2dd33a9da36ead9` | Q4_K_M | 1117320736 | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |
| Larger: Qwen3 1.7B | `90862c4b9d2787eaed51d12237eafdfe7c5f6077` | Q8_0 | 1834426016 | `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a` |

All three files are already available as ignored local assets, each below 4 GiB. Publisher repositories and Apache-2.0 declarations are pinned in the model JSON files, with exact local license hashes in run receipts. Existing third-party notices retain attribution. The larger candidates are different trained weights and architectures (`qwen2` versus `qwen3`), not two quantizations of one checkpoint. Both are Qwen-family models, so no cross-vendor generalization is justified. Model labels are nominal parameter classes; loader metadata is retained.

Only serial, two-thread CPU inference runs on LLMRig. No network inference, GPU inference, emulator service changes or global preference changes occur. The host library compiles the unmodified production JNI bridge against pinned llama.cpp `bb4caa7540188872173c44d161602d9271386413`; the Java harness calls the actual `AnswerEngine` and `EvidencePrompt`. No Android execution is claimed for this comparison. This isolates capability from emulator limits and leaves Android integration, memory/admission and physical-device validation separate.

Each model receives identical selected source text, system instruction and user prompt, with 2048 context tokens and at most 256 output tokens. Production Qwen2.5 uses greedy decoding; production Qwen3 uses its non-thinking template and temperature 0.7, top-k 20, top-p 0.8, presence penalty 1.5 over 256 tokens, fixed seed 42. Thus this is a production-policy comparison, not a sampling-matched architecture experiment. No seed search or prompt revisions are allowed. Each pair is generated once. Loading occurs once per model, with a fresh native context for each question.

Where the production controller abstains before calling JNI, a separately labeled diagnostic call uses the same production prompt and claim grammar to measure raw model capability. That diagnostic output is never counted as a published generated answer. Where the controller invokes JNI, its exact draft serves both analyses; there is no second sample. The grammar restricts answers to one or two bounded claim lines and can itself limit completeness. Raw drafts, fallback text, controller reasons, full prompts and source IDs remain inspectable.

Load time is native load call wall time. First token is time to the first unverified JNI callback, not time to useful evidence. Total generation includes prompt processing and decode (and controller preparation/validation when called through the controller); controller totals are also retained. Host memory snapshots are host observations, not phone measurements.

## Failures and reproduction

The first host build failed because `cmake` was not on PATH. Before any inference, commit `3121c2a` selected installed toolchain CMake and added the serial driver, without changing the frozen cases or runtime policy. The original freeze hash list and preflight amendment preserve that difference. No product source changed.

Reproduction uses existing ignored, hash-verified model and pack files:

```sh
bash tools/runtime/build-host.sh
python3 tools/evaluation/run_model_capability.py
# After reviewing and freezing the run evidence:
python3 tools/evaluation/verify_model_capability.py
```

The verifier checks actual load/generation results, prompt equality, pinned sources and models, budgets, routes and missing/changed artifact rejection. It does not equate lexical overlap, citations or builder ratings with factual entailment. Independent source review must use the blind packet without the identity key or builder ratings.

## Open gates

Results, source assessments and model/architecture selection will be recorded after the serial run. Existing twelve blocked supported development cases are not declared repaired by this new benchmark. Physical Android/GrapheneOS, research usefulness, independent source review and human acceptance remain open. No bounty submission or competitive superiority is claimed.

Observed during the unchanged run: the production comparison selector drops the reversal excerpt for case `cap-10` (magnetic storms versus reversals), retaining only the storm excerpt. Both oracle-offered and actually retained evidence are therefore distinguished in review inputs. The baseline then calls both phenomena rapid; the retained excerpt does not support that transfer. This is an architecture/evidence-selection failure as well as a raw unsupported draft. A model cannot recover missing evidence by guessing. No selector change or resampling is made in this experiment.

## Human correction and execution revision (supersedes initial matrix above)

The coordinator clarified that **Qwen3 1.7B Q8 is the current accepted-task baseline**, not Qwen2.5 0.5B. The historical 0.5B/1.5B observations above do not satisfy the requested alternative comparison. The original scalar CPU run was interrupted: 24 old 0.5B records and only one completed old 1.5B record are retained under `model-capability/historical-cpu-partial`. Its unfinished case has no completed output record; that harness did not persist partial tokens. No completion is inferred.

The human directed a faster, host-only execution revision. `execution-v2.json` retains the exact original fixture hash and scoring expectations, corrects the baseline, and adds two genuinely greater-capacity candidates: Qwen3 4B Q4_K_M and Phi-3.5 Mini 3.8B Q4_K_M. No questions, excerpts, production grammar or prompts are tuned. Existing historical pins are preserved. New immutable revisions, license files and expected download hashes are committed before generation.

The revised host screen uses six threads per process and native CPU ISA, with at most two processes if measured available host RAM is at least 12 GiB. The host-only file/model limit is 4 GiB; Android's two-thread, 2 GiB limit remains unchanged. KV and compute limits stay bounded. This explicitly does not establish Android admission for the new candidates. GPU management is unavailable inside this sandbox despite the coordinator's host report of idle GPUs; no service or global configuration changes are attempted. The CPU fallback avoids new GPU-stack setup. Timing receipts label host concurrency and must not be compared as mixed-backend speed claims.

New candidate weights are downloaded only to ignored paths. The separate source-acquisition worker's private corpus staging is outside this task; only its provided manifest may later be consumed. No staging, holdout or private conversation access is needed for this frozen experiment.
