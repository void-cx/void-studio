import json, os, re, shutil, uuid, hashlib
import sys
import themes
OUT='dist/packs'; os.makedirs(OUT,exist_ok=True)
ONLY=sys.argv[1:]          # z. B. python3 packs.py minecraft  -> nur dieses Pack neu bauen

def obs_json(cfg):
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
    if cfg.get('layout')=='irl':
        sources,first=irl_scenes(cfg,br,src,item,scene)
        base.update(name=cfg.get('collname','VOID IRL'),sources=sources,scene_order=[{"name":s["name"]} for s in sources if s['id']=='scene'],
                    current_scene=first,current_program_scene=first)
        return finish(base,cfg,src)
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
    return finish(base,cfg,src)

def finish(base,cfg,src):
    stg=src("VOID Stinger","obs_stinger_transition",{"path":"./assets/transition.webm",
        "tp_type":0,"transition_point":600,"audio_monitoring":0,"audio_fade_style":0,"track_matte_enabled":False,"hw_decode":True})
    base.update(transitions=[stg],current_transition="VOID Stinger")
    base['modules']['scripts-tool']=[{"path":"./bridge/../studio/void-studio.py","settings":cfg.get('script_settings',{})}]
    return base

def irl_scenes(cfg,br,src,item,scene):
    """IRL: Kameras kommen als Medienquellen (SRT/RTMP vom Handy oder Encoder), dazu Szenen für eine bis vier Kameras
    und „Verbindung weg“, auf die VOID Studio bei einem Abbruch selbst schaltet."""
    names=[('start','Start','Stream startet',True),('solo','Unterwegs','Unterwegs',False),('duo','Zwei Kameras','Zwei Kameras',False),
           ('pip','Bild im Bild','Bild im Bild',False),('quad','Vier Kameras','Vier Kameras',False),('chat','Just Chatting','Just Chatting',False),
           ('pause','Pause','Kurze Pause',True),('signal','Verbindung weg','Verbindung weg',True),('end','Ende','Stream endet',True)]
    B={k:br(f"VOID · {n}",k,r) for k,n,_,r in names}
    cams=[src(f"Kamera {i}","ffmpeg_source",{"is_local_file":False,"input":f"srt://0.0.0.0:{9000+i-1}?mode=listener","input_format":"",
          "reconnect_delay_sec":2,"buffering_mb":2,"hw_decode":True,"clear_on_media_end":True,"restart_on_activate":False,
          "close_when_inactive":False}) for i in range(1,5)]
    c1,c2,c3,c4=cams
    full=lambda c,i:item(c,i,(0,0),(1920,1080))
    lay={'start':[],'solo':[full(c1,1)],
         'duo':[item(c1,1,(24,279),(928,522)),item(c2,2,(968,279),(928,522))],
         'pip':[full(c1,1),item(c2,2,(1432,48),(440,248))],
         'quad':[item(c1,1,(0,0),(960,540)),item(c2,2,(960,0),(960,540)),item(c3,3,(0,540),(960,540)),item(c4,4,(960,540),(960,540))],
         'chat':[item(c1,1,(64,176),(1248,702))],'pause':[],'signal':[],'end':[]}
    scenes=[scene(title,lay[k]+[item(B[k],len(lay[k])+1)]) for k,_,title,_ in names]
    return list(B.values())+cams+scenes,'Stream startet'


VER=json.load(open('versions.json'))
CORE=open('core/core.js',encoding='utf-8').read()
OVERLAY=open('core/overlay.js',encoding='utf-8').read()
built=[]
for cfg in themes.load(ONLY):
    key=cfg['id']
    d=f'{OUT}/void-theme-{key}'
    if not os.environ.get('KEEP'): shutil.rmtree(d,ignore_errors=True)   # KEEP=1: Stinger und Vorschauen behalten
    os.makedirs(d+'/assets/fonts',exist_ok=True); os.makedirs(d+'/preview',exist_ok=True)
    t=open(cfg['template'],encoding='utf-8').read()
    if cfg.get('core'):                 # eigenes Template: gemeinsamer Kern (Bridge, Alerts, Chat, Ziele) wird eingesetzt
        assert '/*@CORE@*/' in t, cfg['template']+': /*@CORE@*/ fehlt'
        t=t.replace('/*@CORE@*/',CORE)
    assert t.count('/*@OVERLAY@*/')==1, cfg['template']+': /*@OVERLAY@*/ fehlt'   # Einblendungen aus VOID Studio
    t=t.replace('/*@OVERLAY@*/',OVERLAY)
    for ph,(name,srcf) in cfg['fonts'].items():
        shutil.copy(srcf,f'{d}/assets/fonts/{name}')
        t=t.replace(f'data:font/woff2;base64,{ph}',f'assets/fonts/{name}')
    shutil.copy('mark.svg',d+'/assets/void-mark.svg'); shutil.copy('lockup.svg',d+'/assets/void-lockup.svg')
    extra=cfg.get('extra',f'extra_{key}')
    if os.path.isdir(extra):
        for fn in os.listdir(extra): shutil.copy(f'{extra}/{fn}',d+'/assets/')
    t=t.replace('"data:image/svg+xml;base64,__MARK__"','"assets/void-mark.svg"').replace('"data:image/svg+xml;base64,__LOCKUP__"','"assets/void-lockup.svg"')

    assert '__' not in re.sub(r'__[a-z]','',t.split('<script>')[0]) and 'base64,__' not in t
    open(d+'/scenes.html','w',encoding='utf-8').write(t)
    for name,lic in cfg['licenses'].items():
        shutil.copy(lic+'/LICENSE',f"{d}/assets/fonts/LICENSE-{name}.txt")
    coll=obs_json(cfg)
    for old in ('import.json','bridge','import.template.json'):                       # alte Bridge-Kopien/Importe aus früheren Builds weg
        q=os.path.join(d,old); shutil.rmtree(q) if os.path.isdir(q) else (os.remove(q) if os.path.exists(q) else None)
    # Vorlage im Unterordner: oben im Pack liegt nach der Installation nur import.json, die Datei für OBS
    os.makedirs(d+'/_vorlage',exist_ok=True); json.dump(coll,open(d+'/_vorlage/import.template.json','w',encoding='utf-8'),ensure_ascii=False,indent=4)
    sig=[(s['name'],[i['name'] for i in s['settings']['items']]) for s in coll['sources'] if s['id']=='scene']
    # infos: Textquellen „Info · …“, die VOID Studio in der Szene „VOID · Infos“ anlegt
    json.dump({'id':key,'name':cfg['label'],'version':VER[key],'structure':hashlib.sha1(json.dumps(sig).encode()).hexdigest()[:10],
               'infos':['Titel','Statuszeilen']+cfg.get('infos',[])},
              open(d+'/pack.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    os.makedirs(d+'/obs',exist_ok=True)
    for sc in cfg['scenes']:
        extra=cfg.get('game_params','') if sc=='game' else ''
        open(f'{d}/obs/{sc}.html','w').write(f"""<!DOCTYPE html><meta charset="utf-8"><title>VOID {sc}</title>
<!-- Einstiegsdatei für OBS („Lokale Datei“). Parameter hier anhängen, z. B. {cfg.get('param_example','#scene=game&cam=bl')} -->
<script>location.replace('../scenes.html#scene={sc}{extra}'+(location.hash.length>1?'&'+location.hash.slice(1):''))</script>
""")
    built.append(key)

print('gebaut:',built)
