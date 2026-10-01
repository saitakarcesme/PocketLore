# PocketLore

PocketLore is an experimental Android application for offline research with inspectable local sources. It includes CPU llama.cpp inference, retrieval, citation-linked answers, explicit abstention and extractive fallback, local model/pack import, and a small offline travel slice.

**Status: development integration milestone; final release freeze is deferred.** The latest APK builds reproducibly on the rig, but the release check fails against the preserved release-v4 identity. The approved scale replan requires chosen-model, bulk-data and Android integration before a new final freeze. The production model is still Qwen2.5 0.5B; Qwen3 4B remains a host candidate. Physical Android/GrapheneOS, independent unseen quality and human acceptance remain open.

See the [current identity audit and deferred release work](docs/evidence/broad-candidate-release.md), [scale integration evidence](docs/evidence/scale-integration.md), [historical installation/demo guide](docs/RELEASE.md), and [release gaps](docs/RELEASE_GAPS.md). The application requests no permissions or core Google Play Services dependency. Assets are acquired separately before offline use.

The emulator retains reference, science and the reviewed broad edition together: 1,113 distinct documents and 40,891 passages. Separate browse-only scale collections contain the first complete wiki shard (413,151 articles, including 82,022 full articles) and 5,120,674 place source records with city lookup. These installed milestones are not the full host-staged inventory or evidence of useful generated answers. Bulk source rights and support gates remain unresolved. The bundled travel catalog has 25 central DC POIs; hours may be stale and routing is unavailable. Generated citations do not by themselves establish factual support.

The target is compatible Android/GrapheneOS hardware with at most 12 GB RAM and 50 GB installed assets. Host/emulator diagnostics are not phone acceptance. See [goals](docs/GOALS.md), [findings](FINDINGS.md), [comparison evidence](docs/evidence/comparison.md), [resource evidence](docs/evidence/resources.md), and [third-party notices](THIRD_PARTY_NOTICES).

Licensed under Apache-2.0; dependency, model and data licenses retain their own terms. Model weights, bulk data, build binaries and private evaluation/coordination archives are excluded from Git.
