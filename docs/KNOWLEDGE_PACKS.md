# English reference packs

Task 030 adds a separately imported, reproducible English reference pack. It is
not bundled into the APK and does not replace the eight-passage starter until
selected by the user. The first edition contains 186 passages from 10 documents:
38 water-science passages (USGS), 126 historical founding-document passages
(National Archives transcriptions), 10 practical outdoor-reference passages and
12 Yosemite/Yellowstone travel passages (National Park Service).

This is a deliberately small, US-focused expansion, not comprehensive science,
world history, travel coverage, a current legal reference, or emergency guidance.
The original Constitution includes superseded provisions and historical slavery
language. Its title and original date distinguish it from current law. Travel
pages are dated snapshots: conditions, regulations and closures can change.
Source inspection displays the document title, URL, date status, retrieval date,
attribution and rights. Edition warnings and exact source/pack hashes appear in the source dialog; notices from older app versions are labeled.

## Reproduce on LLMRig

```sh
# Explicit acquisition only; all downloaded HTML and pack bytes are ignored.
python3 tools/packs/build_pack.py --download
# Subsequent builds are offline and byte-for-byte deterministic.
python3 tools/packs/build_pack.py
bash tools/android-build.sh
python3 tools/packs/verify_pack.py
```

The build uses Python's standard library. `tools/packs/sources.lock.json` records
source URLs, original acquired HTML SHA-256, exact selected block SHA-256 values,
source dates (page byline/update dates or historical document dates), UTC retrieval date,
English language, category, attribution and rights. The edition date is October
1 in the rig's Europe/Luxembourg time zone; acquisition was September 30 UTC.
Raw acquisition caches live in `downloads/packs/raw`. The default artifact is
`downloads/packs/english-reference.plpack`. Retain the original cache with an
archived release; upstream websites are not immutable archive services.

Fetches of changed page wrappers may still reproduce the same selected content:
the builder checks every selected normalized block hash, not dynamic HTML page
wrappers. `raw_sha256` identifies the original acquisition, not a claim that a
later live page is unchanged. If a pinned paragraph changes or disappears, the
build fails and keeps the downloaded response for diagnosis. No automatic pin
refresh or generated factual replacement is allowed. To retain precise original
HTML provenance, compare a cache file's SHA-256 to `raw_sha256` in the lock.

Only reviewed textual blocks are included, with HTML removed and whitespace
normalized. Stable citation IDs combine a fixed document identifier and the first
16 hexadecimal characters of the complete text hash; duplicate IDs are rejected.
The full hashes remain in the manifest. No photographs, maps, media, logos,
third-party book text or navigation elements are copied. The NPS plate-tectonics
page was excluded because it credits external material. NPS Ten Essentials
explanatory text retains its credit to The Mountaineers for the ten-category
system; the referenced book is not included. Federal text is public domain in
the United States, not an assertion that every government-hosted item or every
jurisdiction has identical terms. Original founding-document text is public
domain. See `THIRD_PARTY_NOTICES` and the per-document policy URLs.

## Import contract

A `.plpack` is a ZIP with exactly `manifest.json` and UTF-8 `passages.tsv`.
The manifest has schema 1, language `en`, edition ID, transformation, warning,
document metadata, full per-passage hashes, total count and payload hash.
TSV fields are citation ID, title, URL, source/retrieval dates, attribution/rights,
and text. The importer requires row metadata to match its document manifest.

`KnowledgePack` validates the compressed and expanded size bounds (16 MiB),
manifest bound (2 MiB), supported schema/language, UTF-8, entry names, duplicate
entries/documents/citations, ZIP directory and CRC consistency, metadata,
payload and passage hashes, citation derivation and row counts. It never extracts
ZIP paths. The Activity now uses `PackLibrary`: verified archives are retained by full
SHA-256 in `files/pack-library`, while an atomically committed catalog records active
collections. One combined index is constructed after aggregate admission. The old
`knowledge.plpack` is migrated once and retained unchanged; the legacy installer API
remains for isolated historical checks. Every catalog load revalidates its archives.
Failed/cancelled imports preserve the committed catalog and remove their stages;
crash-orphan cleanup is restricted to this library's owned directory.

Import both the reference and science editions, then tap **Choose collections** and
**Apply** to select what is searched. Both remain installed across restart. Selecting
none leaves search explicitly empty. **Reload library** restores the active index
after an Android memory-trim callback. Search results expose **Inspect source** buttons
with edition, original citation, full source/text hashes, dates and rights. Citation
IDs are namespaced by full archive hash; exact duplicate source snapshots/text/rights
are indexed once with all active edition provenance retained. Original pack bytes and
licenses are unchanged. See [multi-pack measurements](evidence/multi-pack-library.md).

Hashes are corruption checks, not a publisher signature. A malicious publisher
can construct an internally consistent false pack; users must obtain packs from
trusted sources and compare the displayed archive SHA-256 with a trusted release.
The importer does not fact-check text or independently recognize its language.
The catalog admits at most eight retained collections and applies aggregate archive,
expanded-data, manifest, document and active index budgets. Inactive collections still
consume storage. Removal UI and background resumable installation remain future work.
The index/heap admission policy is deliberately below task-170's largest measured
repetition-only workload; diverse-corpus and physical-device behavior remain open.

## Current multi-pack verification

Run `python3 tools/evaluation/verify_multi_pack_library.py` with the pinned public
artifacts and existing emulator-5560. It archives only recognized project fixture
catalogs before testing; unrelated user collections cause a refusal. It exercises
combined/disabled retrieval, actual controls and dialogs, duplicates, integrity and
cancellation rollback, combined admission, cold restart and platform-trim reload.
It keeps the saved model unchanged and deliberately unloads it during retrieval
measurements. These are not generated-answer quality results. Tasks 201 and 202
revalidate JNI integration and the changed release candidate separately.

## Historical single-pack behavioral verification

The following describes the preserved task-030 run, not the current Activity catalog
contract; its legacy saved-file/UI assumptions require release revalidation.


The verifier rebuilds twice and compares bytes, constructs corrupt archives,
builds and installs the APK plus `PackSmokeInstrumentation`, and runs the actual
Android importer on the existing `emulator-5560`. It requires that emulator to
be booted; it never launches one. The production path must reject every corrupt
fixture, preserve the previously installed hash and retrieval index, and clean
staging files. It also retrieves source text in all four categories. No model
substitute or synthetic factual corpus is used.

The verifier then uses Android's document picker to import the real pack, checks
the private saved archive hash, restarts the app, imports a corrupt pack, and
opens an NPS source from the live answer flow. It leaves the reference pack
installed on this test emulator. Earlier starter-specific answer checks require
the bundled starter state and should not be silently interpreted against this
new corpus. The current tests cover corruption, not adversarial archive fuzzing,
power-loss injection, retrieval quality or answer-quality acceptance. Measurements
and preserved failed test attempts are in [task evidence](evidence/knowledge-pack.md).
