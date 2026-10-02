# Optional Ethereum technical collection

On LLMRig, run `python3 tools/packs/specialist/build.py --download` once to acquire only the pinned primary Markdown and license files into ignored `downloads/specialist/raw`. Later builds use those verified bytes without network. The output is `downloads/specialist/ethereum-technical.plpack` (194,793 bytes). Import it using PocketLore's existing Library import control and choose active collections. Research-time networking is not added.

The edition contains eight full dated EIP/ERC documents, 64 sections, and source/rights metadata. Search examples are in `tools/evaluation/specialist/protocol.json`. The source reader shows literal Markdown rather than executing code or rendering remote references. LF is stored as Unicode line separator and tabs as the visible tab symbol; this is reversible, and original UTF-16 ranges and span hashes appear in inspections. Offline legal text accompanies each source.

`bash tools/evaluation/check_specialist_collections.sh` rebuilds twice, verifies exact original roundtrips and changed/missing-source failures, then installs and tests the edition on existing emulator-5562. It leaves the useful edition installed and active, retaining previous collections and the model. It does not download assets or infer answers. Raw run receipts are retained in ignored `downloads/specialist/run-*`.

Only named source texts were reviewed. Linked third-party works and media are excluded. Repository status and dates are snapshot facts, not a claim of current chain activation, gas prices or security recommendations. This development evaluation is neither held-out quality evidence nor physical-device acceptance.
