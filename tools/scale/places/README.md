# Global offline places lane

All acquisition, processing and host verification run in this isolated LLMRig lane. The primary asset is the complete official Overture Places release `2026-09-23.1`, represented by 16 standard SQLite compressed-block shards. The original 16 Parquet objects are pinned by official object list, byte counts, SHA-256 receipts and upstream ETags. Every named valid point/UUID record is eligible regardless of country or confidence. Counts, completed stages and budget results must be read from the sealed handoff rather than inferred from script availability.

## Build and verification

Use the private `places/venv/bin/python` with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 OSMIUM_POOL_THREADS=1`. `acquire_ranges.py` validates bounded byte ranges against the official release object list, records actual mirror URLs and preserves partials/failures. `compact_all.py` owns the private writer lock and runs two single-threaded workers over exactly all 16 objects. `compact.py` uses DuckDB (one thread, 512 MB working-memory limit) and Arrow batches of 2,048 rows. Private spill files and bulk assets stay outside Git. No model calls, GPU, per-place requests or research-time network are needed.

Original non-geometry fields are retained in full, including names, contacts, addresses, categories, operating status and source-property provenance. Exact WKB point coordinates are retained as doubles. Invalid records are retained in `rejected`; no geographic or confidence filtering is permitted. Source IDs remain individually inspectable. Search groups only identical normalized names, exact coordinates and categories, choosing the lowest source ID deterministically. Near matches remain separate; this conservative grouping does not establish real-world semantic uniqueness.

`compact_audit.py` uses 128 deterministic disk partitions to calculate exact global distinct source IDs and exact entity hashes, field fill and country-label counts, and compares the complete input/output ID sets. `source_audit.py` separately measures original field fill and literal provider/license entries. `oracle_checks.py` runs the unchanged 100 frozen queries across 20 cities and six continents against original Parquet and SQLite, checking ordered identities and exact record fields. Empty results are not proof of geographic coverage or real-world absence. SQLite `quick_check` is used; earlier exhaustive integrity scans were interrupted and are not counted as passed. `finalize_work.py` executes finite postprocessing stages under one lock, records transitions atomically and stops on failure without automatic unchanged retries.

The initial row-per-record schema 1 is retained as measured failed staging: one 5.07-million-ID shard alone occupied 7.14 GB. It is superseded by lossless block schema 2. Old scripts/assets and failed logs are preserved. Both formats exceeding the provisional 4 GB global budget is a failed admission gate, not authorization to discard regions. The published AndroidLM database is separately pinned by dataset revision and verified LFS SHA-256 for data-only comparison. Its actual counts differ slightly from its card. Compare measured coverage and field presence using the evidence report; different category/confidence/status filters, native coordinate precision and deduplication rules prevent count ratios from proving real-world uniqueness or superior quality. No rival application/build code is copied or executed.

## Actual reader contract

Schema 2 metadata is JSON in `metadata(key,value)`. `block(id,records,payload,sha256)` stores zlib UTF-8 JSON arrays of `[original_ordinal,latitude,longitude,normalized_name,original_record]`; ordinals are 1-based source positions. Every compressed block is at most 1 MiB and every inflated block at most 32 MiB. Oversized batches split without record loss. `grid` indexes 0.1-degree integer cells; `category` indexes primary, hierarchy, alternate and basic labels; `city` indexes the first source-address locality without claiming administrative containment. Readers verify block SHA-256 and bound inflation before parsing.

`compact_search.py` supplies bounded multi-shard radius/category/exact-name/city search with exact Haversine filtering, pole/antimeridian handling and deterministic grouping. `source(shard,block,ordinal,id)` returns the original full source record and coordinates. `catalog.py` exposes city candidates, nearby places with separately attributed unconfirmed OSM candidate objects, explicit-tag dietary results, and exact-title travel revision links/full original text. Dietary values are never inferred from Overture categories. Combined Overture category plus OSM diet is explicitly unsupported until cross-source identity/taxonomy is established.

`android/CompactPlaces.java` is a standard `SQLiteDatabase`/zlib/JSON per-shard radius/category and source reader, compiled against API 35. It uses no extension, custom collation, Play Services or network. `android/OsmPlaces.java` supplies explicit-tag radius queries and source inspection for the OSM block asset. Both use the same 1 MiB compressed/32 MiB inflated block caps. Compilation is not runtime validation. App integration, multi-shard Android result merging, source-family UI, installation/hash admission and actual phone memory/performance remain open. Verify sealed whole-file hashes before opening read-only assets; label all facts with their source snapshot date. Never treat dated operating status or hours as live status.

## Other source families

`planet.py` streams the official `planet-260921.osm.pbf` and preserves every node, way and relation with `diet:vegan`, `diet:vegetarian` or `opening_hours`, even without names or coordinates. Exact type/ID/version/timestamp, all tags, node/member references and planet hash remain in a separate ODbL SQLite database; The preserved row-format staging stores `raw` as zlib UTF-8 JSON. The selected `osm-compact.sqlite` schema 2 stores bounded zlib JSON arrays of `[latitude,longitude,complete source object]` in `block`, with SHA-256 checks and a type/ID lookup pointing to block/slot. The common planet hash is stored once in `snapshot` and metadata. Partial spatial/name and positive-diet indexes support offline lookup. `osm_read.py` reconstructs source fields; all 4,870,526 objects and coordinates are compared against the preserved row-format asset before selection. One decoder thread and queue of two bound decoding. `planet_geometry.py` resolves way bounding-box centers only when every referenced unique node is present, using disk tables and at most 10 million IDs per decoder pass. Such centers are labelled derived, not entrances. Relations stay unlocated and retained. `enrich.osm_search` requires explicit `yes`/`only`; absent values stay unknown and hours strings are never evaluated as current opening status. Exact normalized name within 50 m is an unconfirmed candidate only, never an overwrite of Overture. Regional cached extracts and failed global/tiled Overpass attempts remain historical evidence, not global coverage claims.

`geonames.py` imports all cities500 rows and supplied aliases, retaining the original row and modification date. The mutable download has an exact hash/acquisition date but unknown upstream release date. This population/admin-seat selection is not every settlement. Ambiguous aliases return multiple cities.

`wikivoyage_xml.py` retains every page/namespace, revision, timestamp, original SHA1 and compressed wikitext from the official full English `20260901` pages-articles XML; its published SHA1 was checked. Literal listing templates preserve raw text and nested fields without template execution. `travel.py` separately extracts all nonredirect HTML pages from the read-only cached full English September ZIM. Missing extracted revision/license links remain unknown. Listing occurrences are not unique places, and XML/ZIM overlap cannot be added as independent coverage. The official XML database is the primary travel asset; the ZIM-derived database is a measured optional supplement, retained in staging.

## Attribution and rights

- Overture Maps Foundation and the providers in every `sources` entry; official release and per-source licenses, IDs, versions and update times are retained. Literal source-license counts are evidence, not distribution clearance. Missing rights remain unknown.
- © OpenStreetMap contributors, https://www.openstreetmap.org/copyright, ODbL 1.0. Separate database; derived/collective database distribution obligations require review.
- GeoNames, https://www.geonames.org/, CC BY 4.0. Indexing and normalization are modifications; original rows remain available.
- Wikivoyage contributors, https://en.wikivoyage.org/, CC BY-SA 4.0, with page revision/history links and original notices. Extraction/indexing are modifications. No media rights are inferred.

Official rights captures and hashes are retained. Distribution readiness, independent criticism, human usefulness, Android/GrapheneOS hardware acceptance and total installed-asset admission remain separate gates. No shared emulator is used by this lane.

## Offline use of the staged catalog

From this repository, add `tools/scale/places` to Python's module path and open only the assets admitted by the sealed manifest:

```python
import pathlib
import sys
sys.path.insert(0, 'tools/scale/places')
from catalog import Catalog
assets = pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data')
catalog = Catalog(
    [assets / f'compact-{i:02}.sqlite' for i in range(16)],
    assets / 'cities.sqlite', assets / 'osm-compact.sqlite',
    assets / 'wikivoyage.sqlite',
)
choices = catalog.city_candidates('Lisbon')
nearby = catalog.nearby(38.72, -9.14, 3, category='restaurant')
vegan = catalog.nearby(38.72, -9.14, 3, diet='vegan')
guide = catalog.travel_nearby(38.72, -9.14, 3)
```

These are local database operations, without HTTP or model calls. Overture candidate enrichment retains every matching OSM source object within the declared exact-name/50 m rule, with unconfirmed identity and conflicting tags intact. `source_variants(row)` yields every preserved original record in one exact group. Name normalization is NFKC, case folding and whitespace collapse. GeoNames alias queries return at most 100 candidates in population order; all source rows/aliases remain stored. Travel proximity results are literal coordinate-bearing listing occurrences, not unique places; `travel_source(page_id)` returns the exact stored article revision, original wikitext and listing templates. Callers must show snapshot dates, provenance, unknown facts and derivation labels.

The optional ZIM archive has a verified cached acquisition receipt and internal date, but no archive-level `License` metadata value. Article-level links and the original HTML remain the relevant retained attribution evidence; missing extracted links stay unknown. Its page counts use enumerated nonredirect HTML entries, not the archive's aggregate `Counter` label.
