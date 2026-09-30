# Goals and release gates

PocketLore targets [bounty 31](https://poidh.xyz/mainnet/bounty/31). The provided September 30, 2026 bounty snapshot is the bootstrap requirements input; it is not a guarantee of current judging or payment.

| Gate | Required evidence | Bootstrap state |
| --- | --- | --- |
| Useful research | Explanation, comparison, synthesis and reasoning on frozen unseen questions; supported claims and useful abstention | Open |
| Android installation | Reproducible APK, asset manifests and clean installation on physical compatible hardware | Open |
| GrapheneOS | Actual compatible-device installation and offline exercise | Waiting for hardware |
| Resource limits | <=12 GB device environment; <=50 GB APK, models, indexes, data, caches and temporary installation footprint | Open |
| Offline use | No remote inference, API, search or network requests during research; no core Play Services | Open |
| Usable speed | Cold/warm first token, first useful content, complete answer, p50/p95, thermal and long-session measurements | Open |
| Honest comparison | Exact versioned artifacts, same questions and conditions, named frontier+web baseline, raw answers and blind review | Open |
| Public delivery | Source, dependency/model/data licenses, pinned hashes, installation and demo instructions | In progress |

The ambition is to outperform submitted rivals in quality, speed, reliability, coverage and installation. It is an objective, not an established result. A score ratio, correctness rate and preference rate are different measures. The bounty's greater-than-half bar has no locally invented official interpretation.

## Sequence

Baseline; durable runner and separate roles; frozen English development/holdout evaluation; runnable Android slice; model/runtime measurements; real knowledge packs; retrieval quality; supported synthesis; travel and deterministic tools; phone resource improvements; clean installation and offline audits; comparable evaluation; release and demo preparation.

Every phase is split into evidence-producing tasks, with early product code. Waiting for hardware does not block independent implementation or host checks. A human user must supply actual device access and any final external submission decisions; they must never be fabricated.
