# Answer integration evidence — task 020

Builder result on LLMRig, October 1, 2026: **both required acceptance commands
passed on the final APK**, using real local inference on the existing AOSP x86_64
emulator. Main-flow generation, citations, labeled fallback, unsupported abstention,
cancellation, source inspection, model import and lifecycle behavior are exercised.
This is integration evidence, not independent criticism, physical-device acceptance,
or useful-research acceptance. No private holdout was read or tuned on.

## What changed

**Answer offline** now retrieves evidence and routes through one answer controller.
If query terms are missing from the pack or the actual excerpts selected for the
prompt, it abstains without invoking generation. With evidence and a loaded model,
it applies the model's chat template with separate trusted system instructions
and user evidence/question content. Without a model, or after a generation/citation
failure, it shows **Extractive fallback — not a generated answer** and the retrieved
passages. Unverified streamed drafts are visibly distinct from completed answers.

The citation gate checks that the model supplied source IDs, every ID belongs to
the actual prompt, and each prose sentence/line has a citation. Empty, citation-only
and output-capped drafts are rejected. The app does not append invented citations
or relabel retrieved passages as generation. IDs can occur at the start or end of
a sentence. This checks citation integrity, **not factual entailment**.

Cancel discards partial output. It also discards a completed native result if a
cancel click arrives before the queued UI publication. A new question clears the
previous answer. Retrieval and import controls are serialized; activity recreation
cancels old work and reloads the saved model through the shared serial worker.
Source buttons retain the exact passage ID and open full text, provenance URL,
acquisition date and rights locally. No INTERNET permission or Play Services
requirement was added. Empty-output checks preserve the declared API-28 minimum;
only API-35 execution was measured.

## Frozen inputs and exact artifacts

The four public development cases were frozen before prompt changes in
`tools/answers/development-cases.json`, SHA-256
`1209c55fea82f39ebe2d22004b3b6cff259e55442d6f255a7dd9b884ee94ae75`.
Their questions and expectations were not changed after inspecting outputs. The
fixture's model hash records the original SmolLM2 baseline; the subsequent candidate
is separately pinned and identified in every candidate report. These are development
cases used during implementation, **not holdout or competitive evaluation**.

Candidate: official `Qwen/Qwen2.5-0.5B-Instruct-GGUF`, revision
`9217f5db79a29953eb74d5343926648285ec7e67`, file
`qwen2.5-0.5b-instruct-q4_k_m.gguf`, **491,400,032 bytes**, SHA-256
`74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`.
Host and app-private imported bytes matched that digest. The
[publisher metadata](answer-integration/qwen-metadata.json) and
[pinned model card](answer-integration/qwen-model-card.md) are preserved. Its
unmodified Apache-2.0 license and attribution are packaged in Android license
assets. Weights are ignored and unbundled. The GGUF is reproducibly fetched by pin;
its upstream conversion was not independently reproduced.

| Final artifact | SHA-256 |
| --- | --- |
| App APK, 17,785,580 bytes | `7776cc4be0d44f1368ca2bc592b6b30ffdb0824046b48a7aa2d99dd350e8e627` |
| Answer instrumentation APK, 76,598 bytes | `dfeea173cefbbbdbbfb152dc60a60a591ea59e76be4ea5118d0398acb6847f6a` |
| ARM64 JNI | `6ae28215cd5dd58e6b07c7c35a544122b6cc323625841f79d06cadf5d4122a8e` |
| x86_64 JNI | `ca2c6e60ed38d5c447cf53cd0efd6c424f18ce53c255202f7c5bac79d14d86ae` |

[Artifact sizes and hashes](answer-integration/reviewed-artifacts.json) include
all six exact inputs/outputs. Production code is captured by checkpoint `44876e9`;
the final evidence commit also includes the added empty-response host regression.
The latest full run is `downloads/answers/smoke-20260930T224530-2` on the rig.

## Checks and observed answers

