import json, os, re, shutil, uuid, glob, subprocess, asyncio
import sys
OUT='dist/packs'; os.makedirs(OUT,exist_ok=True)
ONLY=sys.argv[1:]          # z. B. python3 packs.py minecraft  -> nur dieses Pack neu bauen
SG='fontsource-space-grotesk-5.3.0/files/'
BC=glob.glob('fontsource-barlow-condensed-*/files')[0]+'/'; JB=glob.glob('fontsource-jetbrains-mono-*/files')[0]+'/'
FONT='font/'

THEMES={
 'aion2':{'tpl':'tpl.html','title':'AION 2','game':'AION 2','cam':(1472,814),
   'fonts':{'__RUNES__':('void-runes.woff2','font/VOIDRunes-Regular.woff2'),'__LATIN__':('void-latin.woff2',FONT+'VOIDLatin-Regular.woff2'),
            '__SG4__':('space-grotesk-400.woff2',SG+'space-grotesk-latin-400-normal.woff2'),'__SG5__':('space-grotesk-500.woff2',SG+'space-grotesk-latin-500-normal.woff2')},
   'licenses':['fontsource-space-grotesk-5.3.0']},
 'minecraft':{'tpl':'tpl_minecraft.html','title':'Minecraft','game':'Minecraft','cam':(1472,814),
   'fonts':{'__PX5__':('pixelify-sans-500.woff2','fontsource-pixelify-sans/files/pixelify-sans-latin-500-normal.woff2'),
            '__PX7__':('pixelify-sans-700.woff2','fontsource-pixelify-sans/files/pixelify-sans-latin-700-normal.woff2'),
            '__JB5__':('jetbrains-mono-500.woff2','fontsource-jetbrains-mono-5.3.0/files/jetbrains-mono-latin-500-normal.woff2'),
            '__SG4__':('space-grotesk-400.woff2',SG+'space-grotesk-latin-400-normal.woff2'),'__SG5__':('space-grotesk-500.woff2',SG+'space-grotesk-latin-500-normal.woff2')},
   'licenses':['fontsource-space-grotesk-5.3.0','fontsource-pixelify-sans-x','fontsource-jetbrains-mono-5.3.0']},
 'ets2':{'tpl':'tpl_ets2.html','title':'ETS2','game':'ETS2','cam':(1472,814),'drive':True,
   'fonts':{'__BW5__':('barlow-500.woff2','fontsource-barlow/files/barlow-latin-500-normal.woff2'),
            '__BW7__':('barlow-700.woff2','fontsource-barlow/files/barlow-latin-700-normal.woff2'),
            '__JB5__':('jetbrains-mono-500.woff2','fontsource-jetbrains-mono-5.3.0/files/jetbrains-mono-latin-500-normal.woff2'),
            '__SG4__':('space-grotesk-400.woff2',SG+'space-grotesk-latin-400-normal.woff2'),'__SG5__':('space-grotesk-500.woff2',SG+'space-grotesk-latin-500-normal.woff2')},
   'licenses':['fontsource-space-grotesk-5.3.0','fontsource-barlow-x','fontsource-jetbrains-mono-5.3.0']},
 'gta':{'tpl':'tpl_gta.html','title':'GTA RP','game':'GTA','cam':(1472,330),
   'fonts':{'__AN4__':('anton-400.woff2','fontsource-anton/files/anton-latin-400-normal.woff2'),
            '__JB5__':('jetbrains-mono-500.woff2','fontsource-jetbrains-mono-5.3.0/files/jetbrains-mono-latin-500-normal.woff2'),
            '__SG4__':('space-grotesk-400.woff2',SG+'space-grotesk-latin-400-normal.woff2'),'__SG5__':('space-grotesk-500.woff2',SG+'space-grotesk-latin-500-normal.woff2')},
   'licenses':['fontsource-space-grotesk-5.3.0','fontsource-anton-x','fontsource-jetbrains-mono-5.3.0']},
 'void':{'tpl':'tpl_void.html','title':'VOID','game':'Spiel','capname':'Spielaufnahme','collname':'VOID','cam':(1472,814),
   'fonts':{'__SG7__':('space-grotesk-700.woff2',SG+'space-grotesk-latin-700-normal.woff2'),
            '__JB5__':('jetbrains-mono-500.woff2','fontsource-jetbrains-mono-5.3.0/files/jetbrains-mono-latin-500-normal.woff2'),
            '__SG4__':('space-grotesk-400.woff2',SG+'space-grotesk-latin-400-normal.woff2'),'__SG5__':('space-grotesk-500.woff2',SG+'space-grotesk-latin-500-normal.woff2')},
   'licenses':['fontsource-space-grotesk-5.3.0','fontsource-jetbrains-mono-5.3.0']},
 'wardogs':{'tpl':'tpl_wardogs.html','title':'Wardogs','game':'Wardogs','cam':(1472,330),
   'fonts':{'__BC5__':('barlow-condensed-500.woff2',BC+'barlow-condensed-latin-500-normal.woff2'),'__BC7__':('barlow-condensed-700.woff2',BC+'barlow-condensed-latin-700-normal.woff2'),
            '__JB5__':('jetbrains-mono-500.woff2',JB+'jetbrains-mono-latin-500-normal.woff2'),
            '__SG4__':('space-grotesk-400.woff2',SG+'space-grotesk-latin-400-normal.woff2'),'__SG5__':('space-grotesk-500.woff2',SG+'space-grotesk-latin-500-normal.woff2')},
   'licenses':['fontsource-space-grotesk-5.3.0','fontsource-barlow-condensed-5.3.0','fontsource-jetbrains-mono-5.3.0']},
}

