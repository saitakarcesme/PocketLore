# Primary documentation review

Pinned AndroidLM README: commit `5abca020a65dea01a04d52131943e440a5e6f5cf`, https://github.com/Phineas1500/AndroidLM/tree/5abca020a65dea01a04d52131943e440a5e6f5cf. Its documented design suggests separating full articles from leads by bulk pageviews and keeping term counts on disk. These are design ideas, not measured PocketLore results or a superiority comparison.

Pinned BOAR KNOWLEDGE_PACKS: commit `6b53ee8398510fdc2b90e5db27c5a20d3e4406f9`, https://github.com/rferrari/boar-app/blob/6b53ee8398510fdc2b90e5db27c5a20d3e4406f9/docs/KNOWLEDGE_PACKS.md. Its documented pack manifests, resumable acquisition and bounded retrieval candidates inform the contracts here. Its per-article API and per-chunk embedding approach is unsuitable for this assigned bulk scope. No rival implementation is copied.

FineWiki's pinned card says its source is the August 2025 Wikimedia Enterprise snapshot, its processed release is CC BY-SA 4.0, and its extractor removes references/notes and disambiguations/redirects. The release therefore cannot supply an authoritative redirect table alone. The stored wikitext is required for inspecting formulas, templates and source-specific attribution removed from rendered text. Dataset licensing does not settle every embedded third-party notice.

One generic requests User-Agent received HTTP 403 on a Wikimedia directory probe; the actual monthly file succeeded with the descriptive project User-Agent and a range request. The failure body and successful source headers are preserved. Monthly pageviews are dated 2025-08, observed Last-Modified 2025-10-07; the final receipt pins acquired bytes by SHA-256, not an invented upstream hash.