- `bash tools/android-build.sh`: **PASS**, [raw build log](answer-integration/reviewed-acceptance-build.log).
- `bash tools/android-smoke.sh`: **PASS**, [raw run](answer-integration/reviewed-smoke.log),
  [Activity results](answer-integration/reviewed-result.json),
  [UI results](answer-integration/reviewed-ui-result.json).
- The smoke script also passes 14 synthetic-generator routing/citation/cancellation
  scenarios and eight existing retrieval contracts. Synthetic tests are not model
  quality evidence. They cover invalid/missing IDs, uncited sentences, empty and
  citation-only output, no-model fallback, runtime failure, clipped evidence,
  pre-cancellation, mid-generation cancellation and late-publication cancellation.
- Real UI checks use Android's file picker and confirmation dialog, verify the
  imported SHA-256, force-stop/relaunch and reload the saved model, and inspect the
  source provenance dialog. Real Activity checks invoke the normal answer button,
  compare rendered output with the controller result, click cancel after streaming
  starts, recreate during inference, reject stale results, and generate again.
- Native regression: **23 checks passed** using the same current JNI library hashes
  before the later Java-only cancellation/compatibility fixes. Its separate
  [raw result](answer-integration/native-regression-result.json) and
  [hashes](answer-integration/native-regression-hashes.txt) remain available.

The final generated answer to **Compare evaporation and condensation** was:

> [water-02] The opposite of evaporation is condensation, which occurs when saturated air is cooled, such as on the outside of a glass of ice water.

This was emitted by the model, not substituted by application code. The cited
passage contains those condensation facts. However, the answer omits a substantive
explanation of evaporation and is an **incomplete comparison**. Passing the citation
gate does not make it a high-quality research answer.

For **What is groundwater?**, the model emitted two sentences with a citation only
in the first. The app rejected that draft and displayed labeled retrieved passages.
The raw draft is preserved; it is not counted as generated-answer success.
**quasar supernova** and **Does evaporation cure diabetes?** both abstained with
zero generated tokens and `invoked_model=false`.

## Measurements — rig emulator only

Environment: existing coordinator-supervised `emulator-5560`, boot completed;
AOSP Android 15/API 35 x86_64. The task AVD's configured memory was 2,560 MiB with
two virtual CPUs, on the rig's Intel Core i5-14400F host. No GPU inference was used.
The builder did not launch another emulator, restart a service or weaken a sandbox.
Hidden `/dev/kvm` inside the builder sandbox is **not a current blocker** because
adb reaches the supervised emulator. Prior missing-KVM failures remain untouched.

Runtime identity: `llama.cpp bb4caa7540188872173c44d161602d9271386413; CPU; context=512; threads=2; greedy`.
The prompt has at most two 400-character source excerpts and a question of at most
350 characters. Output is capped at 128 tokens; context overflow falls back rather
than silently truncating the question. The model is already loaded for these
answer measurements. The raw runtime API retains its separate completion mode.

| Frozen case | Visible outcome | Model tokens | First token | Total controller time |
| --- | --- | ---: | ---: | ---: |
| Compare evaporation and condensation | Generated, `[water-02]` | 35 | 9,320.014 ms | 11,792.770 ms |
| What is groundwater? | Extractive fallback after citation rejection | 50 | 13,412.890 ms | 17,082.332 ms |
| quasar supernova | Abstained, no model invocation | 0 | Not applicable | 0.021 ms |
| Does evaporation cure diabetes? | Abstained, no model invocation | 0 | Not applicable | 0.031 ms |

First-token timing begins inside the answer controller and ends at the first Java
byte callback. It includes prompt formatting, fresh context allocation and prefill;
it excludes model load, retrieval and initial UI queueing. Total time includes
validation after generation but excludes final UI scheduling. Full-request throughput
is approximately 2.97 and 2.93 tokens/second respectively; it includes prefill, so
it is not decode-only throughput. Observed UI cancellation returned in **31.393 ms**
after the first streamed token, including the test's polling/UI scheduling. This
is not a worst-case prefill-cancellation bound.

