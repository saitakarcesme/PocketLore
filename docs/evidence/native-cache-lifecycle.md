# Native owned mapping and cache lifecycle — repair 2

Current status: implementation and linked-build validation in progress; no acceptance claim.

The recovered parent c4615b220665376146690779f97589d52e726302 passed the Android build but failed the canonical lifecycle checker on ARM64 identity. Its checker stopped before collecting the model receipt. Its passing narrative was incorrect. The original canonical packet is preserved unchanged under native-cache-inputs/repair-2/prior-c4615b2-review.json.

This repair removes enclosing Git discovery from both ggml and llama build-info in the isolated derivation. Build identities explicitly name the pinned baseline and the modified derivation digest. The shared pinned checkout remains unchanged. An owned Git fixture reproduced the old metadata dependency and verified stable patched metadata across parent commits and dirty state. This establishes a real mechanism, not proof that metadata explains every historical binary difference.

Evidence collection now loads both raw inputs before validation and archives complete success/failure observations atomically. Actual historical fixture and model receipts were recovered. The historical builder packet was recovered, but its hash differs from the independently reviewed 462630... packet; that exact positive packet remains unavailable.

No new model sample has run yet. Full model loading, prefill and generation are forbidden here. Native controls and linked builds do not establish Android execution, useful answers, a complete 50 GB distribution, physical-device qualification or superiority.
