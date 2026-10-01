# Offline travel and tools

Open **Offline travel and tools** on the research screen. The bundled edition dc-regional-2026-10-01-v2 covers 25 places in central DC (38.87–38.91 latitude, -77.06–-77.00 longitude): eight monuments, eleven museums, three parks/gardens and three civic buildings. Categories are editorial groupings of source labels/descriptions, not amenity claims. Choose a category, a required literal phrase and an avoided literal phrase; all three constraints apply to search and planning. Matching is case-insensitive and trims surrounding spaces. Conflicts or absent categories return no matches rather than relaxing preferences. Choose a starting place and a 0–10 km straight-line radius to shortlist at most three other stops. Candidates are sorted by distance from the starting place; this is neither a sequence of walking legs nor an optimized route or timed itinerary. Inspect each source for its dated coordinates, description, Wikidata revision, raw hash and CC0 attribution.

Opening hours are not supplied. Offline hours may be stale; routing, walking time, closures, access, accessibility, reservations and open-now status are unavailable. No live data or model inference is invoked. Unknown place queries return no matching places. This is not a full city guide or a dietary/local-business planner.

Calculator examples:

- `convert 1 mi km` → 1.609344 km; supported distance units: m, km, mi.
- `convert 32 F C` → 0 Celsius; C/F temperatures only.
- `add-days 2024-02-28 1` → 2024-02-29.
- `days-between 2024-02-28 2024-03-01` → 2 calendar days, end minus start.
- `distance Q178114 Q213559` → spherical straight-line kilometers from the sourced coordinates, not a route.

Dates are ISO local calendar dates with no timezone, opening-hours or flight-duration semantics. Distance uses a 6,371.0088 km mean spherical Earth radius, ignoring elevation, paths and barriers. Coordinate precision and the Earth approximation limit accuracy. Invalid/non-finite inputs and incompatible dimensions reject; input/output units remain explicit.

## Reproduce

Provision the existing Android toolchain/runtime using the runtime guide. Fetch the 25 pinned source revisions explicitly while online:

```sh
python3 tools/packs/build_travel.py --fetch --install
bash tools/android-build.sh
bash tools/evaluation/check_regional_poi.sh
```

Raw source JSON and generated packs live under ignored `downloads/regional`. Gradle rebuilds the bundled TSV offline from this cache, verifies raw hashes/revisions and compares its manifest with the checked-in manifest. Missing or changed source bytes fail the build; they are not silently replaced. The runtime independently verifies the pinned payload SHA-256, bounds and schema before exposing any POIs. This small catalog is bundled separately from the research knowledge pack and cannot replace an imported research library. Arbitrary region imports are not implemented.

The new check uses 12 frozen public filters, verifies byte-identical regeneration and exact source extraction, independently checks distance ordering, and exercises production classes and actual Activity controls on existing `emulator-5560`. It does not start services or an emulator. APK installation replaces the debug app while retaining its data. Downloaded source revisions are CC0 structured Wikidata data; the pack contains only source labels/descriptions, numeric coordinates and provenance plus editorial category tags, not synthetic factual prose.

The stable asset filename remains dc-monuments.tsv for compatibility; the bundled manifest identifies the new edition and schema 2. The original three-place lock and task-060 evidence remain historical. Source IDs, statement IDs (including their original letter case), revisions, dates, precision and coordinate alternatives are inspectable. Dates describe Wikidata edits, not on-site verification. Source buttons for a plan include the origin and exactly its selected candidates. The broader catalog does not add restaurants, hotels, dietary/amenity data, live availability, route graphs or timed itineraries. See [regional evidence](evidence/regional-poi-coverage.md).
