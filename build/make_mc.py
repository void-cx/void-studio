import re
t=open('tpl.html').read()
def rep(a,b):
    global t
    assert a in t, a[:90]; t=t.replace(a,b)

# ---------- Namen
rep("VOID × AION 2 · OBS-Szenenset","VOID × MINECRAFT · OBS-Szenenset")
rep("  ?scene=game      AION 2 Game           transparentes Overlay, Kamera UNTER diese Quelle legen","  ?scene=game      Minecraft Game        transparentes Overlay, Kamera UNTER diese Quelle legen")
rep("<title>VOID × AION 2 · Szenen</title>","<title>VOID × Minecraft · Szenen</title>")
rep('<span class="aion">AION 2</span>','<span class="aion">Minecraft</span>')
rep(">AION 2</span>'));",">Minecraft</span>'));")
rep("P.get('title')||'AION 2'","P.get('title')||'Minecraft'")
rep("'Welche Klasse spielst du in AION 2?','Kantor, natürlich.','Die Flügel im Overlay sind schick'",
    "'Wie weit ist die Fabrik?','Die Zahnräder drehen falsch rum','Die Pixel-Wolken sind schick'")

# ---------- Farben: Smaragd + XP-Grün, Verzauberungs-Violett bleibt
rep("--aether:#BFE6FF;     /* Runenlicht */","--aether:#9DF7B6;     /* Spielfarbe hell */")
rep("--sky:#7FC8FF;","--sky:#3FD46A;        /* Spielfarbe: Smaragd */\n  --xp:#7CFF5A;         /* XP-Leiste */")
for a,b in [("#B303F8,#7FC8FF","#2E9E4F,#7CFF5A"),("#B303F8,#E6F5FF","#7CFF5A,#D7FFC2"),
            ("rgba(110,190,255","rgba(80,220,120"),("rgba(80,160,255","rgba(40,190,90"),("#E6F5FF","#F2F5EE"),
            ("#CFE3FF","#D9EBD9"),("#BFE6FF","#9DF7B6"),("rgba(191,230,255","rgba(180,240,190"),
            ("rgba(127,200,255","rgba(90,220,130"),("rgba(80,150,255","rgba(60,200,110")]:
    rep(a,b)

# ---------- Schriften: Pixelify Sans statt Runen/VOID Latin, Effekt = verschleierter Text
rep('@font-face{font-family:"VOID Runes";src:url(data:font/woff2;base64,__RUNES__) format("woff2");font-display:block}\n@font-face{font-family:"VOID Latin";src:url(data:font/woff2;base64,__LATIN__) format("woff2");font-display:block}\n',
 '@font-face{font-family:"Pixelify Sans";font-weight:500;src:url(data:font/woff2;base64,__PX5__) format("woff2");font-display:block}\n'
 '@font-face{font-family:"Pixelify Sans";font-weight:700;src:url(data:font/woff2;base64,__PX7__) format("woff2");font-display:block}\n'
 '@font-face{font-family:"JetBrains Mono";font-weight:500;src:url(data:font/woff2;base64,__JB5__) format("woff2");font-display:block}\n')
rep('font-family:"VOID Runes";font-weight:400;','font-family:"Pixelify Sans";font-weight:700;')
t=t.replace('"VOID Latin"','"Pixelify Sans"').replace("\\'VOID Latin\\'","\\'Pixelify Sans\\'")
rep('.halo text{font-family:"VOID Runes";fill:var(--aether)}\n','')
rep("rastet Buchstabe für Buchstabe in VOID Latin ein.","rastet Buchstabe für Buchstabe ein (wie verschleierter Text in Minecraft).")
rep("const POOL='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';","const POOL='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#%&?!';")
rep("const glyph=c=>KEY&&RUNESET.has(c.toUpperCase())?c:rr();","const glyph=c=>rr();             /* Minecraft: verschleierte Zeichen, kein Runen-Schlüssel */")

