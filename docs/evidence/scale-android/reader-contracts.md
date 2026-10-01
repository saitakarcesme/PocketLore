# Actual Android source and reader contracts

This lane changes setup/library/model/source flows, not upstream bulk schemas or bulk data construction. It has not received another lane's sealed full-shard reader contract. A complete shard or one million places is not claimed here.

## Existing readers retained

- Small `.plpack`: `KnowledgePack` consumes the existing manifest/text ZIP contract and constructs an in-memory bounded index. `PackLibrary` retains at most eight collections with combined small archive/expanded limits of 16 MiB, 1,000 documents, 5,000 active passages, one million text characters and 200,000 tokens. It checks heap reserve before allocation. This is not a large-pack reader.
- Prebuilt `pocketlore-sqlite-v1`: `BroadPack` reads `manifest.json`, `index.sqlite`, and the hash-pinned `CC-BY-SA-4.0.html`. Manifest identity, exact schema, source and passage hashes, source offsets, counts, attribution and license are validated. Current bounds remain one broad edition, 128 MiB archive, 256 MiB expanded database, 5,000 documents and 100,000 passages. These are compatibility bounds, not measurements supporting larger packs.
- Database `user_version=210`, exact schema from the manifest, `search` FTS4 with porter tokenization; `documents(id,title,url,date,rights,provenance,body,sha)` and `passages` fields consumed by the reader include `pid,document,citation,body,sha,start,end`. Actual SQL remains in `BroadPack.java`; a new lane must supply its exact DDL rather than infer a format from this field summary.
- Queries open read-only SQLite, disable mmap, set a 2 MiB page cache and select bounded passage candidates. No corpus-sized Java object graph or permanent database handle is introduced. Import integrity validation scans rows and hashes files; startup also rehashes the database. Those I/O costs need separate scale measurements.
- Travel uses the existing pinned 25-place English Wikidata TSV contract, not a million-place disk reader. No claim of compatibility with a new bulk places schema is made.

## Import and removal

SAF imports request local-only files. UI requires known archive/model sizes. Stream buffers remain 64 KiB; model files remain at most 2 GiB. Pack copy enforces the declared size and checks the full copy plus 256 MiB reserve; SQLite extraction separately checks expansion plus reserve. Model SHA-256 is shown after import and recalculated on reload. Hashes identify bytes; they do not authenticate rights or publisher. Existing native validation remains mandatory.

Durable `model-import.pending` and `pack-import.pending` markers precede copying/provider opening and clear only after successful activation. Failed/cancelled imports remain labeled interrupted or failed on restart. Retry starts from the original provider; arbitrary byte-offset resume is unsupported. Existing cleanup deletes only recognized owned staging paths. Original files are retained.

Collection removal builds the retained snapshot, atomically commits its catalog, then cleans owned unreferenced archives/indexes; cleanup retries on subsequent load. Empty committed catalogs prevent legacy resurrection. UI requires explicit edition confirmation. Model removal requires confirmation and unloads before deleting the saved GGUF. Filesystem directory fsync/power-loss durability has not been measured; this is process-interruption handling.

## Profiles and source display

Android remains CPU-only, two inference threads, one session, context 2048, FP16 KV cap 768 MiB, compute cap 1024 MiB and model cap 2048 MiB. Component limits do not imply peak process or OS safety. The UI explicitly reports that no measured larger-model profile exists for 4B, 7–8B or MoE; raising the current ceiling requires exact model hash/quantization, native allocations, context, device/OS, Java memory, OS reserve and sustained measurements are supplied. No host result admits a phone profile.

Source dialogs preserve selectable Unicode text, scroll, citation IDs, provenance, dates and rights, with missing display values labeled Unknown. No mathematical rendering or source conversion is inferred. Generated, fallback, abstained and cancelled labels retain their previous meaning; linked citations do not establish entailment. Large-font visual checks remain queued.

## Queued integration command and fixtures

After coordinator assignment, rebuild with `-PpocketloreTestRunner=org.pocketlore.app.ScaleLibraryInstrumentation --max-workers=1 assembleDebug assembleDebugAndroidTest` using the lane cache. Install both APKs on the assigned serial, stage an existing source-validated small pack as app-private `files/scale-valid.plpack`, then run:

```
adb -s ASSIGNED_SERIAL shell am instrument -w org.pocketlore.app.test/org.pocketlore.app.ScaleLibraryInstrumentation
```

The fixture must carry its SHA-256 and original source provenance in device evidence. The runner uses an isolated app-cache directory; the UI checks listed in `ux-freeze.md` additionally require real interaction, process kills and screenshots. No emulator or device result exists for this candidate. Do not run against reserved emulator-5560 without coordinator release.
