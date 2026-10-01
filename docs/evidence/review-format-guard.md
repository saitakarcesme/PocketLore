# Review format guard repair

Task `007-review-format-guard`, LLMRig, 2026-10-01, Python 3.14.7. This is a narrow repository format-validation repair, not application or release acceptance.

## Preserved canonical verdict

The explicitly authorized `100-release-preparation/critic-result.json` was read without modification. Its visible result is one 32-word English sentence containing `classes2.dex`. The former `[^.!?]+[.!?]` pattern rejected that filename dot. The original verdict's SHA-256 before and after inspection remains `a577fad436694ea486eb9ac9123839774e50b4ef7bf97d51c88d698a6a4a4ad1`. The exact sentence is a regression fixture in `test_protocol.py`; the canonical file itself was not copied over or rewritten.

The historical failed release-identity check independently justified rework. Fixing the format guard does not reinterpret the verdict, reverse that failure, or establish acceptance of any candidate.

## Bounded behavior

The guard still requires a recognized decision, a string with no outer whitespace, at most 35 whitespace-delimited words, no line/whitespace separators other than spaces, and exactly one terminal ASCII sentence mark. It allows internal dots only in complete technical tokens: digit-separated decimal/version numbers (optionally prefixed with v) and filenames with explicitly recognized source/artifact extensions. Common filename wrappers such as backticks, parentheses and commas are supported. Internal sentence punctuation elsewhere is rejected, including glued uppercase and lowercase second sentences.

Malformed non-object verdicts and non-string visible results return false rather than raising. Existing English anchor-word checks remain; non-ASCII alphabetic characters are rejected, extending the former Turkish-letter exclusion to other scripts. Typographic punctuation such as an em dash remains allowed.

This is deliberately conservative format validation, not linguistic classification or proof of English fluency. Unknown filename suffixes, ordinary dotted abbreviations, accented English names and some valid technical spellings can be rejected. ASCII non-English text sharing an English anchor word can still evade the inherited heuristic. A token that exactly resembles an allowed filename/version is interpreted as such; the guard cannot infer the author's semantic intent. No automatic language model, network service or alternate critic was introduced.

## Actual regression results

The new tests were run against the unchanged guard first: 18 tests ran in 0.087 seconds, with 7 failures and 5 errors. The positive technical-dot fixtures failed, malformed top-level values raised, and the mixed-script fixture exposed the limited prior language filter. These failures preceded the code repair.

After repair, the exact acceptance command returned exit code 0:

```sh
python3 -m unittest discover -s tools/orchestration -p 'test_*.py'
```

```text
..................
----------------------------------------------------------------------
Ran 18 tests in 0.083s

OK
```

Coverage includes the exact 32-word canonical sentence; `classes2.dex`, paths, compound filenames and archive extensions; decimal 0.5 and versions 8.9.2/v1.2.3; typographic punctuation; genuine spaced/glued boundaries using periods, exclamation marks and question marks; ellipses and repeated punctuation; malformed tokens and values; line/control separators; outer whitespace; the existing exact 35-word boundary and rejected longer text; Turkish, French-without-English-anchors and mixed-script rejection. All existing invocation, repair-chain, recovery and canonical-role tests also pass.

A direct read-only call on the canonical JSON now returns true with the word count and original digest unchanged. `git diff --check` passes.

Source SHA-256:

- `tools/orchestration/protocol.py`: `475a9d53f3044c7b06e3bf3664862450fb7d74a3443a24a667d63097ca7d2b18`
- `tools/orchestration/test_protocol.py`: `5f4aff6ae025cf9f53ecfc5f9de30aa7c6c5514aa7c6dd712b123e5815da1b23`

## Deployment and acceptance limits

Only the two scoped Python files, this report and FINDINGS were edited. Application files, product tests, private canonical evidence, services, runner state and role configuration were unchanged. No private holdout, credentials or other private logs were read. Nothing was pushed and main was not advanced.

The normal runner must obtain canonical criticism of the immutable checkpoint. Host coordination deploys the accepted pinned protocol later; this task does not deploy it or claim independent maintenance acceptance. Product and physical-device gates are unchanged.