# ---------- Himmel: Pixel-Nacht
rep("""    radial-gradient(900px 700px at 8% 18%, rgba(179,3,248,.30), transparent 70%),
    radial-gradient(1000px 760px at 94% 30%, rgba(80,170,255,.26), transparent 70%),
    radial-gradient(1200px 520px at 50% 108%, rgba(17,65,228,.32), transparent 70%),
    radial-gradient(700px 500px at 50% 46%, rgba(180,240,190,.10), transparent 70%),
    linear-gradient(180deg,#080A22 0%,var(--night) 55%,#05061A 100%);}""",
"""    radial-gradient(900px 600px at 6% 10%, rgba(179,3,248,.16), transparent 70%),
    radial-gradient(1200px 500px at 50% 100%, rgba(63,212,106,.12), transparent 70%),
    linear-gradient(180deg,#05061A 0%,#0A1030 42%,#122448 72%,#183A44 100%);}""")
rep(".mote{position:absolute;border-radius:50%;",".mote{position:absolute;border-radius:0;")
rep("const d=el('div','mote'+(Math.random()<.35?' v':''));const s=rnd(3,8);","const d=el('div','mote'+(Math.random()<.5?' v':''));const s=[4,6,8][Math.random()*3|0];")
rep("@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}","@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}\n.beam{display:none}")

# ---------- Motiv: Pixel-Landschaft
rep("@keyframes rise{","""/* ---------- Motiv: Pixel-Nacht über Blockhügeln ---------- */
.px-stars i{position:absolute;width:4px;height:4px;background:#E8F0FF;animation:twinkle 3s steps(2) infinite}
@keyframes twinkle{50%{opacity:.25}}
.px-moon{position:absolute;right:250px;top:120px;width:96px;height:96px;background:#E9EEF6;
  box-shadow:0 0 0 12px rgba(233,238,246,.12),0 0 80px 30px rgba(200,215,255,.12)}
.px-moon i{position:absolute;background:#C7CEDB}
.px-clouds{position:absolute;left:0;top:0;width:3840px;height:1080px;animation:clouds 140s linear infinite;will-change:transform}
.px-clouds i{position:absolute;height:40px;background:rgba(220,230,255,.07)}
@keyframes clouds{to{transform:translateX(-1920px)}}
.px-land{position:absolute;left:0;bottom:0;width:1920px;height:1080px}
@keyframes rise{""")
rep("/* Achteck-Loch mit abgeschrägten Ecken","""/* Pixel-Nacht: Sterne, eckiger Mond, flache Wolken, drei Lagen Blockhügel */
function motif(target){
  const st=el('div','px-stars');
  for(let i=0;i<70;i++){const s=el('i');s.style.cssText=`left:${(i*277)%1920}px;top:${(i*131)%620}px;animation-delay:-${(i%7)*.43}s;opacity:${.4+(i%3)*.25}`;st.appendChild(s)}
  target.appendChild(st);
  const moon=el('div','px-moon');[[12,16,20],[52,28,16],[24,60,24],[64,64,12]].forEach(([x,y,s])=>{const c=el('i');c.style.cssText=`left:${x}px;top:${y}px;width:${s}px;height:${s}px`;moon.appendChild(c)});
  target.appendChild(moon);
  const cl=el('div','px-clouds');
  [[80,160,280],[520,240,200],[900,120,360],[1400,210,240],[1700,140,180]].forEach(([x,y,w])=>[0,1920].forEach(o=>{
    const c=el('i');c.style.cssText=`left:${x+o}px;top:${y}px;width:${w}px`;cl.appendChild(c);
    const c2=el('i');c2.style.cssText=`left:${x+o+40}px;top:${y-40}px;width:${w*.55|0}px`;cl.appendChild(c2)}));
  target.appendChild(cl);
  const layer=(b,base,amp,ph,col)=>{let x=0,d=`M0,1080`;
    while(x<=1920){const h=Math.round((base+amp*Math.sin(x/1920*Math.PI*2.4+ph)+amp*.45*Math.sin(x/1920*Math.PI*7+ph*2))/b)*b;
      d+=` L${x},${1080-h} L${x+b},${1080-h}`;x+=b}
    return `<path d="${d} L1920,1080Z" fill="${col}"/>`};
  const land=el('div','px-land');
  land.innerHTML=`<svg viewBox="0 0 1920 1080" width="1920" height="1080">${layer(48,300,90,0.3,'#0F1D33')}${layer(32,200,70,1.7,'#10261F')}${layer(24,110,40,3.1,'#0A1A12')}
    <rect x="0" y="1062" width="1920" height="18" fill="#2E9E4F" opacity=".35"/></svg>`;
  target.appendChild(land);
}

/* Achteck-Loch mit abgeschrägten Ecken""")
rep("  sky(stage);halo(stage);wings(stage);","  sky(stage);motif(stage);")

