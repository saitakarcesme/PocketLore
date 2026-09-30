# PocketLore

PocketLore is an early open-source Android project for useful offline research: explanations, comparisons and synthesis with inspectable local sources.

**Status: first extractive Android prototype; native generation is the next milestone.** It is not a bounty-ready release. No physical Android or GrapheneOS device is attached, no competitive advantage has been demonstrated, and desktop/emulator results cannot establish phone performance.

The target is a reproducible installation on compatible Android/GrapheneOS hardware with at most 12 GB device RAM and 50 GB total installed assets, no research-time networking and no core Google Play Services requirement. Models, indexes and source packs will have explicit provenance and licenses.

See [goals and release gates](docs/GOALS.md), [research interpretation](docs/RESEARCH.md), [findings](FINDINGS.md) and [third-party notices](THIRD_PARTY_NOTICES). See [Android build and installation](docs/ANDROID.md), [runtime plan](docs/RUNTIME.md), [frozen evaluation protocol](docs/EVALUATION.md), and [remaining release gaps](docs/RELEASE_GAPS.md). The starter library contains eight hash-pinned USGS water-science passages acquired during build setup; the app searches and displays them offline with source inspection. This is retrieved evidence, not yet generated synthesis. Large assets and private coordination archives are deliberately excluded from this repository.

Licensed under Apache-2.0; independently licensed data and dependencies retain their own terms.
