#!/usr/bin/env python3
"""Create the private license/provenance manifest without changing source text."""
import argparse, json, pathlib
from acquire import PRIMARY, LICENSE, filehash, save

def build(stage):
 rules=json.loads((stage/'selection-v1.json').read_text())
 manifest={
  'dataset':'https://huggingface.co/datasets/'+rules['dataset'],
  'dataset_revision':rules['revision'],'snapshot':rules['config'],
  'selection_sha256':filehash(stage/'selection-v1.json'),
  'source_jsonl_sha256':filehash(stage/'sources.jsonl'),
  'chunk_jsonl_sha256':filehash(stage/'chunks.jsonl'),
  'license':'CC-BY-SA-4.0','license_url':LICENSE,
  'primary_sources':{name:{'url':url,'sha256':filehash(stage/'raw'/name)} for name,url in PRIMARY.items()},
  'license_resolution':'Wikimedia Terms of Use section 7, effective June 7, 2023, and dump licensing specify CC BY-SA 4.0; the November 2023 extracted dataset card declares CC BY-SA 3.0/GFDL and that discrepancy is preserved, not treated as CC0 or a waiver.',
  'dataset_card_sha256':filehash(stage/'raw/dataset-card.md'),
  'attribution_method':'Article title, Wikipedia contributors, article URL and contributor-history URL on each source and chunk; section 7 permits attribution via article URLs.',
  'redistribution_obligations':['Retain attribution and source/history links','Retain CC BY-SA 4.0 license URL and supply staged license text for offline access','Indicate upstream extraction and PocketLore excerpting modifications','Share adapted text under CC BY-SA 4.0 or a compatible license','Do not apply additional restrictions','Preserve any source-specific imported-content notices; review exceptions before distribution'],
  'unknowns':['No per-article revision IDs, timestamps or contributor lists are supplied by this upstream extract','History links are live attribution references, not frozen contributor records','Plain-text extraction may omit third-party attribution or exception notices; marker rejection is not exhaustive copyright clearance'],
  'modifications':'Full upstream extracted text retained; nonoverlapping verbatim chunks with character offsets and UTF-8 hashes; no synthetic factual passages.',
  'scope':'Private corpus staging only; model-answer, product, physical-device and bounty acceptance are not established.'}
 save(stage/'license-provenance.json',manifest)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=pathlib.Path);a=p.parse_args();build(a.stage)
