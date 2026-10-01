# Task 211: source-faithful broad edition

Task 210 repair already produced the required new disk-backed edition. This task reuses its sealed source bytes, exact compatible pack and actual Android evidence rather than downloading again or inventing another edition. Task 211 adds a reproducible per-document rights/extraction/topic disposition and behavioral regressions for all five named audit counterexamples. Builder completion is not independent acceptance or publication authorization.

## Source disposition and semantic evidence

[Dispositions](source-faithful-broad/dispositions.json) cover all **1,173** rendered revision candidates: **1,095 admitted**, **78 excluded** (67 unresolved additional terms, 11 without eligible prose). Every record binds a permanent revision URL, source timestamp, HTML SHA-256, extraction SHA-256, exact additional attribution notices and links, extraction disposition and math/quotation counts. The historical keyword area is explicitly separate from the semantic judgment. Four hundred records link the builder's actual source-body judgments to exact supporting-excerpt hashes; the [full reviewed excerpts](broad-reference/repair/semantic-review.json) remain preserved. Other sources receive no semantic quota credit.

The edition has **40,681 unique genuine passages**, with exactly **50 reviewed documents in each of eight areas**: science, history, geography, mathematics, computing, civics, practical reference and travel. Targets are unchanged. No biography or transport-company title is treated as practical guidance. These are builder topical judgments, not independent source evaluation or comprehensive coverage. The corpus retains alphabetic, geographic and historical biases.

The [frozen counterexamples](source-faithful-broad/counterexamples.json) explicitly require:

| Source | Disposition and discriminating check |
|---|---|
| Absolute value | Admitted, mathematics quota; actual TeX zero identity and the source's numerical example survive. |
| Algae | Admitted, science quota; `50 metres (160 ft)` survives verbatim. |
| Transport in Belgium | Admitted as uncounted background; three infrastructure quantities retain km/mile units, and incorporated CIA source attribution remains inspectable. Historical network quantities are not current operating availability. |
| Futurist cooking | Admitted as uncounted cultural background; cannot count as practical guidance. |
| Louisville Museum Plaza | Admitted as uncounted historical background; abandonment text survives, and it cannot count as a travel attraction or practical guidance. |

The checker actively mutates these assumptions: practical credit for Futurist cooking, travel credit for Museum Plaza, loss of transport units and removal of incorporated-source attribution must each fail. The underlying full gate also reparses every admitted HTML snapshot, checks every source/passage hash and UTF-16 substring, distinct counts, exact notices/references, all area quotas, missing license/legal text, missing/changed artifacts, missing math and unresolved additional terms. This is not a producer-success or file-presence check.

## Rights and extraction limits

Wikipedia editorial text retains CC BY-SA 4.0, title, Wikipedia contributors, permanent article revision, contributor-history link, dates, license and modification statement. Additional source-specific notices and links are preserved; unresolved extra terms are excluded. Attribution via article/history links does not claim an independently frozen author roster. The 36 admitted notices include explicit public-domain incorporation and CC BY 4.0 sources. No generic public-domain label is applied to Wikipedia. The exact rights policy, exclusions and licensing references are in [task 210 repair evidence](broad-reference.md) and THIRD_PARTY_NOTICES.

Math is copied from source TeX, not reconstructed; numeric units come from rendered prose. There are 8,179 retained mathematical representations. Media, tables, quoted paragraphs and navigation are excluded. TeX remains plain text and some paragraphs require surrounding context. Source notices can retain citation-template CSS text alongside attribution; this formatting noise is not stripped by this task because changing sealed bytes would require a new edition and validation. Unknown attribution exceptions cannot be guaranteed absent merely by automated parsing; independent rights/source review remains required. `distribution_ready` remains false pending that review, and nothing is published.

The new sources are rendered revision snapshots acquired on 2026-10-01, not silently repaired versions of the historical 2023 extract. Cached HTML and receipts bind reconstruction; later oldid rendering may change template output. All old acquisition/extraction failures and the original checkpoint remain preserved.

## Exact candidate and Android evidence reuse

The new edition is `broad-reference-rendered-20261001-v2`:

- Pack: 46,339,444 bytes, SHA-256 `b8d18801b099402205938979ab2bb44ee9a316f06f030aab789cf93ba3605012`.
- SQLite index: 121,401,344 bytes, SHA-256 `9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386`.
- APK: 11,921,193 bytes, SHA-256 `d3f32566fbff579a0175e65662ea212ef18a1346e20f390d10127b6d52f7523f`.
- Saved production model: Qwen2.5 0.5B, SHA-256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`.

The behavioral gate verifies these identities against the actual [fresh import](broad-reference/repair/run/import.json), [new-process restart](broad-reference/repair/run/restart.json), [source dialog](broad-reference/repair/run/restart-source.png), [offline license](broad-reference/repair/run/restart-license.png) and [hashed receipt](broad-reference/repair/run/receipt.json). These are existing emulator-5560 measurements, not a newly executed UI run. Since no production source, pack or APK changed in task 211, their measured evidence remains applicable; drift fails the check.

Fresh import took 31,501.659 ms, restart opening 384.508 ms. The two small packs and model remained intact; combined catalog counts are 1,113 documents/40,891 passages. Eight real source dialogs per run, offline legal text, corruption rejection, cancellation and stage cleanup were exercised. Cancellation operation time was 131.554 ms including test overhead. Restart opening added 856,064 Java-heap bytes; emulator PSS was 94,096 KiB after opening, not a phone peak-memory claim. Instrumentation supplies a fixture URI to the real import worker; external SAF browsing is not newly tested. No service restart, unrelated deletion, network research or physical-device result is implied.

## Reproduction and remaining gates

```sh
python3 tools/packs/broad/repair/dispositions.py > /tmp/pocketlore-source-dispositions.json
cmp /tmp/pocketlore-source-dispositions.json docs/evidence/source-faithful-broad/dispositions.json
bash tools/android-build.sh
python3 tools/evaluation/verify_source_faithful_broad.py
```

Both required checks passed. Required logs are [build](source-faithful-broad/build.log) and [verification](source-faithful-broad/verification.log). Full edition acquisition/build reproduction is documented in task 210 repair; no unchanged shards were fetched here. The checker requires the preserved local sealed artifacts and rejects identity drift.

This task does not tune retrieval or claim generated support. Expected-article recall remains 24/32 on the unchanged public development set, with eight absent controls withheld. The separate exact-formula paragraph query still fails top-four retrieval; its raw failure is preserved. Broad generated answers remain disabled. Concrete next work remains task 212's passage relevance/diversity and supported JNI integration, then task 213's exact candidate release validation. Independent source/rights review, clean-machine reproduction, signing ownership, physical Android/GrapheneOS and human acceptance remain open; no private runner or queue state was changed.
