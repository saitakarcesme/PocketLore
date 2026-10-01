# PocketLore

PocketLore is an experimental Android application for offline research with inspectable local sources. It includes CPU llama.cpp inference, retrieval, citation-linked answers, explicit abstention and extractive fallback, local model/pack import, and a small offline travel slice.

**Status: development debug candidate, not an accepted product or bounty submission.** Both build and release checks pass for the measured emulator candidate, including identical APK bytes across forced rebuilds on the rig. Independent clean-machine reproduction remains open. Real emulator runs expose incomplete answers, unnecessary abstention and withheld drafts. No physical Android or GrapheneOS device has been measured, independent quality review remains open, and no competitive advantage has been established.

Start with the [build, installation and live demo guide](docs/RELEASE.md), [candidate evidence and exact artifacts](docs/evidence/release-preparation.md), and [unresolved release gates](docs/RELEASE_GAPS.md). The app has no requested permissions or core Google Play Services dependency. Models and the larger pack are acquired separately before offline use.

The reference pack contains 186 licensed English passages covering selected science, historical documents, practical outdoor reference and US travel; the bundled travel catalog contains three DC monuments. Coverage is limited. Opening hours can be stale, routing is unavailable, and source URLs do not establish live conditions. Generated citations are inspectable but do not guarantee factual support.

The target is compatible Android/GrapheneOS hardware with at most 12 GB RAM and 50 GB installed assets. Host/emulator diagnostics are not phone acceptance. See [goals](docs/GOALS.md), [findings](FINDINGS.md), [comparison evidence](docs/evidence/comparison.md), [resource evidence](docs/evidence/resources.md), and [third-party notices](THIRD_PARTY_NOTICES).

Licensed under Apache-2.0; dependency, model and data licenses retain their own terms. Model weights, bulk data, build binaries and private evaluation/coordination archives are excluded from Git.
