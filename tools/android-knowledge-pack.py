#!/usr/bin/env python3
"""Acquire or reproduce the pinned starter pack; never called during app use."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent

class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.active, self.parts = True, []

    def handle_endtag(self, tag):
        if tag == 'p' and self.active:
            self.rows.append(' '.join(''.join(self.parts).split()))
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--download', action='store_true', help='Allow installation-time source downloads')
    parser.add_argument('--output', type=Path, default=ROOT / 'android/app/src/main/assets/water-science.tsv')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'android/knowledge-sources.json').read_text())
    args.cache.mkdir(parents=True, exist_ok=True)
    output = ['# id\ttitle\tsource_url\tretrieved_date\trights\ttext']
    evidence = []
    for source in manifest['sources']:
        local = args.cache / (source['id'] + '.html')
        if not local.exists():
            if not args.download:
                raise SystemExit(f'Missing source {local}; run once with --download during installation')
            request = urllib.request.Request(source['url'], headers={'User-Agent': 'PocketLore-bootstrap/0.1'})
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise SystemExit('Source exceeds acquisition limit')
            local.write_bytes(raw)
        paragraphs = Paragraphs()
        paragraphs.feed(local.read_text())
        for passage in source['passages']:
            candidates = set(p for p in paragraphs.rows if p.startswith(passage['prefix']))
            if len(candidates) != 1:
                raise SystemExit(f'Source changed: selector for {passage["id"]} has {len(candidates)} matches')
            text = candidates.pop()
            digest = hashlib.sha256(text.encode()).hexdigest()
            if digest != passage['sha256']:
                raise SystemExit(f'Source changed: hash mismatch for {passage["id"]}; review before updating manifest')
            output.append('\t'.join([passage['id'], passage['title'], source['url'], manifest['retrieved_date'],
                'USGS-authored text; U.S. public domain', text]))
            evidence.append({'id': passage['id'], 'sha256': digest, 'source': source['url']})
    data = ('\n'.join(output) + '\n').encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(json.dumps({'passages': len(evidence), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'output': str(args.output), 'sources': evidence}, indent=2))

if __name__ == '__main__':
    main()
