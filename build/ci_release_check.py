"""Entscheidet, ob ein Release nötig ist: nur wenn eine Version in versions.json neuer ist als im letzten Release."""
import json, os, sys, urllib.request
repo = os.environ['GITHUB_REPOSITORY']
force = os.environ.get('FORCE', 'false') == 'true'
V = json.load(open('versions.json'))
try:
    with urllib.request.urlopen(f'https://github.com/{repo}/releases/latest/download/index.json', timeout=20) as r:
        old = json.load(r)
    prev = {p['id']: p['version'] for p in old.get('packs', [])}
    prev['studio'] = old.get('studio', {}).get('version')
except Exception as e:
    print(f'Kein bisheriges Release gefunden ({e}) – erstes Release.')
    prev = {}
changed = [k for k, v in V.items() if k != 'hold' and k not in V.get('hold', []) and prev.get(k) != v]
release = force or bool(changed)
print('Geänderte Versionen:', ', '.join(f'{k} {prev.get(k)} → {V[k]}' for k in changed) or 'keine')
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(f'release={"true" if release else "false"}\n')
