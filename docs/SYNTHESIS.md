# Supported synthesis development slice

The Android answer controller selects retrieved excerpts, includes source dates and URLs, and asks the loaded local model for one or two concise linked claims. Comparison queries select a passage for each named aspect; other queries retain the first two hits and additional hits that add question-term coverage. This is a small lexical selector over the existing top four results, not a new semantic retrieval system.

The production JNI tokenizer counts the complete model chat template and reserves 256 output tokens in a 2,048-token context. Excerpts shrink from 900 to 200 characters if needed; losing question coverage or still exceeding the budget withholds generation. Native code independently rejects overflow. Cancellation discards partial drafts. Token callbacks remain explicitly unverified until final validation.

A llama.cpp grammar constrains output to one or two citation-prefixed sentences or an abstention. It contains no factual answer. Short source labels map to immutable passage IDs after generation, preserving the raw draft. For comparisons using multiple excerpts, each claim must emit all selected labels: this is joint context attribution and can overcite. It does not identify which individual source supports each clause. Each sentence is limited to 220 characters and cannot contain internal periods, so decimals and abbreviations are currently restricted.

The answer controller checks citation membership, sentence coverage, token completion, numeric presence and lexical overlap with cited excerpts. For explicit two-source comparisons, a further conservative check rejects clause terms found only in the other subject's excerpt; ambiguous clauses are not resolved. Comparison prompts request one subject per line, addressing the same requested property. These checks are not semantic entailment: earlier drafts passed despite reversing or transferring source facts. The final answer's citation spans call the existing source inspector. Missing evidence abstains; rejected drafts become explicitly labeled extractive fallback.

A narrow conflict detector recognizes otherwise identical statements with opposite explicit negation. It requests disclosure and withholds drafts that do not cite both sides and identify uncertainty. The fallback names the potential disagreement. Different dates, numerical differences, implicit contradictions and real-world reconciliation remain outside this heuristic. Dates are included in the prompt; the application cannot automatically establish whether old information is current.

## Reproduce on LLMRig

Provision the existing pinned runtime and English pack using their documented fetch/build steps. The optional synthesis model is separately pinned in `tools/evaluation/synthesis-model.json`; its upstream Apache-2.0 license and attribution are bundled in Android assets. No weights enter Git.

```sh
python3 tools/evaluation/fetch-synthesis-model.py
bash tools/android-build.sh
bash tools/evaluation/check_synthesis.sh
```

The first command performs online provisioning into ignored downloads. The checks require the existing booted `emulator-5560`; they do not launch an emulator or restart services. The evaluator installs the app/test APKs and uses an isolated test model and pack, preserving the app's saved model. It executes real production JNI generation, token-overflow/cancellation checks, and citation-span callbacks, with raw prompts, source excerpts and outputs saved under unique ignored `downloads/synthesis/run-*` directories. It fails when a required generation or bounded development meaning check fails. Host fictional control tests are separate from the real-source quality cases.

The five development questions were frozen before tuning; four require generated answers and one requires absent-evidence abstention. An additional fictional sensor conflict tests control behavior only. No private holdout is used. See [measured evidence](evidence/synthesis.md) for actual results, failures and claim review. Physical hardware, independent source-support review, broad reasoning quality, sustained performance and resource acceptance remain open.