def obs_json(key,cfg):
    base=json.load(open('base/obs-base.json',encoding='utf-8'))
    canvas=base['sources'][1]['canvas_uuid']
    def src(name,kind,settings,extra=None):
        d={"prev_ver":537001986,"name":name,"uuid":str(uuid.uuid4()),"id":kind,"versioned_id":kind,"settings":settings,
           "mixers":255,"sync":0,"flags":0,"volume":1.0,"balance":0.5,"enabled":True,"muted":False,"push-to-mute":False,
           "push-to-mute-delay":0,"push-to-talk":False,"push-to-talk-delay":0,"hotkeys":{},"deinterlace_mode":0,
           "deinterlace_field_order":0,"monitoring_type":0,"private_settings":{}}
        if extra:d.update(extra)
        return d
    # Pfade mit ./ löst der OBS-Importer relativ zum Ordner der import.json auf
    br=lambda n,s,r=True:src(n,"browser_source",{"is_local_file":True,"local_file":f"./obs/{s}.html","width":1920,"height":1080,"fps_custom":True,"fps":60,"reroute_audio":True,"restart_when_active":r,"shutdown":False})
    def item(s,i,pos=(0,0),bounds=None):
        it={"name":s["name"],"source_uuid":s["uuid"],"visible":True,"locked":False,"rot":0.0,"align":5,"bounds_type":0,"bounds_align":0,
            "bounds_crop":False,"crop_left":0,"crop_top":0,"crop_right":0,"crop_bottom":0,"id":i,"group_item_backup":False,
            "pos":{"x":float(pos[0]),"y":float(pos[1])},"scale":{"x":1.0,"y":1.0},"bounds":{"x":0.0,"y":0.0},"scale_filter":"disable",
            "blend_method":"default","blend_type":"normal","show_transition":{"duration":300},"hide_transition":{"duration":300},"private_settings":{}}
        if bounds: it.update(bounds_type=3,bounds_crop=True,bounds={"x":float(bounds[0]),"y":float(bounds[1])})
        return it
    scene=lambda n,items:src(n,"scene",{"id_counter":len(items),"custom_size":False,"items":items},{"mixers":0,"canvas_uuid":canvas})
    g=cfg['game']
    bs,bp,be=br("VOID · Start","start"),br("VOID · Pause","pause"),br("VOID · Ende","end")
    bc,bg=br("VOID · Just Chatting","chat",False),br(f"VOID · {g} Overlay","game",False)
    cam=src("Kamera","dshow_input",{"video_device_id":"","res_type":0})
    cap=src(cfg.get('capname',f"{g} Spielaufnahme"),"game_capture",{"capture_mode":"window","window":"","capture_cursor":False})
    scenes=[scene("Stream startet",[item(bs,1)]),scene("Kurze Pause",[item(bp,1)]),scene("Stream endet",[item(be,1)]),
            scene("Just Chatting",[item(cam,1,(64,176),(1248,702)),item(bc,2)]),
            scene(g,[item(cap,1,(0,0),(1920,1080)),item(cam,2,cfg['cam'],(416,234)),item(bg,3)])]
    extra=[]
    if cfg.get('drive'):        # zweite Spielszene mit Telemetrie-Rahmen
        bd=br(f"VOID · {g} Telemetrie","drive",False);extra=[bd]
        scenes.append(scene(f"{g} Telemetrie",[item(cap,1,(24,24),(1472,828)),item(cam,2,(1520,24),(376,212)),item(bd,3)]))
    base.update(name=cfg.get('collname',f"VOID × {g}"),sources=[bs,bp,be,bc,bg]+extra+[cam,cap]+scenes,scene_order=[{"name":s["name"]} for s in scenes],
                current_scene="Stream startet",current_program_scene="Stream startet")
    stg=src("VOID Stinger","obs_stinger_transition",{"path":"./assets/transition.webm",
        "tp_type":0,"transition_point":600,"audio_monitoring":0,"audio_fade_style":0,"track_matte_enabled":False,"hw_decode":True})
    base.update(transitions=[stg],current_transition="VOID Stinger")
    base['modules']['scripts-tool']=[{"path":"./bridge/../studio/void-studio.py","settings":{"tele_on":True} if cfg.get('drive') else {}}]
    return base