An earlier Qwen run had a single `dumpsys meminfo` sample of **579,428 KiB PSS** and
**699,288 KiB RSS** ([raw sample](answer-integration/qwen-memory-point-sample.txt)).
It is a whole-process point observation during the earlier user-only-prompt run,
not a measured final-run peak or a device acceptance result. Model load latency,
true cold-cache latency, time to first *useful* content, p50/p95, energy, thermal
behavior and sustained memory stability were not established.

APK + one model totals **509,185,612 bytes** before ART/native installation overhead,
source originals, caches or import staging. The test app's files directory used
571,256 KiB, including both the native test's 93.5 MB SmolLM2 and the imported Qwen
model; the Qwen source copy in emulator Downloads adds another 491,400,032 bytes.
Model replacement can temporarily retain the old model, staging copy and source
original together. The [raw app-file listing](answer-integration/reviewed-app-files.txt)
is not a complete installed-footprint or simultaneous peak-storage measurement.
The 12 GB/50 GB physical resource gates remain open.

Wi-Fi and mobile data were disabled during research tests; their recorded settings
are [0](answer-integration/reviewed-wifi.txt) and
[0](answer-integration/reviewed-mobile-data.txt). The
[APK permission dump](answer-integration/reviewed-permissions.txt) has no INTERNET
permission. No packet-capture audit or physical GrapheneOS execution was performed.

## Preserved failures and review fixes

1. SmolLM2-135M with a chat-formatted user-only prompt generated confused/repetitive
   text and no acceptable cited answer: [raw failure](answer-integration/smollm-baseline-failure.json).
2. The first Qwen user-only prompt also omitted citations and misdescribed evaporation:
   [raw failure](answer-integration/qwen-user-prompt-failure.json). The approach changed
   to explicit trusted system instructions; citation criteria were not weakened.
3. Android did not register an additional instrumentation entry as intended:
   [runner failure](answer-integration/runner-registration-failure.log). The test
   build now explicitly selects its runner through a Gradle property.
4. A repeated picker run selected a background Downloads breadcrumb instead of the
   drawer entry: [picker failure](answer-integration/repeat-picker-failure.log).
   The script now selects the observed drawer entry. This was a harness error.
5. Review found a late-cancellation publication race and an API-33-only String call;
   both were fixed and the exact final APK reran both required commands successfully.

Earlier files named `final-*` in this evidence directory record the first full pass
before those review fixes; they are preserved unchanged. `reviewed-*` records the
final accepted-by-checks artifact. The [illustrative answer screenshot](answer-integration/generated-answer-layout-before-review.png)
was captured before those two non-layout fixes and visibly labels generation and
source inspection; its displayed timing is a separate observation.

## Reproduction and remaining gaps

Follow [RUNTIME.md](../RUNTIME.md): provision the immutable runtime/source pack and
`bash tools/answers/fetch-model.sh` outside research time, then run the two required
commands against the already supervised emulator. Neither acceptance script fetches
weights or starts another emulator. All substantive build/inference/data work took
place on LLMRig; weights, APKs and downloaded source remain ignored.

Coverage checks are lexical and conservative. They can reject synonyms and cannot
prove that a relation is supported just because its words occur in a source.
Citation checks are structural and cannot detect every false claim with a valid ID.
Excerpts may be truncated, the comparison is incomplete, and no broad factual
quality benchmark, adversarial-source evaluation or human acceptance was performed.
ARM64 compiled but was not executed. Physical Android/GrapheneOS, useful synthesis,
long-context coverage and whole-install resource acceptance remain open.

Evidence checksums are in [SHA256SUMS](answer-integration/SHA256SUMS). The builder
checkpoint does not advance main or substitute for independent criticism; no push,
branch switch, private-context access or orchestration change was performed.
