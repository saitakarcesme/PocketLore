# Resource policy and recovery

PocketLore uses one resident native session, one request context and one sequence per process. Closing during an active call cancels it; the resident lease remains held until that call returns and finishes context and model destruction. A second session is rejected while that lease is live. Each request has a fresh 2,048-token context, a 256-token output cap, a 2,048-token batch and a 128-token microbatch, using two CPU threads and FP16 K/V storage. Context and sampler memory are freed on success, failure and cancellation; no persistent prompt/KV cache is written.

A model file must be regular and at most 2,048 MiB. The pinned llama.cpp memory breakdown additionally rejects a context before decoding if model buffers exceed 2 GiB, context/KV buffers exceed 768 MiB or compute buffers exceed 1 GiB. **This check runs after context allocation.** It cannot prevent a malicious/unsupported GGUF or allocation-time OS kill, and the file-size limit alone does not prove arbitrary-model RAM safety. Native diagnostic counters report live lease/context counts and active buffer allocations; they are not process memory totals. Memory accounting uses an internal API from the exact immutable runtime pin, so a future revision requires review.

On Android memory-pressure callbacks, PocketLore cancels the current native operation, discards unverified answer text and queues model release behind the operation. Saved model/source files remain. The user can choose **Reload saved model**, or **Unload model to free memory** manually. A failed Java allocation in model import or generation releases resources and reports failure instead of publishing a partial draft. Android may kill a process without callbacks; reloading after restart is still necessary, and this policy does not establish survival of true system OOM.

Model staging is serialized across Activity recreation. Pack import runs on a separate shared serial worker and installation is synchronized. Pack data is streamed to a bounded stage, then verified/indexed before atomic replacement. This avoids the former additional full archive copy. Cancel pack import or memory pressure cancels the copy and prevents promotion; validation also responds to thread interruption. A blocked document-provider read may delay cancellation. Free storage must cover the model's declared size, or the pack's conservative 16 MiB maximum, plus **256 MiB** reserve. Existing originals remain at their provider; old installed and new staged copies coexist until promotion.

Only `model.partial` and `pack-[digits].partial` in app files are eligible for orphan cleanup, on the corresponding serialized worker. Installed files, unrelated partial files, research data and system-managed caches are retained. Stage files are deleted in failure/finally paths, including the tested injected Java allocation failure. No arbitrary cache-directory deletion occurs. The application writes no persistent index or inference cache; Android-managed code/cache storage remains part of disk accounting.

The intended <=12 decimal GB device allocation and conservative <50 GB disk plan are specified in [measured evidence](evidence/resources.md). They are engineering budgets, not physical acceptance. The tested emulator is approximately 2.59 GB and swaps; rig host memory is reported separately. Normalized/synthetic resource-control tests do not replace physical pressure, thermal, long-session, large-pack or diverse-model measurements.

## Reproduce

Provision the documented pinned runtime/toolchain, pack and travel source caches first. The existing isolated emulator must be booted. The resource check reuses the pinned Qwen3 model and reference pack in `files/synthesis-tests/` from the synthesis setup, and a saved app model in `files/model.gguf` from answer integration. It verifies the Qwen3 and pack hashes before testing. It does not download, replace the user's model, start an emulator or alter services.

```sh
bash tools/android-build.sh
bash tools/evaluation/check_resources.sh
```

The resource test makes one full temporary copy of the 1.83 GB model in an isolated app test directory; at least its size plus 256 MiB of free device storage is required. It removes that stage and preserves installed files. Small labeled test sentinels and raw reports remain as evidence. Outputs are under ignored `downloads/resources/run-*`. The script fails for missing dependencies, failed behavior assertions or JNI errors and preserves available outputs. Runtime generation here is a resource workload, not an evaluation of citation support or answer quality.