for key,cfg in THEMES.items():
    if ONLY and key not in ONLY: continue
    d=f'{OUT}/void-theme-{key}'
    if not os.environ.get('KEEP'): shutil.rmtree(d,ignore_errors=True)   # KEEP=1: Stinger und Vorschauen behalten
    os.makedirs(d+'/assets/fonts',exist_ok=True); os.makedirs(d+'/preview',exist_ok=True)
    t=open(cfg['tpl']).read()
    for ph,(name,srcf) in cfg['fonts'].items():
        shutil.copy(srcf,f'{d}/assets/fonts/{name}')
        t=t.replace(f'data:font/woff2;base64,{ph}',f'assets/fonts/{name}')
    shutil.copy('mark.svg',d+'/assets/void-mark.svg'); shutil.copy('lockup.svg',d+'/assets/void-lockup.svg')
    if os.path.isdir(f'extra_{key}'):
        for fn in os.listdir(f'extra_{key}'): shutil.copy(f'extra_{key}/{fn}',d+'/assets/')
    t=t.replace('"data:image/svg+xml;base64,__MARK__"','"assets/void-mark.svg"').replace('"data:image/svg+xml;base64,__LOCKUP__"','"assets/void-lockup.svg"')
    
    assert '__' not in re.sub(r'__[a-z]','',t.split('<script>')[0]) and 'base64,__' not in t
    open(d+'/scenes.html','w').write(t)
    for lic in cfg['licenses']:
        shutil.copy(lic.replace('-x','')+'/LICENSE',f"{d}/assets/fonts/LICENSE-{lic.split('-',1)[1].rsplit('-',1)[0]}.txt")
    coll=obs_json(key,cfg)
    for old in ('import.json','bridge'):                       # alte Bridge-Kopien/Importe aus früheren Builds weg
        q=os.path.join(d,old); shutil.rmtree(q) if os.path.isdir(q) else (os.remove(q) if os.path.exists(q) else None)
    json.dump(coll,open(d+'/import.template.json','w',encoding='utf-8'),ensure_ascii=False,indent=4)
    import hashlib
    sig=[(s['name'],[i['name'] for i in s['settings']['items']]) for s in coll['sources'] if s['id']=='scene']
    VER=json.load(open('versions.json'))
    LABEL={'aion2':'AION 2','wardogs':'Wardogs','minecraft':'Minecraft','ets2':'Euro Truck Simulator 2','gta':'GTA V / Roleplay','void':'VOID (ohne Spielbezug)'}
    json.dump({'id':key,'name':LABEL.get(key,coll['name']),'version':VER[key],'structure':hashlib.sha1(json.dumps(sig).encode()).hexdigest()[:10]},
              open(d+'/pack.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    os.makedirs(d+'/obs',exist_ok=True)
    for sc,extra in [('start',''),('pause',''),('end',''),('chat',''),('game',cfg.get('game_params',''))]+([('drive','')] if cfg.get('drive') else []):
        open(f'{d}/obs/{sc}.html','w').write(f"""<!DOCTYPE html><meta charset="utf-8"><title>VOID {sc}</title>
<!-- Einstiegsdatei für OBS („Lokale Datei“). Parameter hier anhängen, z. B. #scene=game&cam=bl -->
<script>location.replace('../scenes.html#scene={sc}{extra}'+(location.hash.length>1?'&'+location.hash.slice(1):''))</script>
""")

    cfg['dir']=d

print('gebaut:',ONLY or list(THEMES))
