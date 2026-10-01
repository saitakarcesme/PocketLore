# Licensed science supplement: task 150

Measured on LLMRig and the existing API 35 x86_64 emulator-5560 on 2026-10-01. Both named checks pass; this is builder evidence, not independent or product acceptance. No physical device was used.

## Edition and provenance

The separately versioned `science-supplement-2026-10-01-v1` contains 24 selected factual paragraphs from eight real English agency documents across geology, genetics and geomagnetism. No factual text was generated. No images, captions or third-party media are included. HTML removal and whitespace normalization are the only text transformations. Each citation is a document prefix plus the first 16 hexadecimal characters of its full paragraph SHA-256; the full digest, raw-page digest, source URL, rights URL, attribution and dates are pinned in the [source lock](../../tools/packs/science-sources.lock.json) and [manifest](science-supplement/final/manifest.json).

| Topic | Source | Selected blocks | Source update date |
| --- | --- | ---: | --- |
| Geology | [Earthquakes, USGS](https://www.usgs.gov/faqs/what-earthquake-and-what-causes-them-happen) | 3 | Not stated |
| Geology | [Volcanoes, USGS](https://www.usgs.gov/programs/VHP/about-volcanoes) | 5 | Not stated |
| Geology | [Magma and lava, USGS](https://www.usgs.gov/faqs/what-difference-between-magma-and-lava) | 1 | Not stated |
| Genetics | [DNA, NHGRI](https://www.genome.gov/about-genomics/fact-sheets/Deoxyribonucleic-Acid-Fact-Sheet) | 4 | 2020-08-24 |
| Genetics | [Chromosomes, NHGRI](https://www.genome.gov/about-genomics/fact-sheets/Chromosomes-Fact-Sheet) | 4 | 2020-08-15 |
| Geomagnetism | [Earth's core, USGS](https://www.usgs.gov/faqs/how-does-earths-core-generate-a-magnetic-field) | 1 | Not stated |
| Geomagnetism | [Polarity reversals, USGS](https://www.usgs.gov/faqs/it-true-earths-magnetic-field-occasionally-reverses-its-polarity) | 4 | Not stated |
| Geomagnetism | [Magnetic storms, USGS](https://www.usgs.gov/faqs/what-a-magnetic-storm) | 2 | Not stated |

All retrieval/snapshot dates are 2026-10-01; an unknown publication date is explicitly unknown, not replaced with a related-item date. Selected agency text is public domain under the [USGS policy](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits) and [NHGRI policy](https://www.genome.gov/about-nhgri/Policies-Guidance/Copyright), subject to their third-party exceptions. Selection excludes third-party credits and media. Attribution is retained per passage; no endorsement is claimed. See THIRD_PARTY_NOTICES. Responsive duplicate paragraphs were selected once. The DNA eye-color simplification was excluded during source review.

Acquisition failures and excluded candidate sources are preserved in [acquisition findings](science-supplement/acquisition-findings.md): USGS 404s, NOAA 403s and the NASA attribution-policy decision. Those are observed acquisition outcomes, not fabricated raw HTTP captures.

## Freeze and behavioral results

Commit `cf1d5c0` froze the source selection and [12 public queries](../../tools/evaluation/science-supplement/cases.json) before retrieval evaluation: four literal, four paraphrase and four absent. Query-file SHA-256 is `d775afe09a6e64e565872894d4510e264ebd49de5c156629aeae71693f595198`; source-lock SHA-256 is `96268ab080a3bbf05502d467c0e076b5a499e87908160b8dd9e747e4b8e80501`. No retrieval tuning or private holdout access occurred.

The [final raw results](science-supplement/final/results.json) record every exact question, returned passage text/ID/score, route, reason and retrieval time. All eight supported queries retrieve their required pinned source within the production top four; all four absent queries abstain. This is a small public development set, not broad recall or answer accuracy. The null-generator AnswerEngine still blocks five supported cases (volcanoes, magma, DNA, chromosomes and polarity reversal); the other three are FALLBACK. **No generated answer quality is established**. The Activity loads the existing real model, but these query evaluations deliberately supply no generator.

Production KnowledgePack import took 81.424704 ms (monotonic elapsed time around isolated install, including read/validation/index creation; single emulator sample). Retrieval alone took 0.075795–0.978510 ms per query; these exclude import, model load, UI and inference and are not warm/cold distributions or phone latency.

Three new-edition corruptions are rejected while preserving the installed pack and removing stages:

- Payload mutation with unchanged manifest hash: Passage payload hash mismatch.
- Empty rights/license field: Invalid metadata: license.
- Changed source-block digest: Invalid stable citation ID.

The production Activity imports the edition, opens its actual citation dialog, and rejects the corrupted payload while retaining the science edition. [Visible inspection](science-supplement/final/source-dialog.png) shows `science-magma-b214c1cb4647b3fc`, the complete original magma/lava sentence, URL, source/retrieval dates and rights. Instrumentation checks the actual accessibility tree. The picker result uses an injected app-owned file URI and inspection invokes the real Activity method; this does not claim a new manual SAF-picker or external-provider test. Original saved model/library hashes are identical [before](science-supplement/final/saved-before.txt) and [after](science-supplement/final/saved-after.txt).

The [initial run](science-supplement/initial/results.json) passed retrieval/import checks but its [screenshot](science-supplement/initial/source-dialog.png) exposed the old library's stale 186-passage status. MainActivity now refreshes this counter after import; the final regression requires the actual status to say 24 passages. Initial evidence remains unchanged.

## Exact artifacts and checks

- Pack: 31,183 bytes, SHA-256 `c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274`.
- Final app APK: 11,773,557 bytes, SHA-256 `234f418b10257a61ad25941a82d83c1ff036a90889437d4a007dba59334bc738`.
- Final test APK: 240,794 bytes, SHA-256 `8e39c66551ebce443723629ed4f79b002bfec396f00d85bdd463cb36492eccdb`.
- Final raw results SHA-256: `244a5f9c26456cdc04995bf4c94efcbc06a6a9f452d6ccdd7fcf6feb44f11d9d`.
- `bash tools/android-build.sh`: exit 0, [standalone build log](science-supplement/android-build.log); APK digest still matches the tested candidate.
- `bash tools/evaluation/check_science_supplement.sh`: exit 0, [summary](science-supplement/final/summary.json), [instrumentation](science-supplement/final/instrumentation.txt), [fixture build](science-supplement/final/build.log), [emulator fingerprint](science-supplement/final/fingerprint.txt).

The check rebuilds the edition twice and requires byte identity, verifies frozen fixture hashes, runs production Android retrieval/import/inspection, asserts absent abstention and corruption rollback, and verifies saved assets after restoration. It does not accept a self-reported PASS alone. Raw HTML, packs and APKs remain under ignored `downloads/science/`; only bounded results and screenshots are committed.

## Reproduction and limits

From the project root on the provisioned rig:

```sh
python3 tools/packs/build_science.py --download
bash tools/android-build.sh
bash tools/evaluation/check_science_supplement.sh
```

The fetch step requires network only for missing source caches. It writes ignored raw HTML, enforces exact page and paragraph hashes, and never silently updates pins. Dynamic page changes, even unrelated HTML changes, will fail reproduction without the matching snapshot; independent future clean acquisition is not proven. With the pinned caches present, building is offline and deterministic. The default output is `downloads/science/science-supplement-2026-10-01-v1.plpack`. Transfer that file to the device and select it with Import knowledge pack; the edition **replaces** the active library, not merges it. Keep an original pack file to restore it. The automated check assumes emulator-5560 is booted with the existing saved model/library and restores that library afterward; it does not start an emulator or service.

This is dated introductory reference, not medical guidance, current forecasts, or a comprehensive science corpus. Multi-pack search/merging, broader supported answer coverage, unseen evaluation, useful generated synthesis, physical ARM64/GrapheneOS and human acceptance remain open. Product APK identity changed for the count fix; historical release freezes are not current validation. Tasks 160–180 remain independent rig work. No orchestration/state, services, branches or main were changed, and nothing was pushed.
