# Task 030: English knowledge pack and verified import

Builder evidence, measured on LLMRig and the existing AOSP API 35 x86_64
`emulator-5560`; **not physical Android or GrapheneOS acceptance**. No private
holdout, runner state, orchestration, branch changes, pushes or services were
used or changed. No GPU job was needed. This report does not establish research
answer quality, factual entailment or competitive performance.

## Result and exact artifacts

Both required checks passed on the final implementation:

- `bash tools/android-build.sh`: PASS, 7 seconds reported by Gradle, offline toolchain.
- `python3 tools/packs/verify_pack.py`: PASS, 47.713 seconds wall time including
  repeated build, test installation, instrumentation and real document-picker UI.
- Existing `bash tools/android-check.sh`: PASS, eight starter retrieval,
  abstention, corruption and citation contract checks (host regression).

Final run: `downloads/packs/verify-20261001T010843` (rig local time, UTC+02:00;
2026-09-30 23:08:43 UTC). The final pack is also available at the ignored local
path `downloads/packs/english-reference.plpack`. Raw acquisition files and all
candidate archives remain under ignored `downloads/packs`; no bulk corpus or
build binary is committed. The complete final manifest, logs and a source-dialog
capture are frozen in [knowledge-pack/](knowledge-pack/).

| Artifact | SHA-256 |
| --- | --- |
| Pack, 159,327 bytes | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |
| Debug APK | `13b1e144e5c3e669f8ed4850091d0f383cf9027efc37144d8cc0ae1a8242994c` |
| Pack instrumentation APK | `a6e620bce9c89190f28eed2b519e4000242003ac083b8abb2b1f43f08932014a` |

Two independently written pack archives were byte-identical. All ten cached raw
HTML hashes matched the original acquisition pins; individual selected block
hashes were revalidated on both builds. Stable citation IDs derive from document
ID and text hash, so adding the verified page dates did not change citation IDs.
The final pack's payload hash and all per-document/passage hashes are recorded
in [pack-manifest.json](knowledge-pack/pack-manifest.json).

## Corpus and provenance

| Coverage | Documents | Passages | Source dates |
| --- | --- | --- | --- |
| Science: evaporation, infiltration, groundwater, surface runoff | 4 USGS pages | 38 | Byline dates: 2019-06-08 evaporation; 2026-09-17 for the other three |
| History: original Declaration, Constitution and Bill of Rights | 3 National Archives transcriptions | 126 | 1776-07-04; 1787-09-17; 1791-12-15 |
| Practical reference: NPS Ten Essentials explanations | 1 NPS page | 10 | Page updated 2026-05-28 |
| Travel: Yosemite trail regions and Yellowstone hiking | 2 NPS pages | 12 | Pages updated 2025-07-17 and 2025-04-18 |

Total: 10 documents, 186 passages, versus eight passages in the existing starter.
All acquisition dates are 2026-09-30 UTC. Historical document dates, modern byline
and page-update dates are explicitly distinguished. The corpus consists of
selected real source text with HTML removed and whitespace normalized; it is not
model-generated or synthetic factual data. Rights and attribution travel in the
manifest and every passage row and are visible in the app's source dialog.

Sources are USGS-authored and NPS-authored federal text plus original founding
documents, public domain in the United States. Excluded: images/media, logos,
third-party book text and the NPS geology page crediting external contributions.
The NPS Ten Essentials system's Mountaineers credit is preserved; the referenced
book is not copied. See [pack documentation](../KNOWLEDGE_PACKS.md), the source
lock and `THIRD_PARTY_NOTICES` for exact URLs, licenses and reproduction steps.

## Measured behavior

Production `KnowledgePack.install` validated the archive, created the real
`ResearchEngine` index and atomically saved it in **174.904 ms** in this single
emulator instrumentation run. This is elapsed import/index/save time, not cold
storage, p50/p95, download, model inference or phone latency. The archive is
159,327 bytes; temporary plus old/new archives and in-memory representations
add overhead. Peak RAM and whole-install storage were not measured here.

The instrumentation retrieved evidence for evaporation, Declaration, NAVIGATION
and Yosemite; verified persisted reload; rejected **18** corruption cases; checked
that every rejection left the prior saved hash and retrievable pack unchanged;
and checked temporary-file cleanup. Cases cover changed payload, truncated ZIP,
invalid directory offset, missing manifest, traversal, oversized expansion,
malformed UTF-8, unknown and fractional schema, wrong language/count, duplicate
documents/citations/entries, empty license, mismatched provenance and changed
passage text even after recomputing the payload hash. Full actual exceptions are
in [instrumentation.txt](knowledge-pack/instrumentation.txt).

The separate real UI flow selected the pack through Android's document picker,
compared the installed SHA-256, force-stopped/restarted the app, confirmed the
same pack reloaded, attempted a corrupt import, and verified the saved hash stayed
unchanged. A normal Yosemite question exposed imported source buttons; the
opened source showed its stable citation, NPS URL, 2025 page date, retrieval date
and public-domain attribution. See [UI results](knowledge-pack/ui-result.json)
and [source screenshot](knowledge-pack/source-dialog.png). This checks retrieval
and inspectability, not whether the optional model's answer is useful or correct.
The verifier leaves this pack installed on the isolated emulator.

## Preserved failures and limitations

The first verifier failed when an adb shell redirection was not quoted for the
remote shell. No success was recorded; [raw failure](knowledge-pack/initial-verifier-failure.txt)
is retained. The first UI attempt failed because the test searched for a mixed-case
button string while Android rendered uppercase; [raw failure](knowledge-pack/ui-label-failure.txt)
is retained. Case-insensitive control matching fixed that test issue. Later runs
passed; production failures were not suppressed. The duplicate ZIP name warning
in passing verifier logs is intentional construction of the rejection fixture.

During source discovery these NPS URLs returned HTTP 404 and were not included:
`/subjects/fossils/fossilization.htm`, `/articles/000/hiking-safety.htm`,
`/inde/learn/historyculture/stories-declaration.htm`,
`/inde/learn/historyculture/stories-constitution.htm`, and
`/articles/000/10essentials.htm`. Real accessible sources replaced those candidates;
no synthetic replacement passages were produced. Initial metadata marked USGS
dates unknown; page inspection established explicit byline dates before freezing
this final manifest and its evidence.

Coverage remains narrow and history-heavy, with no world-history, multilingual,
broad travel or live conditions claim. Original constitutional provisions can be
superseded; the document title labels this historical text, not current law.
The current answer prompt does not yet carry all document-date metadata into
generation, so source inspection and warnings do not establish stale-answer safety.
Travel warnings do not replace checking current conditions before departure.

Hash consistency is not publisher authentication or factual verification. The
importer trusts a manifest's attribution and English-language declaration once
internally consistent; hostile publishers can forge those declarations. Source
URLs are live sites, so retain the exact acquisition cache for long-term rebuilds.
Changed selected text fails the pinned build; changed wrappers alone need not.
No signature trust infrastructure, exhaustive ZIP fuzzing, power-loss injection,
or phone resource/lifecycle acceptance is claimed. Process death can leave an
unused staging file; active archive replacement is atomic. There is one active
imported pack and no removal/merging UI yet. Independent criticism, physical
hardware and broader useful-research evaluation remain open.
