# Frozen travel development cases — 2026-10-01

Frozen before travel implementation. No private holdout is used.

- Search case-insensitively for Lincoln; only Lincoln Memorial matches. Unknown restaurant query returns no match, not an invented venue.
- Search the bounded three-monument DC pack. Each POI has source ID, coordinates, revision/date, raw source hash and CC0 attribution; source inspection resolves the selected ID.
- Plan up to two other stops from Washington Monument within a 2 km straight-line radius. Exclude the starting POI; verify ascending spherical distances and both source IDs. A 0 km radius yields no other stops. This is a candidate shortlist, not walking directions or a timed itinerary.
- Always disclose missing/stale opening hours and unavailable routing, walking times, live access, accessibility and booking status. Do not infer open-now or a visit time from the date calculator.
- Exact conversion: 1 mile = 1.609344 km; 32 Fahrenheit = 0 Celsius; dimensional mismatch and non-finite values reject.
- Calendar: 2024-02-28 plus 1 day = 2024-02-29; difference from 2024-02-28 to 2024-03-01 = 2 calendar days; invalid date rejects. No timezone/flight-duration inference.
- Distance: identical coordinates = 0; equatorial 1 degree = approximately 111.195 km; antimeridian 179 to -179 degrees = approximately 222.390 km; invalid coordinates reject.
- Payload corruption, duplicate IDs and out-of-region/non-finite coordinates reject; no silent partial catalog.
- Execute production behavior on host and existing x86_64 emulator, exercise actual UI search/planning/tools/source buttons, and preserve outputs and timings. Physical Android acceptance remains open.
