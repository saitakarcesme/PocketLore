# Indexed original-wikitext search — unvalidated checkpoint

Task542 adds an exact Unicode-scalar trigram candidate index without duplicated whole source bodies. It preserves accepted541 body-before-title/first-occurrence behavior and explicitly rejects queries shorter than three scalars. The fixed8192-record fixture, five queries and ten trials were frozen before execution.

Initial host measurements showed rare1 vs8192 and absent0 vs8192 decompressions; frequent queries were slower and are retained without tuning. Independent review identified an expired SQLite progress callback, incomplete derivation binding and missing exact mutation coverage checks. These are being repaired before the sole256-page derivation. This checkpoint is not accepted and has not read the original archive or any model/device data.
