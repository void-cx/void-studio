"""Release bauen: Pack-Zips, void-studio.py, index.json (Versionen + SHA-256), CHANGELOG – fertig für ein GitHub-Release."""
import hashlib, json, os, shutil, zipfile, time
import themes
PACKS='dist/packs'; OUT='dist/release'
shutil.rmtree(OUT,ignore_errors=True); os.makedirs(OUT)
V=json.load(open('versions.json'))
sha=lambda f:hashlib.sha256(open(f,'rb').read()).hexdigest()
idx={'generated':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'packs':[]}
for d in sorted(os.listdir(PACKS)):
    if d.replace('void-theme-','') in V.get('hold',[]): print('zurückgehalten:',d); continue
    src=os.path.join(PACKS,d); man=json.load(open(os.path.join(src,'pack.json'),encoding='utf-8'))
    zf=os.path.join(OUT,f'{d}.zip')
    with zipfile.ZipFile(zf,'w',zipfile.ZIP_DEFLATED) as z:
        for root,_,files in os.walk(src):
            for f in files:
                full=os.path.join(root,f); z.write(full,os.path.join(d,os.path.relpath(full,src)))
    # Vorschaubilder zusätzlich einzeln im Release, damit das Portal sie zeigen kann (VOID Studio → Szenen für OBS)
    # Reihenfolge wie in themes/<id>.json
    order=[p[0] for t in themes.load([man['id']]) for p in t['previews']]; prev=os.path.join(src,'preview'); previews=[]
    for f in sorted(os.listdir(prev) if os.path.isdir(prev) else [],key=lambda f:(order.index(f[:-4]) if f[:-4] in order else 99,f)):
        if f.endswith('.jpg'):
            shutil.copy(os.path.join(prev,f),os.path.join(OUT,f'{d}-{f}')); previews.append({'scene':f[:-4],'file':f'{d}-{f}'})
    idx['packs'].append({**man,'file':os.path.basename(zf),'sha256':sha(zf),'size':os.path.getsize(zf),'previews':previews})
shutil.copy('../studio/void-studio.py',OUT)
log=json.load(open('changelog.json',encoding='utf-8'))
idx['studio']={'version':V['studio'],'file':'void-studio.py','sha256':sha(os.path.join(OUT,'void-studio.py')),'changelog':log.get(V['studio'],[])}
json.dump(idx,open(os.path.join(OUT,'index.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
with open(os.path.join(OUT,'CHANGELOG.md'),'w',encoding='utf-8') as f:
    f.write('# VOID Studio – Änderungen\n\n')
    for v,items in log.items(): f.write(f'## {v}\n\n'+''.join(f'- {i}\n' for i in items)+'\n')
print('\n'.join(f"{p['id']:10} {p['version']}  {p['size']//1024} KB" for p in idx['packs']))
