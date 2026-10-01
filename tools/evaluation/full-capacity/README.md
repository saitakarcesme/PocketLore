# Full simultaneous capacity experiment

Run on LLMRig with the dedicated coordinator-managed emulator-5562 already booted. Do not start, resize or stop emulator services. Never use emulator-5560 for this experiment.

1. `bash tools/android-build.sh assembleDebug assembleDebugAndroidTest -PpocketloreTestRunner=org.pocketlore.app.FullCapacityInstrumentation`
2. `python3 tools/evaluation/full-capacity/run.py`
3. `python3 tools/evaluation/full-capacity/ui.py`
4. `python3 tools/evaluation/full-capacity/freeze.py`
5. `bash tools/evaluation/check_full_scale_android_capacity.sh`.

The run consumes the task300 sealed lane paths and task301 frozen manifests. It rehashes immutable source assets, incrementally imports all shards through `ScaleLibrary.install`, and keeps all prior shards resident. One incoming ZIP is recreated in ignored `downloads/full-capacity`; local ADB streams it into an app-owned FIFO. There is no research network or inference. `capacity-aux` holds declared OSM/Wikivoyage inventory for storage accounting, without claiming integrated Android readers. The actual small-pack library remains independently imported through `PackLibrary.install`.

Existing successful result directories are resumed, never silently overwritten. If a step fails, preserve that directory and its transport/log evidence before a corrected attempt; reconcile the actual catalog before retrying. The runner must not be used on arbitrary user app data: emulator-5562 is the isolated task303 fixture environment.

The replacement changes only SQLite `user_version` and appends one unused byte to the block container of largest wiki shard000_00003. These transformed artifacts are representation-only storage fixtures; all article text, record hashes, offsets, provenance and rights remain original. The inverse transaction restores original sealed bytes. No duplicated passages or new facts are counted.

Measurements: per-import precommit logical files includes old and new objects simultaneously; 250ms instrumentation samples report app logical/allocated storage and PSS, while 1s host sampling records complete `/data` usage. Timed sampling is not an instantaneous allocator high-water mark. Product APK and test APK bytes are reported separately; no loaded-model memory or phone/thermal claim follows. A provider archive copy is a separate conservative budget, not part of the observed FIFO path.

The acceptance verifier rejects cumulative-count loss, missing simultaneous sealed hashes, missing actual source reads, failed rollback/selection restart and absent full-size changed-object replacement. It also exercises changed/missing model/run artifacts and semantic count/peak regressions. Passing capacity does not certify source rights, unique venues, live availability, generated support or competitive quality.
