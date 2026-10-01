# Full-scale Android capacity validation (task 303)

Status: protocol frozen; measurement pending. This is emulator capacity and reader validation, not physical-device, source-rights or generated-answer acceptance.

Recovered the useful task301 implementation through preserved checkpoint `49117a8926f299780eec7ce922ff92f16eaa123f` onto the existing checkpoint branch. Main at inspection was `0e09794`. Earlier 6.23 GB emulator failures and the rolling sweep remain historical evidence; they cannot satisfy simultaneous residency.

## Frozen measurement protocol

Use only isolated `emulator-5562`, AOSP API35 x86_64, nominal 4 GB RAM/two cores. Record boot fingerprint, boot completion, actual memory and `/data` capacity. Leave emulator-5560 and services untouched. Install the rebuilt APK, pinned production 0.5B model, three reviewed reference/science/broad editions, all fifteen wiki and sixteen places primary shards, shared aliases/cities/notices once, and the declared auxiliary OSM/Wikivoyage assets. Auxiliary residency does not imply an implemented reader. No downloads or inference.

Import cumulative version2 collections through the production shared-object transaction using bounded local ADB/FIFO transport; never retire old shards to fit. Hash sealed host inputs and installed objects. Keep all thirty-one shards resident during combined exact-title/redirect, twenty-city/category/spatial and absent-category checks from the existing frozen task301 protocol, source reads and restart. Preserve generation-denied rights flags. Exercise active selection persistence and cancelled/corrupt update rollback against the full resident catalog.

For an actual new-object atomic replacement, use the largest wiki shard (000_00003): a copy of its SQLite database with only the user_version header changed and its block container with one unused trailing newline. This explicitly labeled representation-only stress fixture changes no source records, formulas, rights or article offsets. It is not a new corpus edition or factual coverage. Replace both large objects together, preserving the original source inventory and recording transformed hashes. Measure precommit old+new residency, continuously sampled app logical/allocated bytes, device df and process memory. Restore the sealed original representation afterward, measuring the reverse transaction too. No full host corpus duplicate is made; at most one bounded delta archive and replacement shard copies are used.

Report installed app/assets/cache and maximum update footprint in decimal bytes against 45,000,000,000 target and 50,000,000,000 hard cap. The measured FIFO path avoids a provider archive copy; separately report the conservative additional provider-copy budget and do not call that an observed peak. Instrumentation captures a precommit point while old and new objects coexist; timed samples alone may miss instantaneous maxima. APK/test APK and Android runtime overhead are separated. Cold restart means app process restart, not emulator restart.

Acceptance must require whole simultaneous inventory hashes, actual full readers, rollback/restart, representative changed-object replacement and measured storage limits. Missing/changed artifacts must fail. A capacity pass cannot certify unique real venues, unreviewed rights, useful model answers, phone performance or human acceptance.
