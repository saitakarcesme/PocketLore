# Refined native UI verification

This lane resumes coordinator-sealed `15c48b43999cb57599c58477668fc73a03748276`. The earlier handoff was rejected for an empty reviewed Git diff and absent Android proof; neither that report nor an internal reviewer establishes independent acceptance. This refinement supplies a nonempty patch with explicit new files, real APK identities and Android execution evidence for coordinator sealing and independent acceptance.

## What is implemented

Research, Library, Places and Saved are separate task destinations. Settings and collection disclosure retain existing setup/recovery controls. A private SQLite notebook records completed results and opened sources; users can search history, bookmark, write notes, remove records with confirmation, compare two real records, and export/share snapshots. Source readers expose source dates and original provenance, persisted reader size and navy/cream themes. A restored research result is explicitly a snapshot; its saved record contains source details. Pack formats, eligibility, rights and answer algorithms are unchanged.

## Execution and evidence

The lane-root `HANDOFF-refined.json` identifies the exact final APK, test APK, patch, files, logs and screenshots. Evidence lives in `../evidence-refined` relative to the repository. The first runtime attempt stalled and captured some transitions too early; its raw log, images and FAIL explanation remain preserved. Later synchronization waits for actual states, and successful passes are tied to their own build identities. Historical screenshots with inaccurate state/theme filenames are not promoted to final evidence.

`RefinedUiInstrumentation` runs on the existing emulator-5562, AOSP API35, 320×640 at 160dpi, using its real installed catalog. It exercises:

- Four destinations, Settings access and Back to Research, keyboard display and real native control dimensions.
- An actual reviewed-pack question after explicitly unloading the model: the engine reports extractive fallback and `invokedModel=false`; completed history is saved. No generated-answer usefulness is claimed.
- Activity recreation with retained question and explicitly labeled result snapshot.
- Actual installed article lookup, long source titles, source date, citation identity and retained generation prohibition.
- Bookmark and note writes, database reopening, Activity restart and persisted reader sizing/themes.
- Comparison of actual saved research/source records, explicitly without new synthesis.
- A real Android document picker Save action, successful output-stream completion, actual exported Markdown, and a read-only sharing provider; no compatible receiving app exists on this AOSP image.

Runs at system font scales 1.0 and 2.0 preserve screenshots and accessibility trees. The prior font setting is restored after testing. Node/control dimension checks are bounded tests, not a TalkBack listening assessment. Some controls are intentionally reached by scrolling; screenshots do not establish every interaction or physical-device acceptance.

Before install, the runner state and emulator activity instrumentation are inspected. The installed APK is preserved and its development signing certificate is matched; only an in-place update is used. No uninstall, device wipe/restart, duplicate emulator or emulator-5560 operation occurs. Small catalog JSON hashes and allocated pack/model directory sizes are compared before/after; this does not rehash 41GB or repeat capacity acceptance. Tests add only bounded notebook/export/evidence files. They do not change active packs or model assets.

## Build and host checks

Installed rig JDK/SDK, existing dependency cache, two Gradle workers, 2GB Gradle heap, offline mode:

```sh
PATH="/home/isa/Android/atlas-toolchain/jdk/bin:$PATH" \
GRADLE_USER_HOME="$PWD/downloads/ui-gradle" \
bash tools/android-build.sh assembleDebug assembleDebugAndroidTest \
  -PpocketloreTestRunner=org.pocketlore.app.RefinedUiInstrumentation \
  -x buildPocketLoreNative -x buildPocketLoreIndex -x buildTravelPack --max-workers=2
```

Native libraries and the small bundled assets are reused with the prior recorded hashes; canonical native source matches were already recorded. No model download or inference. The lane-local original debug key is retained outside Git and the installed app's existing development signer is reused so its data survives update. This is not production signing.

`python3 tools/evaluation/check_ui_scope.py` verifies byte identity of protected engine/import/source-reader classes against the sealed base, no Android permissions, minimum control dimensions and palette contrast. Measured ratios include cream/navy 14.70:1, cream/raised navy 12.15:1, teal/navy 10.35:1, and dark teal/cream 6.44:1. Rendering and contrast are separate checks. `git diff --check` is also required.

## Remaining limits

See `UI-CAPABILITY-GAPS.md` for the completed static audit and remaining competitor gaps. No competitive win is claimed. Notebook snapshots are not ingestible knowledge packs; export is not sync, restore or rights clearance. Notebook limits are 200 records, 2MiB per record and 16MiB of source body/provenance; notes have their own 20,000-character limit. Excess content fails visibly rather than truncating. Full source text remains in installed collections when a preview or notebook limit applies.

Physical Android/GrapheneOS, TalkBack listening, switch access, adaptive tablet panes, sustained performance/thermals and human acceptance remain open. Shared-recipient delivery remains untested because no receiver is installed. Import/recovery transaction algorithms are unchanged and their controls remain reachable; this UI run does not repeat the heavy capacity/import protocol. Result restoration uses a bounded state snapshot and Saved for complete source inspection; unfinished generation is not resumed after process death.

Git could not create checkpoint.git/index.lock because metadata remains mounted read-only. The coordinator must seal the explicitly named final files from the hash manifest, then review that actual commit; the working patch is not a claim of an existing new commit.

## Final installed-identity discrepancy

After the candidate UI runs completed, a final device check found installed APK `1b687b9b3568bfcc72feaad6810b1a65d5730af552d75dbd962183779a8fa23e`, matching the canonical host APK, rather than this lane's delivered `3873ba23b6cda8268ec77ced1362a2e3230751d09f7ae111cfecb1795ece364e`. Manifest, DEX, resources and bulk-review assets differ. The exact installed artifact and package update times are preserved in lane evidence. No attempt was made to overwrite canonical work. Candidate runtime logs/screenshots describe the earlier UI test window; the device's final installed state is not claimed as this UI release. Coordinator-controlled reintegration and an installed identity check remain required.
