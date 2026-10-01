# PocketLore native product direction — refinement

Base: coordinator-sealed `15c48b43999cb57599c58477668fc73a03748276`. The installed baseline screenshot shows a form of development controls and clipped content, not an accepted product experience. Earlier compilation and host assertions did not establish Android usability; the original critic rejected that missing proof. This direction precedes refinement code.

## Task-first structure

Four named destinations: Research, Library, Places, Saved. Each destination has a short heading, explicit Offline status and a scrollable content area. Compact navigation uses two rows when text or width needs it, with a selected label rather than color alone. Settings is a secondary action. Model, import, storage, removal and compatibility controls live behind settings/disclosure, not above the question. Back closes a reader or settings before leaving the task. Question drafts and destination survive recreation.

Research presents a real question input, the existing answer action, cancellation while busy, truthful answer status, source excerpts, and actions to save or compare actual retrieved evidence. No template answers or simulated progress. Completed results are captured with their question, actual result label and inspectable source metadata in a private local notebook; unfinished or cancelled drafts are not presented as completed answers. Source-only browsing remains separate from generation eligibility.

Library searches installed Knowledge collections. Places opens the real city/category/radius search directly and retains absent-hours, routing and coverage labels. No map is implied by stored coordinates. Regional tools remain available as a secondary task. Installed collection metadata is displayed without promoting staged host counts to device coverage.

Saved is a searchable history/bookmark list, with real persistent records, notes and deletion confirmation. Opening a record shows its capture time, source date as supplied (or Unknown), source/edition provenance, and an explicit snapshot label. A full-screen source reader has persisted font size (18/22/26sp) and navy/cream reading themes. It uses scrollable full titles, selectable source text, bookmark, note, export and share actions. A two-item comparison shows the actual saved questions/results/source details sequentially on compact screens; it makes no new factual judgment or inference. Empty selection cannot create a comparison.

Notebook storage is app-private and separate from pack formats. Bounded SQLite transactions preserve records across process death and reject excessive snapshots instead of silently truncating. Export creates portable UTF-8 Markdown through Android ACTION_CREATE_DOCUMENT; share uses a temporary read-granted content URI and system chooser. Export retains result labels, dates, provenance, limitations and user notes; it does not upgrade rights or answer support. No broad storage/network permission or GMS dependency. Provider/IO failure remains visible and export cancellation is harmless.

## Primary documentation studied

- [Android core app quality](https://developer.android.com/docs/quality-guidelines/core-app-quality): preserve task state and Back behavior, readable composition, 48dp targets, contrast, system sharesheet and internal sensitive-data storage. Local policy keeps offline/noGMS and no automatic cloud backup despite optional online platform guidance.
- [Android Views accessibility](https://developer.android.com/guide/topics/ui/accessibility/views/apps-views): 48×48dp focusable controls, meaningful distinct control labels, natural TextView announcements and persistent input labels.
- [Material canonical examples](https://m3.material.io/foundations/layout/canonical-examples/overview): list/detail and supporting content relationships, rather than a single settings form. Its JavaScript-only page was corroborated with [Android's primary canonical Views guidance](https://developer.android.com/develop/ui/views/layout/canonical-layouts): compact lists open details and Back returns to the list. Full adaptive tablet split panes remain a gap.
- [Apple typography](https://developer.apple.com/design/human-interface-guidelines/typography), read through Apple's [documentation JSON](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/typography.json): system fonts, restrained weight hierarchy and proportionate accessible scaling. Apple point sizes are not treated as Android dp/sp rules.

## Concrete rules and measurement

Use platform sans serif; regular body at 18sp (no body below 16sp), medium headings 24–28sp, visible labels 16sp. Text scales with Android settings. No fixed-height content cards or single-line result titles. All interactive controls have minimum 48dp width and height; scroll content remains reachable with keyboard and system insets. Navy #101D2B and raised #1B2D3E use cream #F4EEDD and teal #83D9CC. The light reader reverses cream/navy and uses dark teal #175F58. Measure contrast from actual sRGB values and record results, rather than asserting theme compliance from appearance. Validate long titles, 200% text, small display, keyboard, selected navigation and accessibility node bounds on the APK when device access is safe.

## Evidence and release boundary

Compile with installed rig SDK/cache, bounded workers and reused pinned native libraries; preserve old APKs and logs. No inference or corpus changes. emulator-5562 may be used only after canonical activity/runner checks show no conflicting test; never touch emulator-5560, erase data, restart devices or create another emulator. Preserve the existing approximately 41GB catalog and signing identity. Capture real screenshots/accessibility trees and run persistence/export/source-flow tests; if blocked, record the exact cause and leave integration unaccepted.

The competitor-feature audit lane was still running at initial inspection; its final handoff arrived before freeze and its artifact/source hashes were verified. See UI-CAPABILITY-GAPS.md for the 63-capability reconciliation. This finite refinement is not a claim of all competitor capabilities or competitive superiority. Physical Android/GrapheneOS, source rights, useful synthesis, offline coverage completeness and human acceptance remain separate gates.
