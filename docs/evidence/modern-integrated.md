# Modern integrated Android compatibility — strategy-change result

**Build passes; the required fresh integrated API37 check fails.** The materially different device-owned transaction now preserves complete UI evidence and restores font before teardown, but an actual emulator reboot interrupts the cold-restart phase. This is a negative, bounded result, not completion or acceptance.

Design, failures and discriminating checks: [strategy-change report](400-modern-integrated-android-compatibility-strategy-change.md). Earlier successful builder reports remain historical; the latest failed canonical invocation `20261002T023803Z-96ed2e58` is preserved under [strategy evidence](modern-integrated/strategy/), including its actual offline collection/restoration failures.

## Changed design and actual fresh execution

Test-only DeviceEvidence executes original-font restoration while instrumentation remains active, then emits32KiB evidence chunks and an exact SHA256/byte manifest through instrumentation status before finish. The host admits only flat bounded evidence files, rejects missing/duplicate/corrupt/stale chunks and requires successful transport, source report and manifest identity. Post-finish per-file/archive extraction is removed. Production application/runtime/model/answer policy is unchanged.

The required `bash tools/android-build.sh` passes; the compiled APK remains22,702,878 bytes, SHA256 `9c71a32dbc2deac3d650c6849a335379bd2b005c1516437c613bcd0fcff7dd70`. Current ELF LOAD/RELRO/ZIP16KB receipts are retained. Six host tests pass, including exact historical transport failure and new actual-report stream mutations. The fresh required `bash tools/evaluation/check_modern_integrated.sh` fails; the later source-snapshot/offline-probe verification additions do not change that result or authorize another replay.

Fresh run: `downloads/modern-integrated/20261002T024449Z-ae7daa88`. Exact executed checker source is retained as `strategy/executed-check.py`; future runs capture their source on entry. Full raw status streams contain encoded screenshots and remain in that ignored run directory, SHA/size pinned by committed `retained-files.json`. Decoded JSON/text reports, transport exit/timing metadata, and exact non-chunk status lines are committed. No source/model/APK binary payload is committed.

- No-UI and UiAutomation activity/screenshot teardown probes each pass with unchanged boot identity. They do not reproduce or diagnose the later failure.
- Default and200% font UI each pass108 actual checks: keyboard/Back/edit/recreation, model-unloaded result, source/Notebook/notes/bookmarks, SAF export/cancellation/retry and lifecycle. Both restore original1.0 inside instrumentation before emitting evidence. Blocked export cancellation70ms/131ms.
- Cold-restart instrumentation returns255 after23.088 seconds. Subsequent font readback command encounters an offline device. The entire run fails; no recovered PASS can replace it.
- Documents, cold documents, resident native recovery and final same-boot identity/retention checks were not reached. Earlier repair1/2 reports do not satisfy them.

The tested system is emulator-5564 Android17/API37 x86_64 with16384-byte pages. No physical device or full corpus is represented. Before boot ID: `8795d7d4-66d0-4c6f-b771-6762214d26b6`. After the device returned: `75d5e110-b22d-431e-af27-b0bb96f6c109`. This proves a guest reboot during/after the failing boundary. A later read-only observation confirms font1.0 and the original APK/model hashes, but those observations cross the reboot and cannot satisfy same-run retention. The builder did not restart/wipe/uninstall/clear data or modify services.

## Diagnosis, external dependency and preserved limits

The emulator crash buffer contains repeated UWB HAL startup aborts for missing/dev/uwb0 and no system-server crash entry. Those observations do not identify the cause of this reboot and do not justify changing unrelated services. No OOM, GPU or timeout cause is claimed.

Required next action: coordinator diagnosis/stabilization of the existing5564 emulator/guest restart boundary, without builder service/configuration changes or disturbance of5560/5562/protected inference. Once the environment remains stable, the full declared check must pass with unchanged boot ID, original font, all six fresh phases and exact final identities. The checker remains honestly failing until then; no further identical suite retries were run.

Current subset baseline raw logical/allocated storage and asset identities are preserved, but a complete current post-run budget/retention snapshot is not established. Prior303/390 full inventory and prior API35/37 passes are not transplanted. Model/corpus/optional assets were not downloaded or expanded; no generation, research inference, global preference, private holdout, orchestration/main or publication change occurred. Gradle remains configured2workers/2GiB, not measured total peak.

Present-asset recognition, full-capacity API37, physical ARM64 Android/GrapheneOS, TalkBack/human acceptance, sustained stability, unseen answer quality, source rights and external release remain open. Source quotations remain labeled extractive and do not establish generated answer quality. Independent criticism of this frozen negative result is recorded separately; no acceptance is claimed.
