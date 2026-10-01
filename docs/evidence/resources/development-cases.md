# Resource development cases — frozen before implementation

- Keep the existing 2,048-token context and 256-token output caps; reject over-budget input before context creation. Prevent overlapping resident native sessions, including a session closing during active generation.
- Load a real pinned model on the existing emulator, generate real tokens, cancel an active generation and reuse or reload successfully. Sample process PSS and Java/native heap through load, inference and unload; label sampling and emulator limitations.
- Deliver low-memory/trim callbacks to the actual Android controller; discard unverified output, release the model after cancellation and keep the saved file. Explicit reload recovers; never pretend an injected callback proves survival of a real OS kill.
- Reject insufficient storage before import; preserve old installed model/pack on failure or cancellation. Clean only recognized abandoned import stages on restart, without deleting installed assets or unrelated files.
- Enforce one serialized pack import and a bounded staged copy with free-space reserve. Exercise mid-copy cancellation and Java allocation failure cleanup; simulated failures are control tests, not actual exhausted-device measurements.
- Record APK, native libraries, model, packs, index representation, persistent cache, staging/temporary footprint, source copies, test fixtures and available host/emulator memory separately. Account for overlapping old/new/source model copies.
- Define a conservative <=12 decimal GB device design allocation; do not assert physical acceptance or a measured worst-case peak from host/emulator snapshots.