# ---------- Rahmen: Pixel-Ecken
rep("   ${dia(cx,y)}${dia(cx,y+h)}`;","""   ${[[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]].map(([px,py,sx,sy])=>
      [[0,0],[8,0],[16,0],[0,8],[0,16]].map(([dx,dy])=>`<rect x="${px+sx*dx-(sx<0?8:0)}" y="${py+sy*dy-(sy<0?8:0)}" width="8" height="8" fill="#3FD46A"/>`).join('')).join('')}`;""")

# ---------- Texte
rep("start:{title:'Stream startet',subs:['Client wird gepatcht','Charakter wird gewählt','Aether wird gesammelt','Kaffee steht bereit','Gleich geht’s los']}",
    "start:{title:'Stream startet',subs:['Welt wird generiert','Chunks werden geladen','Zahnräder werden geschmiert','Spawnpunkt wird gesetzt','Gleich geht’s los']}")
rep("pause:{title:'Kurze Pause',subs:()=>['Bin gleich zurück','Chat bleibt offen',...latestLines(),'Kurz Aether tanken']}",
    "pause:{title:'Kurze Pause',subs:()=>['Kurz AFK','Der Ofen läuft noch',...latestLines(),'Bin gleich zurück']}")
rep("follow:e=>['Neuer Follow','Danke fürs Folgen'],","follow:e=>['Neuer Follow','ist der Welt beigetreten'],")
rep("sub:   e=>['Neues Abo',(e.tier?`Stufe ${e.tier}`:'')],","sub:   e=>['Neues Abo',`Fortschritt erzielt${tier(e.tier)}`],")
rep("resub: e=>['Abo verlängert',`${e.months} Monate${tier(e.tier)}`],","resub: e=>['Abo verlängert',`${e.months} Monate überlebt${tier(e.tier)}`],")
rep("gift:  e=>[e.amount>1?'Abos verschenkt':'Abo verschenkt',`${e.amount} ${e.amount>1?'Abos':'Abo'}${tier(e.tier)}`],",
    "gift:  e=>[e.amount>1?'Abos verschenkt':'Abo verschenkt',`${e.amount} ${e.amount>1?'Abos':'Abo'} gedroppt${tier(e.tier)}`],")
rep("cheer: e=>['Bits',`${e.amount} Bits`],","cheer: e=>['Bits',`${e.amount} Bits · +${e.amount} XP`],")
rep("raid:  e=>['Raid',`mit ${e.amount} ${e.amount==1?'Person':'Leuten'}`],","raid:  e=>['Raid',`${e.amount} ${e.amount==1?'Person spawnt':'Leute spawnen'}`],")

# ---------- Klang: kurzes XP-Pling
rep("const base={follow:523.25,","const base={follow:880,")
rep("sub:440,resub:440,gift:392,cheer:587.33,raid:329.63,redeem:493.88}","sub:784,resub:784,gift:698.46,cheer:1046.5,raid:587.33,redeem:830.6}")
rep("[[ 'sine',1,.5],['triangle',.5,.18]]","[['sine',1,.45],['square',1,.03]]")
rep("const t=t0+i*.11;","const t=t0+i*.06;")
rep("e.gain.exponentialRampToValueAtTime(.0001,t+1.8);o.connect(e).connect(out);o.start(t);o.stop(t+1.9)",
    "e.gain.exponentialRampToValueAtTime(.0001,t+.45);o.connect(e).connect(out);o.start(t);o.stop(t+.5)")

