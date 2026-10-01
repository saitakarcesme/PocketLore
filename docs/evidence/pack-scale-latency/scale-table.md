# Scale measurements recorded before latency completion

All values are emulator observations. Each transition retains the original 186-passage index and the pinned real model; duplicates do not add factual coverage.

| Passages | Admission | Import ms | Java used-heap delta bytes | Before / after PSS KiB | Sampled peak PSS / RSS / swap KiB |
| ---: | --- | ---: | ---: | --- | --- |
| 186 | accepted | 88.933 | 696320 | 564146 / 565675 | 575611 / 638672 / 25564 |
| 930 | accepted | 397.945 | 3096576 | 564921 / 576150 | 583874 / 659192 / 25692 |
| 3720 | accepted | 1530.898 | 11866112 | 567416 / 597531 | 639295 / 714832 / 25692 |
| 9300 | accepted | 3726.406 | 29159424 | 571556 / 621278 | 700821 / 775648 / 25564 |
| 13764 | accepted | 5511.986 | 42688512 | 575390 / 640456 | 759315 / 833912 / 25564 |
| 13950 | rejected | 36.896 | -147456 | 575367 / 575514 | 575514 / 650832 / 25564 |

Java deltas use requested-GC snapshots while old and new indexes remain live. They include runtime/allocator effects. The negative rejection delta is GC variation, not negative index size. RSS and swap are process-wide; sampled maxima can miss short transients. The baseline source vocabulary remains 1,770 terms, while postings grow from 6,001 to 444,074; these are duplicate-heavy stress results, not vocabulary-diversity scaling.
