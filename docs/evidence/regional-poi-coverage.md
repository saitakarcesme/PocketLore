# Regional DC POI coverage: task 160

Both named checks pass on LLMRig with the existing API 35 x86_64 emulator-5560, measured 2026-10-01. This is bounded builder evidence, not independent acceptance, phone/GrapheneOS measurement or a current city guide. No inference, private holdout or orchestration work was involved.

## Catalog and exact provenance

Edition **dc-regional-2026-10-01-v2** expands the bundled catalog from three monuments to **25 real places**: eight monuments, eleven museums, three parks/gardens and three civic buildings. Bounds are latitude 38.87–38.91 and longitude -77.06–-77.00, central Washington, DC. The TSV is **9,855 bytes**; its stable asset filename remains dc-monuments.tsv. This catalog is independent of the imported research library.

[Wikidata structured data is CC0](https://www.wikidata.org/wiki/Wikidata:Licensing); [CC0 terms](https://creativecommons.org/publicdomain/zero/1.0/) and attribution are included in the packaged travel notice and THIRD_PARTY_NOTICES. Only source labels, English descriptions, Earth coordinates and provenance are extracted. No images, Wikipedia prose, synthetic factual descriptions, hours or live operational fields are used. Category tags are editorial groupings based on the pinned label/description, explicitly disclosed as such in inspection; they do not infer amenities or access.

The [source lock](../../tools/packs/regional-sources.lock.json) pins all raw hashes, selected coordinate statement IDs, precision, source-modified dates, retrieval date and revision-qualified URLs. The [25 revision refetch receipts](regional-poi/revision-fetch.json) record byte-identical independent refetches on this rig. Hashes establish byte identity, not source truth or authenticity. Source-modified dates describe entity edits, not site visits; all retrieval dates are 2026-10-01.

| Place / source ID | Editorial category | Pinned revision | Latitude, longitude |
| --- | --- | --- | --- |
| Washington Monument [Q178114] | monument | 2522611887 | 38.889475, -77.035244444444 |
| Lincoln Memorial [Q213559] | monument | 2547949032 | 38.889277777778, -77.050138888889 |
| Jefferson Memorial [Q326183] | monument | 2540949369 | 38.881388888888885, -77.03666666666666 |
| Korean War Veterans Memorial [Q708847] | monument | 2540951276 | 38.887778, -77.047222 |
| Vietnam Veterans Memorial [Q713628] | monument | 2497613843 | 38.891111111111, -77.047777777778 |
| World War II Memorial [Q1470020] | monument | 2540955555 | 38.88944444444444, -77.04055555555556 |
| Franklin Delano Roosevelt Memorial [Q592198] | monument | 2540950009 | 38.88388889, -77.04444444 |
| Martin Luther King, Jr. Memorial [Q536802] | monument | 2540949818 | 38.886111, -77.044167 |
| National Museum of Natural History [Q148554] | museum | 2532014048 | 38.8913, -77.0259 |
| National Gallery of Art [Q214867] | museum | 2541643848 | 38.89138888888889, -77.02 |
| National Museum of American History [Q148584] | museum | 2521309747 | 38.89111111111111, -77.03 |
| National Air and Space Museum [Q752669] | museum | 2519978289 | 38.888333333333335, -77.02 |
| Hirshhorn Museum and Sculpture Garden [Q1620553] | museum | 2515909623 | 38.888161, -77.022968 |
| National Museum of African American History and Culture [Q3073495] | museum | 2515928019 | 38.89111111111111, -77.03277777777778 |
| National Building Museum [Q624008] | museum | 2507071156 | 38.8975, -77.018056 |
| National Museum of Women in the Arts [Q861608] | museum | 2495717665 | 38.900051, -77.029315 |
| DAR Museum [Q3798323] | museum | 2540943497 | 38.893608, -77.039716 |
| Freer Gallery of Art [Q1075126] | museum | 2532031281 | 38.888333333333335, -77.0275 |
| National Portrait Gallery [Q1967614] | museum | 2549792178 | 38.897777777777776, -77.02305555555556 |
| National Mall [Q465811] | park-garden | 2539560179 | 38.88944444444444, -77.02305555555556 |
| Lafayette Square [Q6471523] | park-garden | 2539559905 | 38.8995, -77.0366 |
| United States Botanic Garden [Q1848855] | park-garden | 2516626039 | 38.888, -77.013 |
| United States Capitol [Q54109] | civic | 2532197862 | 38.889722222222225, -77.00916666666667 |
| United States Supreme Court Building [Q1579670] | civic | 2550105402 | 38.8905, -77.0045 |
| White House [Q35525] | civic | 2545452879 | 38.897777777777776, -77.03666666666666 |

The National Gallery's English-readable label is stored by Wikidata in the mul field; that exact selector is pinned rather than inventing an en value. MLK Memorial has two non-deprecated coordinate statements; the first statement is explicitly pinned and the alternative count disclosed. Selected coordinates are approximate points, not verified entrances, routes or accessibility information. Overlapping sites, such as the National Mall and museums inside it, are distinct source entities; they are not deduplicated into a route graph.

## Frozen public cases and behavior

Commit **d0a2b2e** froze source selection and [12 public cases](../../tools/evaluation/regional-poi/cases.json) before product filter changes. Fixture SHA-256: b52adce5df4f28138b6f1f33a3fe4c750c7c5933fb9a0809c3fa5065cb81a513. No private holdout was accessed. Cases cover all four supplied categories, case/space normalization, required and avoided phrases, absent restaurant/hotel categories, an absent venue/amenity and conflicting text/category preferences.

The new production filter ANDs a category, a required literal phrase and an avoided literal phrase across the source name plus description. Empty category means all; unknown category means zero. Whitespace around each phrase is trimmed and matching is case-insensitive. These are literal preferences, not semantic, dietary or accessibility inference. Search and planning use the same constraints; conflicting constraints are never relaxed.

The [final raw results](regional-poi/final/results.json) preserve all 25 parsed records/evidence strings, all 12 actual filter results and times, five category plans, a preferred plan and actual Activity text. **12/12 frozen cases pass** and **25/25 records match the locked source fields and coordinate statements**. The check rebuilds twice for byte identity, checks selected fields against original JSON, verifies manifest/payload/notices inside the actual APK, and independently recomputes all selected distance orders in Python.

Planning filters before radius sorting and truncation, excludes the origin, sorts by straight-line distance then source ID, and returns at most three candidates in the UI (API limit 1–5). The actual Activity selection from Washington Monument, within 2 km, category museum, require “art museum”, avoid “Women”, returned:

- Freer Gallery of Art [Q1075126], 0.682 km.
- Hirshhorn Museum and Sculpture Garden [Q1620553], 1.073 km.
- National Gallery of Art [Q214867], 1.336 km.

These are original-origin distances, not successive legs or an itinerary. Each candidate includes its source description, ID and matching category. Source buttons cover exactly the origin and selected candidates. Instrumentation exercises real search/plan controls and checks these buttons, verifies conflicting preferences yield zero stops and restaurant search yields no sources, and opens an actual source dialog. The [inspection screenshot](regional-poi/final/inspection.png) and accessibility text show Q148554's coordinates, statement, revision, raw hash, rights and warnings. These are programmatic control actions, not physical-device taps or human usability review.

Eight rejection controls pass: NaN/infinite/negative radius, unknown origin, zero/six-stop limits, mutated payload and a coordinate statement attributed to another entity. Zero-radius and conflicting-preference plans also return no candidates. The statement-prefix regression preserves the original case of each source ID. Original saved model and research-pack hashes are identical [before](regional-poi/final/saved-before.txt) and [after](regional-poi/final/saved-after.txt); no imports or model calls were needed.

## Measurements and artifacts

Final catalog load/validation: **9.154938 ms**. The 12 single filter calls took **0.158095–0.865051 ms**. Timings use monotonic System.nanoTime around production constructor/filter calls; they exclude app launch, APK installation, rendering and network. There is no warm/cold distribution, sustained/thermal or phone performance claim. [Emulator fingerprint](regional-poi/final/fingerprint.txt) identifies the environment.

- Pack SHA-256: 2240dbd96698266eb27a3f892e346b2e2154c186c097f8ebf79d3f8ede086a8e.
- Source-lock SHA-256: 0d3105f89698d52746dc1edc6c777c74ddbb860c11e3beb2012867fedaaa9772.
- App APK: 11,773,557 bytes, SHA-256 ee1d884d40a3b510c680ee8c9b97e470a22f75f953a7330e59503b45c8ab74cd.
- Test APK: 238,674 bytes, SHA-256 54d94ce3bb745a9c245371d89a5a66d5754dbabcdb22d9504a70db4e7440ce30.
- Raw results SHA-256: 02541fcbfc673b8466cd78f4d8381475a17b982b1e94e4d5cb6a47c3c42ab018.
- bash tools/android-build.sh: exit 0, [standalone log](regional-poi/android-build-final.log).
- bash tools/evaluation/check_regional_poi.sh: exit 0, [summary](regional-poi/final/summary.json), [test build](regional-poi/final/build.log), [instrumentation](regional-poi/final/instrumentation.txt).

The standalone build's APK hash matches the tested final candidate. APKs and source JSON remain ignored under downloads/regional; no binary builds or bulk datasets were committed. The verifier requires actual results, exact expected IDs, provenance and plan predicates, rather than only accepting a PASS label.

## Preserved failures and repair

1. The search API and bare Q148554 EntityData URL returned HTTP 403. Explicit flavor=simple acquisition succeeded; all selected revision-qualified refetches matched. The initial [acquisition log](regional-poi/acquisition.log) also records the missing en label before its mul selector was reviewed. The preliminary 403 observations are recorded in [freeze notes](regional-poi/freeze.md); no raw HTTP response body was retained.
2. Checkpoint **2f8cea9** preserved an unvalidated harness compile failure: Android Files lacks readString. [Build](regional-poi/compile-failure/build.log) and [traceback](regional-poi/compile-failure/check.log) are unchanged; the harness now reads bytes with UTF-8.
3. The next real run failed loading the catalog because validation incorrectly assumed an uppercase Q statement prefix. Genuine pinned statements use both cases. [Raw failure](regional-poi/claim-case-failure/results.json) and [build](regional-poi/claim-case-failure/build.log) remain preserved. Case-insensitive prefix checking now accepts the originals; another entity's prefix still rejects.
4. The [first passing run](regional-poi/first-pass/summary.json) preceded the expanded bundled attribution notice. The final run additionally verifies the exact current payload, manifest and notice inside the new APK. Old three-record assertions were adapted to the larger catalog's count and nearest neighbors; task-060 historical evidence remains unchanged. The old broad travel check was not rerun in this task.

## Reproduction and open limits

See [travel instructions](../TRAVEL.md). On the provisioned rig, explicitly fetch missing immutable inputs, then build and validate:

    python3 tools/packs/build_travel.py --fetch --install
    bash tools/android-build.sh
    bash tools/evaluation/check_regional_poi.sh

Fetching is an online setup operation. Gradle regenerates offline from exact cached revisions and refuses missing/changed bytes or a mismatched checked-in manifest. Historical revision availability and independent clean-machine reproduction are not guaranteed by this same-rig measurement. The check reuses emulator-5560 and replaces the debug APK with install -r while preserving saved assets; it does not launch/restart services. Test fixtures are absent from the product APK.

Opening hours are unavailable and saved hours may be stale. Routing, walking time, closures, current access, accessibility and reservations remain unverified/unavailable in UI, plans and inspection. No live availability is fabricated. This bounded 25-record catalog has no restaurants, hotels, dietary data, map/path graph, arbitrary regional imports, optimized scheduling or broad natural-language preferences. Human usefulness and independent source accuracy review remain open, as do physical Android/GrapheneOS and release acceptance. Tasks 170–180 remain independent rig work and the changed APK needs a later release freeze. No push, branch switch, main advancement, runner/state/service change or private context access occurred.
