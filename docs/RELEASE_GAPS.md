# Release gaps

This list distinguishes achievable rig work from actual external dependencies. It is not a completion claim.

| Gap | Next evidence | Dependency |
| --- | --- | --- |
| Native inference in Android | CPU ARM64/x86_64 builds, 23 JNI behavior checks and real SAF import/restart/recreation checks recorded; ARM64 execution and physical acceptance remain open | Existing supervised emulator restored through adb; no current KVM blocker. See [answer evidence](evidence/answer-integration.md) |
| Supported generated research | Main answer flow now generates a cited answer, rejects uncited drafts into labeled fallback, and abstains on missing coverage. The development comparison is incomplete; citation integrity is not semantic support or useful-research acceptance | Better model/answer quality, semantic source review, frozen quality evaluation and broader packs |
| Knowledge coverage | 186 real English passages from 10 documents, deterministic build, provenance/hashes and transactional import implemented; emulator corruption/restart/source UI checks recorded | US/history-heavy sample; broader geographic/scientific coverage, quality evaluation and physical import/resource tests remain open. See [pack evidence](evidence/knowledge-pack.md) |
| Retrieval quality | Frozen 30-case development evaluation, raw baseline/candidate results, inverted index and 38-query host/emulator parity now recorded | Independent relevance review, unseen evaluation and larger-corpus scaling remain open; two explicit distractors and 17/20 supported-query generation blocks remain. See [retrieval evidence](evidence/retrieval.md) |
| Travel and tools | Locality/diet constraints, deterministic calculation, stale-data handling | Licensed travel pack and implementation |
| Resource and offline audit | Whole-install accounting, import recovery, no research network checks | Rig checks first; physical confirmation later |
| Comparable quality | Frozen exact artifacts, named frontier+web raw references, blind scoring | Evaluation implementation; no fabricated provider access |
| Physical Android acceptance | Clean install, cold/warm latency, peak RAM, total storage, sustained use | Compatible physical device not attached |
| GrapheneOS acceptance | Actual compatible hardware install and offline exercise | Compatible physical device not attached |
| Human evaluation and public demo | Independent review and truthful real-device recordings | Human/device access; publication is separate from code pushes |

The initial 16-question local-model pilot is a structural evaluation scaffold, not verified factual gold. Holdout is private and must remain unseen by implementation workers. No bounty submission or superiority claim is justified at bootstrap.
