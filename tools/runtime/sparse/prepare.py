"""Reuse only byte-verified isolated derivations, never modify the pinned source."""
import hashlib,json,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[3]
identity=json.loads(pathlib.Path(__file__).with_name('identity.json').read_text())
key=identity['patch_sha256'][:16];out=R/'downloads/strong-native-host'/('derivation-'+key)
if not out.exists():subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('derive.py')),str(out)],check=True,stdout=sys.stderr)
r=json.loads((out/'derivation.json').read_text())
assert r['base']==identity
for p,h in r['files'].items():assert hashlib.sha256((out/'source'/p).read_bytes()).hexdigest()==h
print(out/'source')
