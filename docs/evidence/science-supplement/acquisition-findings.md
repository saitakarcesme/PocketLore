# Acquisition findings before retrieval evaluation

2026-10-01, LLMRig. No retrieval evaluation ran before freezing source blocks and 12 cases.

- Initial USGS candidate paths `/faqs/what-volcano` and `/programs/earthquake-hazards/science/science-earthquakes` returned HTTP 404. Canonical About Volcanoes and magma/lava pages replaced these candidates.
- NASA Sun, Mars and Moon pages were fetched into ignored storage, but not selected. Current NASA media/AI attribution guidance complicated their use in a source-linked generated-answer application; no NASA text or media enters this edition.
- NOAA jet-stream, atmosphere and energy pages returned HTTP 403 to the rig acquisition attempt. These were replaced by USGS geomagnetism documents, not fabricated or silently omitted from the required document count.
- Final topics: geology (three documents), geomagnetism (three), genetics (two). Body paragraphs were reviewed before hashing. NHGRI duplicate responsive blocks are selected only once. Related-article teasers and all media/captions are excluded.
- USGS selected articles do not state a clear article publication/update date; their provenance explicitly distinguishes that unknown value from the 2026-10-01 snapshot date. Related-item dates are not reused as article dates. NHGRI DNA and chromosome pages visibly report 2020-08-24 and 2020-08-15 updates.
