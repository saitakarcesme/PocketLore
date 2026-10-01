# Android scale UX development freeze

Frozen before implementation, 2026-10-01. Scope: isolated Android source and documentation; host checks and compilation only. No holdout, GPU, emulator or physical acceptance.

1. Setup explains local-only acquisition, retained original files, storage reserve and unknown rights; unsupported bulk schemas are rejected without conversion.
2. Known-size model imports reject unknown, truncated, oversized and cancelled inputs; preserve the 2 GiB ceiling and 256 MiB reserve.
3. Compatibility shows current native context/KV/compute/OS limits; 4B, 7–8B and MoE remain unadmitted without exact model/device/profile measurements.
4. Collection selection remains atomic; removal requires naming the edition and explicit confirmation; cancellation changes nothing; removed archives cannot resurrect through legacy migration.
5. Interrupted import state survives process death and explains restart-from-source recovery; installed assets remain usable; only owned partial files are cleaned.
6. Pack preflight shows exact known archive bytes, reserve and checksum identity semantics; database expansion has a separate reserve check.
7. Source inspection remains selectable/scrollable at large font, preserves mathematical Unicode, dates, rights, provenance and citation IDs; unknown metadata is labeled unknown.
8. Search failure restores controls with a readable status; answer labels never conflate retrieval/fallback with generated synthesis.
9. Large existing prebuilt editions use the current bounded SQLite reader; no whole-corpus load or invented compatibility with another lane's schema.

Queued emulator cases: SAF model/pack import and cancellation; process kill during copy and validation followed by restart; remove/cancel/restart/empty library; disk-full and truncated-provider rejection; source scroll at 200% font with math/date/unknown rights; absent/generated/fallback/cancel states; memory-pressure unload; profile rejection above 2 GiB. Coordinator must schedule a device other than reserved emulator-5560 or release that reservation.
