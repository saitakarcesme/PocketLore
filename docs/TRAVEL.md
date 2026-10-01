# Offline travel and tools

Open **Offline travel and tools** on the research screen. The bundled slice covers three monuments in a bounded DC rectangle: Washington Monument, Lincoln Memorial and Jefferson Memorial. Search names/descriptions or choose a starting place and a 0–10 km straight-line radius to shortlist at most two other stops. Candidates are sorted by distance from the starting place; this is neither a sequence of walking legs nor an optimized route or timed itinerary. Inspect each source for its dated coordinates, description, Wikidata revision, raw hash and CC0 attribution.

Opening hours are not supplied. Offline hours may be stale; routing, walking time, closures, access, accessibility, reservations and open-now status are unavailable. No live data or model inference is invoked. Unknown place queries return no matching places. This is not a full city guide or a dietary/local-business planner.

Calculator examples:

- `convert 1 mi km` → 1.609344 km; supported distance units: m, km, mi.
- `convert 32 F C` → 0 Celsius; C/F temperatures only.
- `add-days 2024-02-28 1` → 2024-02-29.
- `days-between 2024-02-28 2024-03-01` → 2 calendar days, end minus start.
- `distance Q178114 Q213559` → spherical straight-line kilometers from the sourced coordinates, not a route.

Dates are ISO local calendar dates with no timezone, opening-hours or flight-duration semantics. Distance uses a 6,371.0088 km mean spherical Earth radius, ignoring elevation, paths and barriers. Coordinate precision and the Earth approximation limit accuracy. Invalid/non-finite inputs and incompatible dimensions reject; input/output units remain explicit.

## Reproduce

Provision the existing Android toolchain/runtime using the runtime guide. Fetch the three immutable source revisions explicitly while online:

```sh
python3 tools/packs/build_travel.py --fetch --install
bash tools/android-build.sh
bash tools/evaluation/check_travel.sh
```

Raw source JSON and generated packs live under ignored `downloads/travel`. Gradle rebuilds the bundled TSV offline from this cache, verifies raw hashes/revisions and compares its manifest with the checked-in manifest. Missing or changed source bytes fail the build; they are not silently replaced. The runtime independently verifies the pinned payload SHA-256, bounds and schema before exposing any POIs. This small catalog is bundled separately from the research knowledge pack and cannot replace an imported research library. Arbitrary region imports are not implemented.

The check freezes the three-place behavior, verifies byte-identical pack regeneration, runs shared production assertions on the host and existing `emulator-5560`, and invokes actual Activity buttons. It does not start services or an emulator. APK installation replaces the debug app while retaining its data. Downloaded source revisions are CC0 structured Wikidata data; the pack contains only verbatim English labels/descriptions and numeric coordinates, not synthetic factual prose.