# ---------- Typografie, Pixel-Alerts, XP-Leisten
def steps(c=12,s=4):
    pts=[];n=c//s
    tl=[(0,c)]+[(s*i if j==0 else s*i, c-s*i) for i in range(1,n) for j in (0,)]
    # Treppe: (0,c)->(s,c)->(s,c-s)->(2s,c-s)...->(c,0)
    tl=[];x,y=0,c
    for i in range(n):tl+= [(x,y),(x+s,y)];x+=s;y-=s
    tl.append((c,0))
    f=lambda X,Y:f"{X} {Y}"
    P=[f(f"{a}px",f"{b}px") for a,b in tl]
    P+=[f(f"calc(100% - {c-b}px)" if True else '',f"{a}px") for a,b in []]
    return tl
def poly(c=12,s=4):
    tl=[];x,y=0,c
    for i in range(c//s):tl+=[(x,y),(x+s,y)];x+=s;y-=s
    tl.append((c,0))
    pts=[f"{a}px {b}px" for a,b in tl]
    pts+=[f"calc(100% - {a}px) {b}px" for a,b in reversed(tl)]                       # oben rechts
    pts+=[f"calc(100% - {a}px) calc(100% - {b}px)" for a,b in tl]                   # unten rechts
    pts+=[f"{a}px calc(100% - {b}px)" for a,b in reversed(tl)]                       # unten links
    return "polygon("+",".join(pts)+")"
P=poly()
rep("@media (prefers-reduced-motion:reduce)",f"""/* ---------- Minecraft-Typografie und Pixel-Formen ---------- */
.title{{font-weight:700;font-size:138px;letter-spacing:.02em;color:#F2F5EE;text-shadow:.07em .07em 0 rgba(0,0,0,.55),0 0 .3em rgba(63,212,106,.25)}}
.status{{font-weight:500;font-size:34px;letter-spacing:.06em;text-shadow:.08em .08em 0 rgba(0,0,0,.55)}}
.head .title{{font-size:62px}}
.plate .title{{font-size:22px;font-weight:700}}
.a-name{{font-weight:700;font-size:62px;letter-spacing:.02em;text-shadow:.07em .07em 0 rgba(0,0,0,.6)}}
.a-detail{{font-weight:500;font-size:26px;letter-spacing:.04em;color:#FFE16A}}
.foot .aion{{font-weight:700;letter-spacing:.04em}}
.m-name{{font-weight:700;font-size:19px;letter-spacing:.02em}}
.g-v{{font-family:"JetBrains Mono";font-size:14px;letter-spacing:0}}
.ch .rn{{font-size:1em;top:0;color:var(--aether);text-shadow:.07em .07em 0 rgba(0,0,0,.55)}}
.ch.v .rn{{color:#E2A6FF}}
.alert{{clip-path:{P}}}
.alert .body{{clip-path:{P};background:linear-gradient(180deg,#1B2033,#0C0F1E)}}
.alert{{background:linear-gradient(135deg,#3FD46A,#7CFF5A 50%,#B303F8)}}
.goal,.plate{{clip-path:{poly(8,4)}}}
.g-track{{height:8px;background:#1A2A1A;outline:2px solid #000}}
.g-fill{{background:var(--xp)!important}}
.g-track::after{{content:"";position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent 0 calc(5.55% - 2px),#000 calc(5.55% - 2px) 5.55%)}}
.g-head{{transform:none;border-radius:0;background:var(--xp);border:2px solid #000;box-shadow:0 0 8px rgba(124,255,90,.8)}}

@media (prefers-reduced-motion:reduce)""")

# ---------- Stinger: Chunks laden ein, Bildmarke, Blöcke brechen weg
t=re.sub(r'/\* STINGER-CSS-START \*/.*?/\* STINGER-CSS-END \*/',lambda m:'''/* STINGER-CSS-START */
.mc-back{position:absolute;inset:0;background:#141A24;opacity:0;animation:mcBack 1.95s steps(1) both}
@keyframes mcBack{0%{opacity:0}26.5%{opacity:1}74%,100%{opacity:0}}
.mc-b{position:absolute;width:80px;height:80px;transform:scale(0);animation:mcB 1.95s both;
  box-shadow:inset 0 0 0 4px rgba(255,255,255,.05),inset -8px -8px 0 rgba(0,0,0,.18)}
/* STINGER-CSS-END */''',t,flags=re.S)
t=re.sub(r'/\* STINGER-THEME-START \*/.*?/\* STINGER-THEME-END \*/',lambda m:'''/* STINGER-THEME-START */
/* Minecraft: Blöcke laden diagonal wie Chunks ein, die Bildmarke baut sich auf, dann brechen die Blöcke weg */
function stingerTheme(root){
  root.appendChild(el('div','mc-back'));          /* deckt Kanten zwischen den Blöcken ab */
  const cols=['#1D2433','#222A3B','#19202D','#262F42','#1B2B26','#203226','#2A2235'];
  let css='';const S=80,C=24,R=14;
  for(let y=0;y<R;y++)for(let x=0;x<C;x++){
    const k=y*C+x,n=((x*73+y*151)%97)/97;           /* feste Streuung, damit jede Aufnahme gleich ist */
    const tin=Math.min(.9,((x+y)/(C+R))*.85+n*.15), tout=.2+n*.8;
    const a=(4+tin*20).toFixed(1), b=(a*1+3.5).toFixed(1), c=(75+tout*18).toFixed(1), d=(+c+5).toFixed(1);
    css+=`@keyframes mcB${k}{0%,${a}%{transform:scale(0)}${b}%,${c}%{transform:scale(1) translateY(0);opacity:1}${d}%,100%{transform:scale(.4) translateY(140px) rotate(${(n*60-30)|0}deg);opacity:0}}`;
    const base=cols[(x*3+y*5+(n*7|0))%cols.length];
    const ore=n<.1?'#3FD46A':n>.92?'#B36BFF':'';      /* Erzpunkte: Smaragd und Amethyst */
    const bg=ore?`linear-gradient(${ore},${ore}) 16px 20px/12px 12px no-repeat,linear-gradient(${ore},${ore}) 44px 40px/12px 12px no-repeat,linear-gradient(${ore},${ore}) 24px 52px/8px 8px no-repeat,${base}`:base;
    const bl=el('div','mc-b');bl.style.cssText=`left:${x*S}px;top:${y*S}px;background:${bg};animation-name:mcB${k}`;
    root.appendChild(bl);
  }
  const st=document.createElement('style');st.textContent=css;root.appendChild(st);
}
function stingerMark(m,root){m.style.zIndex=5}
/* STINGER-THEME-END */''',t,flags=re.S)

open('tpl_minecraft.html','w').write(t)
print('AION übrig:',len(re.findall('AION',t)))

# ===== Runde 2: Blocky-Logo, Splash-Text, Fortschritts-Toasts =====
import json as _json
B=_json.load(open('blocky32.json'))
# statische Blocky-Marke als Datei (Toast-Icon)
def hx(h):return [int(h[i:i+2],16) for i in (1,3,5)]
def sh(h,dv):return '#%02x%02x%02x'%tuple(max(0,min(255,c+dv)) for c in hx(h))
rects=''.join(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{B["pal"][k]}"/><rect x="{x}" y="{y}" width="1" height=".14" fill="{sh(B["pal"][k],35)}"/><rect x="{x+.86}" y="{y}" width=".14" height="1" fill="{sh(B["pal"][k],-45)}"/>' for x,y,k in B['cells'])
open('extra_minecraft/void-mark-blocky.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" shape-rendering="crispEdges">{rects}</svg>')

t=open('tpl_minecraft.html').read()
# Blocky-Bildmarke: ersetzt makeMark() (spätere Funktionsdeklaration gewinnt)
rep("/* Achteck-Loch mit abgeschrägten Ecken",'''/* Minecraft: Bildmarke als Pixel-Blöcke, wird Block für Block von unten nach oben gebaut */
const BLOCKY=%s;
function makeMark({cls='',d=0,t=700}={}){
  const w=el('div','vmark blk play '+cls);
  w.style.setProperty('--d',d+'ms');w.style.setProperty('--t',t+'ms');
  const sh=(h,dv)=>'#'+[1,3,5].map(i=>Math.max(0,Math.min(255,parseInt(h.substr(i,2),16)+dv)).toString(16).padStart(2,'0')).join('');
  let g='';
  BLOCKY.cells.forEach(([x,y,k])=>{const c=BLOCKY.pal[k],del=d+(31-y)*t*.028+((x*7+y*3)%%5)*t*.012;
    g+=`<g class="bk" style="animation-delay:${del|0}ms"><rect x="${x}" y="${y}" width="1" height="1" fill="${c}"/>
      <rect x="${x}" y="${y}" width="1" height=".14" fill="${sh(c,35)}"/><rect x="${x+.86}" y="${y}" width=".14" height="1" fill="${sh(c,-45)}"/></g>`});
  w.innerHTML=`<i class="glow"></i><svg viewBox="0 0 32 32" shape-rendering="crispEdges" aria-label="VOID">${g}</svg>`;
  return w;
}

/* Achteck-Loch mit abgeschrägten Ecken''' % _json.dumps({'pal':B['pal'],'cells':B['cells']}))

# Splash-Text am Titel (wie im Hauptmenü)
rep("  T.show(P.get('title')||cfg.title,1500).then(()=>{","""  const SPL=['Auf eigener Hardware!','Seit 2016!','Mit extra Zahnrädern!','Chunks inklusive!','Jetzt mit Create!','Nicht graben, bauen!'];
  const sp=el('div','splash');sp.innerHTML=`<span>${P.get('splash')||SPL[Math.random()*SPL.length|0]}</span>`;c.appendChild(sp);
  T.show(P.get('title')||cfg.title,1500).then(()=>{
    sp.style.left=(t.offsetLeft+t.offsetWidth-40)+'px';sp.style.top=(t.offsetTop+t.offsetHeight-10)+'px';sp.classList.add('on');""")

rep("@media (prefers-reduced-motion:reduce)","""/* ---------- Blocky-Marke, Splash, Toasts ---------- */
.vmark.blk .bk{transform-box:fill-box;transform-origin:50% 100%}
.vmark.blk.play .bk{animation:bkIn calc(var(--t)*.26) steps(3,end) both}
@keyframes bkIn{from{transform:scaleY(0) translateY(-2px);opacity:0}}
.vmark.blk.mark{width:150px;margin-bottom:26px}
.splash{position:absolute;transform:translate(-50%,-50%) rotate(-18deg);white-space:nowrap;opacity:0;transition:opacity .3s;
  font-family:"Pixelify Sans";font-weight:700;font-size:36px;color:#FFFF55;text-shadow:.09em .09em 0 #3F3F15}
.splash.on{opacity:1}
.splash span{display:inline-block;animation:splash .55s ease-in-out infinite alternate}
@keyframes splash{to{transform:scale(1.09)}}
.alerts{justify-content:flex-end;padding-right:40px;top:40px}
.alert{transform:translateX(130%)}
.alert.in{transform:none}
.alert .body{display:grid;grid-template-columns:76px 1fr;column-gap:22px;align-items:center;text-align:left;min-width:560px;max-width:780px;padding:18px 30px 18px 18px}
.alert .body::before{content:"";grid-row:1/span 4;align-self:center;width:76px;height:76px;background:#0C0F1E url(assets/void-mark-blocky.svg) center/54px no-repeat;
  box-shadow:inset 3px 3px 0 #000,inset -3px -3px 0 #3A3F55}
.a-kind{grid-column:2;color:#FFFF55;font-family:"Pixelify Sans";font-weight:700;font-size:20px;margin-bottom:6px}
.a-name{grid-column:2;font-size:44px}
.a-detail{grid-column:2;margin-top:6px;font-size:22px}
.a-msg{grid-column:2;margin:8px 0 0;max-width:none}
.alert .vmark{display:none}

@media (prefers-reduced-motion:reduce)""")
open('tpl_minecraft.html','w').write(t)
