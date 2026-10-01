# Offline travel evidence — task 060

Both named checks passed on LLMRig on 2026-10-01: `bash tools/android-build.sh` and `bash tools/evaluation/check_travel.sh`. This is bounded host/emulator development evidence, not independent acceptance, physical Android/GrapheneOS validation, a complete destination guide or generated-answer quality evidence. No model inference was required. No private holdout, runner state, orchestration, services or global preferences were touched; no branch switch or push occurred.

## Product and provenance

The Android research screen now opens a separate offline travel/tools screen. It searches three real POIs, displays inspectable source records, and builds a nearest-candidate shortlist within a user-specified straight-line radius from one of those places. It provides deterministic length/temperature conversion, calendar arithmetic and spherical coordinate distance. The existing imported research pack is retained; this travel catalog does not replace it.

The bounded region is latitude 38.87–38.90, longitude -77.06–-77.02 around the National Mall/Tidal Basin in Washington, DC. The pack is **909 bytes**, containing three verbatim English Wikidata labels/descriptions and their Earth coordinates. No synthetic factual descriptions, images or Wikipedia prose are included. Wikidata structured data is [CC0](https://www.wikidata.org/wiki/Wikidata:Licensing); source attribution is bundled in Android and recorded in `THIRD_PARTY_NOTICES`.

| POI | Source revision | Source modified date | Coordinates (latitude, longitude) |
| --- | --- | --- | --- |
| Washington Monument Q178114 | 2522611887 | 2026-07-25T18:46:14Z | 38.889475, -77.035244444444 |
| Lincoln Memorial Q213559 | 2547949032 | 2026-09-20T14:58:26Z | 38.889277777778, -77.050138888889 |
| Jefferson Memorial Q326183 | 2540949369 | 2026-09-06T08:01:25Z | 38.881388888888885, -77.03666666666666 |

All were retrieved 2026-10-01. [The source lock](../../tools/packs/travel-sources.lock.json) records exact raw hashes, source revisions and dates. [Independent revision fetches](travel/revision-fetch.json) reproduced all three original raw hashes. Source modification dates describe the entity revision, not on-site verification dates. Source coordinates can be approximate and do not establish entrances or accessible paths.

Pack SHA-256: `6cb245864d7b42facc8b987d7e4843f795b87912062d09a8bbddcdc034877924`.
Source-lock SHA-256: `5016fa4e06089d02cb6c4fa7f333a003f17affa377ffb9ba865209debc2610b3`.
The [bundled manifest](../../android/app/src/main/assets/dc-monuments-manifest.json) pins count, bounds, rights, payload and source-lock hash. Raw assets and generated TSV stay ignored. Gradle regenerates the TSV offline from pinned cached inputs; missing or changed input fails. Android verifies its compiled payload hash and rejects malformed/non-finite/out-of-region or duplicate records. Hashes establish byte identity, not publisher authenticity or current accuracy. This is a bundled catalog, not arbitrary region-pack import support.

## Behavior and measured results

[Development cases](travel/development-cases.md) were committed before implementation in `7d62197`. No private holdout was accessed. [Final summary](travel/final/summary.json), [host results](travel/final/host.txt), [emulator results](travel/final/emulator.txt), [instrumentation](travel/final/instrumentation.txt), [standalone build](travel/build-final.log), and [test APK build](travel/final/build.log) preserve actual outputs. Run directory: `downloads/travel/verify-20261001T011541Z`; both APKs are archived there, outside Git.

- 31 assertions run against production classes on both the host JVM and AOSP x86_64 emulator. They cover case-insensitive/absent search, exact source IDs, nearby-place order and radius, provenance, unit dimensions, leap days/invalid dates, equatorial/antimeridian/invalid-coordinate distance, non-finite inputs, corruption, duplicate IDs and region rejection.
- Seven additional assertions use actual Android Activity controls: catalog load, search result, source inspection button, planning result, conversion result, invalid-date rejection and absent-place result. Final total: 38 emulator assertions. These are instrumentation actions, not physical-device finger taps or human usability acceptance.
- From Washington Monument with a 2 km radius, actual host/emulator output lists Jefferson Memorial at **0.908 km** and Lincoln Memorial at **1.289 km**. Both distances are measured from the original starting place, not successive itinerary legs. Both endpoints' source IDs are displayed. The labels/descriptions and coordinates are the evidence; no claim is made about suitability, current access or walking feasibility.
- `1 mi` converts to `1.609344 km`, `32 F` to `0 C`, and `2024-02-28 + 1 day` to `2024-02-29`. Date differences count local calendar days; no timezone, flight duration or open-now status is inferred. Spherical distance uses radius 6,371.0088 km, not a routing graph, and ignores elevation/barriers. Rounded display values are not precision guarantees.

| Measurement | Host JVM | AOSP x86_64 emulator |
| --- | --- | --- |
| Single catalog load/validation | 14.652 ms | 2.408 ms |
| Mean search plus plan, 1,000 warm iterations | 0.029664 ms | 0.159360 ms |

Measurements exclude Activity rendering, provisioning, full app launch, JNI/model work and network, and are not p95, peak-memory or phone latency claims. The small catalog makes these timings unsuitable for scaling predictions. [Environment fingerprint](travel/final/environment.txt) identifies the emulator.

APK SHA-256: `688daa5f5069729a23d670b8a4b2882f0b0761832ada5bcb8f75bd930488becb`.
Test APK SHA-256: `6e50ce820deb4ce703127668300f54e500f9f6b96f774e7596218b3d38fc930f`.

## UI inspection and preserved limitations

The first behavioral build passed but visual inspection found content at the system bars. [Initial screen](travel/ui-before.png) preserves that layout defect; inset handling and a visible radius label were added. Final [screen](travel/ui-final.png) and [actual plan](travel/plan-final.png) were inspected after navigating through the main-screen travel button and tapping the plan button via adb. Corresponding UI hierarchy dumps are preserved under `travel/final/`. Initial build/test evidence is retained under `travel/first/`; neither named final check failed. The screen is a scrollable functional slice with explicit command syntax, not a polished natural-language travel assistant.

Opening hours are **not supplied**; the screen and plan say offline hours may be stale. Routing, walking times, closures, reservations, accessibility and current access remain unverified/unavailable. A candidate shortlist is explicitly not a route or timed itinerary. No live values are fabricated and no travel runtime code makes network calls; the Android manifest has no network permission.

Coverage is only three monuments: no restaurants/dietary selection, lodging, transit, path network, maps, rich attraction descriptions, live hours, wider-region imports or preference-aware scheduling. Source inspection is by matching POI buttons rather than inline clickable plan spans. Calendar tools do not infer events or availability. Broader planning usefulness, human evaluation, resource peaks, sustained performance and physical Android/GrapheneOS acceptance remain open. [Reproduction instructions](../TRAVEL.md) document offline build prerequisites and exact tool semantics. Evidence hashes are frozen in [SHA256SUMS](travel/SHA256SUMS).
