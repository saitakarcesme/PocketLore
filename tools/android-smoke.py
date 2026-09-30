#!/usr/bin/env python3
"""Exercise PocketLore on an explicitly selected emulator; never a phone acceptance test."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--adb', default='/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb')
parser.add_argument('--serial', required=True)
parser.add_argument('--evidence', type=Path, required=True)
args = parser.parse_args()
if not args.serial.startswith('emulator-'):
    raise SystemExit('This smoke script is emulator-only and disables emulator Wi-Fi/mobile data.')
args.evidence.mkdir(parents=True, exist_ok=True)

def adb(*command, binary=False):
    return subprocess.check_output([args.adb, '-s', args.serial, *command], text=not binary)

def hierarchy(name):
    adb('shell', 'uiautomator', 'dump', '/sdcard/pocketlore-smoke.xml')
    data = adb('shell', 'cat', '/sdcard/pocketlore-smoke.xml')
    (args.evidence / (name + '.xml')).write_text(data)
    return ET.fromstring(data)

def tap(node):
    bounds = list(map(int, re.findall(r'\d+', node.attrib['bounds'])))
    adb('shell', 'input', 'tap', str((bounds[0] + bounds[2]) // 2), str((bounds[1] + bounds[3]) // 2))

def screenshot(name):
    (args.evidence / (name + '.png')).write_bytes(adb('exec-out', 'screencap', '-p', binary=True))

def launch():
    adb('shell', 'am', 'force-stop', 'org.pocketlore.app')
    adb('shell', 'am', 'start', '-n', 'org.pocketlore.app/.MainActivity')
    for _ in range(10):
        tree = hierarchy('launch')
        if any('8 passages installed' in n.get('text', '') for n in tree.iter('node')):
            return tree
        time.sleep(0.3)
    raise AssertionError('Pack did not load')

def query(text):
    tree = launch()
    tap(next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText'))
    adb('shell', 'input', 'text', text.replace(' ', '%s'))
    adb('shell', 'input', 'keyevent', '4')
    tap(next(n for n in tree.iter('node') if n.get('text') == 'FIND EVIDENCE'))
    return hierarchy('answer')

apk = ROOT / 'android/app/build/outputs/apk/debug/app-debug.apk'
installation = adb('install', '-r', str(apk))
assert 'Success' in installation, installation
adb('shell', 'svc', 'wifi', 'disable')
adb('shell', 'svc', 'data', 'disable')
tree = query('Compare evaporation and condensation')
texts = '\n'.join(n.get('text', '') for n in tree.iter('node'))
assert '[water-02]' in texts and '[water-01]' in texts, texts
assert 'not a generated explanation' in texts
screenshot('answer')
for _ in range(6):
    tree = hierarchy('sources')
    buttons = [n for n in tree.iter('node') if n.get('text', '').startswith('Inspect [water-02]')]
    if buttons:
        tap(buttons[0]); break
    adb('shell', 'input', 'swipe', '550', '2080', '550', '620', '350')
else:
    raise AssertionError('Source inspection button not found')
tree = hierarchy('source-detail')
texts = '\n'.join(n.get('text', '') for n in tree.iter('node'))
assert 'https://www.usgs.gov/' in texts and 'verbatim USGS paragraph' in texts
screenshot('source-detail')
tree = query('quasar supernova')
assert any('No supporting passage' in n.get('text', '') for n in tree.iter('node'))
screenshot('unsupported')
(args.evidence / 'emulator-meminfo.txt').write_text(adb('shell', 'dumpsys', 'meminfo', 'org.pocketlore.app'))
package = adb('shell', 'dumpsys', 'package', 'org.pocketlore.app')
(args.evidence / 'package.txt').write_text(package)
assert 'android.permission.INTERNET' not in package
result = {
    'status': 'passed', 'environment': 'AOSP API 35 x86_64 emulator; not physical hardware',
    'serial': args.serial, 'apk_sha256': hashlib.sha256(apk.read_bytes()).hexdigest(), 'apk_bytes': apk.stat().st_size,
    'checks': ['install and launch', 'pack loaded', 'comparison evidence retrieved', 'source provenance dialog', 'unsupported-query abstention', 'no INTERNET permission'],
    'network_state': {'wifi_on': adb('shell', 'settings', 'get', 'global', 'wifi_on').strip(), 'mobile_data': adb('shell', 'settings', 'get', 'global', 'mobile_data').strip()},
    'physical_device_acceptance': False,
}
(args.evidence / 'smoke-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
