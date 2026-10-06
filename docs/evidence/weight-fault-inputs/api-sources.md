# Primary API basis

- https://man7.org/linux/man-pages/man2/madvise.2.html — MADV_RANDOM advises random page references; advice success alone is not measured cache behavior. DONTNEED may reduce mapping RSS without immediate shared page-cache release.
- https://man7.org/linux/man-pages/man2/posix_fadvise.2.html — Linux RANDOM disables file readahead for that open handle; separate open handles are unaffected. Duplicated descriptors require care because they share an open-file description.
- https://www.kernel.org/doc/html/latest/core-api/mm-api.html — readahead populates page cache before explicit demand and may be triggered by reads or faults; filesystem and prior cache state influence it.

These host API descriptions do not establish Android runtime support, model behavior, a sole cause for task534 cache pressure, or a performance guarantee. The synthetic plan is frozen before measurements.
