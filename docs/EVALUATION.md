# Frozen evaluation protocol

The initial suite separates public development prompts from a private holdout. Both are authored by an actual local model call before product tuning and frozen with SHA-256 manifests. They are unverified evaluation rubrics, not factual gold answers or measurements. A model judge can assist review but cannot establish human acceptance or competitive superiority.

The public manifest exposes holdout count and hash only. Holdout questions, raw generation response (which contains both splits), and private manifests must never be given to implementation workers. Implementers may inspect `evaluation/development.json`. The private custodian runs holdout only after a candidate commit, APK, knowledge packs and model assets are frozen and hashed. Holdout failures are reported in aggregate for release assessment, not used to tune the same holdout. A leaked or tuned holdout must be retired and independently replaced with its history preserved.

## Scoring

For every question retain exact input, app output, cited passage text and source metadata, abstention or limitation text, elapsed timing, model/runtime configuration, pack hashes and artifact hashes. Score each dimension separately from 0 to 2: correctness supported by cited sources; synthesis or reasoning usefulness; citation entailment and coverage; uncertainty and coverage awareness; and task fulfillment. Zero means absent or materially wrong, one means partial, two means adequate. Report unsupported claims and missing-source failures individually. No factual gold is supplied by the suite: a reviewer must verify the answer and rubric against authoritative frozen sources before assigning factual scores.

Questions that require current information must disclose the pack timestamp and inability to verify live conditions; fabricated freshness fails. Correct abstention is valuable when evidence is absent. Retrieving relevant text alone does not demonstrate useful explanations, comparisons or reasoning.

## Comparable measurements

Use the identical disclosed question set and scoring protocol for PocketLore, rivals and the frontier-plus-web reference, and disclose knowledge availability, versions, hardware and differing web access. Keep raw failures, not just averages. Report sample count, per-capability scores, abstention precision, crash rate, first useful output time and total answer latency with p50/p95 where meaningful. Small pilot results are not superiority evidence.

Measure cold and warm start separately. Define RAM as peak process resident memory plus other required runtime processes; record the measurement tool, GPU/accelerator memory separately where available, and total installed APK/model/knowledge/cache bytes. Device acceptance requires compatible physical Android/GrapheneOS hardware at no more than 12 GB RAM and 50 GB installed assets. Emulator and LLMRig desktop results are engineering checks only. Audit research-time network with airplane mode plus traffic capture or equivalent OS instrumentation; absence of Android INTERNET permission supports but does not replace the physical offline audit.

## Validation

Run `python tools/evaluation/validate_cases.py evaluation/development.json`. The structural validator checks fields, capability categories, uniqueness and an ASCII language guard; it does not prove semantic quality or English fluency. Private generation evidence records the actual returned model identity, raw response, request, duration and validation result. English-language case review and rubric adequacy remain reviewer judgments.

## Pilot rubric limitations

The generated rubrics can contain oversimplified premises. For example, the development civic comparison asks for current statistics even though an offline pack can only support dated statistics. The global freshness and uncertainty rule takes precedence: a clearly dated comparison plus an explicit inability to establish current values is acceptable; invented current values fail. Reviewers must not penalize a sourced correction to a question's premise, a justified request for missing location or material details, or a responsible abstention. Before using this pilot for competitive claims, independent reviewers must audit both the rubric and supporting sources without giving holdout content to implementers. Do not silently edit frozen case files; version any replacement and preserve prior hashes.
