import re
t=open('tpl.html').read()
def rep(a,b):
    global t
    assert a in t, a[:90]; t=t.replace(a,b)

# ---------- Namen
rep("VOID × AION 2 · OBS-Szenenset","VOID · OBS-Szenenset (ohne Spielbezug)")
rep("  ?scene=game      AION 2 Game           transparentes Overlay, Kamera UNTER diese Quelle legen","  ?scene=game      Spiel                 transparentes Overlay, Kamera UNTER diese Quelle legen")
rep("<title>VOID × AION 2 · Szenen</title>","<title>VOID · Szenen</title>")
rep('<div class="pair"><span>Enter The Void</span><span class="x">×</span><span class="aion">AION 2</span></div>',
    '<div class="pair chips" id="chips"><span class="dom">void.cx</span></div>')
rep(">AION 2</span>'));",">void.cx</span>'));")
rep("P.get('title')||'AION 2'","P.get('title')||'Enter The Void'")
rep("'Welche Klasse spielst du in AION 2?','Kantor, natürlich.','Die Flügel im Overlay sind schick'",
    "'Was spielen wir heute?','Server läuft stabil','Das schwarze Loch ist hypnotisch'")

# ---------- Farben: reine CI
rep("--aether:#BFE6FF;     /* Runenlicht */","--aether:#7C9BFF;     /* Blau-Text */")
rep("--sky:#7FC8FF;","--sky:#7C9BFF;\n  --vtext:#D27BFF;      /* Violett-Text */")
for a,b in [("#B303F8,#7FC8FF","#B303F8,#1141E4"),("#B303F8,#E6F5FF","#B303F8,#7C9BFF"),
            ("rgba(110,190,255","rgba(124,155,255"),("rgba(80,160,255","rgba(17,65,228"),("#E6F5FF","#F2F3FA"),
            ("#CFE3FF","#A3A6C2"),("#BFE6FF","#7C9BFF"),("rgba(191,230,255","rgba(210,123,255"),
            ("rgba(127,200,255","rgba(124,155,255"),("rgba(80,150,255","rgba(179,3,248")]:
    rep(a,b)

# ---------- Schriften: CI (Space Grotesk + JetBrains Mono), Tipp-Animation
rep('@font-face{font-family:"VOID Runes";src:url(data:font/woff2;base64,__RUNES__) format("woff2");font-display:block}\n@font-face{font-family:"VOID Latin";src:url(data:font/woff2;base64,__LATIN__) format("woff2");font-display:block}\n',
 '@font-face{font-family:"Space Grotesk";font-weight:700;src:url(data:font/woff2;base64,__SG7__) format("woff2");font-display:block}\n'
 '@font-face{font-family:"JetBrains Mono";font-weight:500;src:url(data:font/woff2;base64,__JB5__) format("woff2");font-display:block}\n')
t=t.replace('"VOID Latin"','"Space Grotesk"').replace("\\'VOID Latin\\'","\\'Space Grotesk\\'")
rep('.halo text{font-family:"VOID Runes";fill:var(--aether)}\n','')
rep("const FX='cipher', FXDUR=650;","const FX='type', FXDUR=700;        /* VOID: Text wird getippt wie im Terminal */")

# ---------- Himmel: Void-Schwarz mit Markenlicht
rep("""    radial-gradient(900px 700px at 8% 18%, rgba(179,3,248,.30), transparent 70%),
    radial-gradient(1000px 760px at 94% 30%, rgba(80,170,255,.26), transparent 70%),
    radial-gradient(1200px 520px at 50% 108%, rgba(17,65,228,.32), transparent 70%),
    radial-gradient(700px 500px at 50% 46%, rgba(210,123,255,.10), transparent 70%),
    linear-gradient(180deg,#080A22 0%,var(--night) 55%,#05061A 100%);}""",
"""    radial-gradient(900px 700px at 8% 12%, rgba(179,3,248,.22), transparent 70%),
    radial-gradient(1000px 760px at 96% 92%, rgba(17,65,228,.24), transparent 70%),
    #07071A;}""")
rep("@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}","@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}\n.beam{display:none}")

# ---------- Motiv: Akkretionsscheibe, reagiert auf Alerts und Chat
rep("@keyframes rise{","""/* ---------- Motiv: Ereignishorizont ---------- */
#void{position:absolute;inset:0;width:1920px;height:1080px}
.horizon{position:absolute;left:50%;top:400px;width:260px;height:260px;margin:-130px 0 0 -130px;border-radius:50%;
  background:radial-gradient(circle,#000 0 58%,rgba(7,7,26,.9) 66%,transparent 72%);box-shadow:0 0 0 2px rgba(210,123,255,.18)}
@keyframes rise{""")
rep("/* Achteck-Loch mit abgeschrägten Ecken","""/* Akkretionsscheibe auf Canvas: Teilchen kreisen um den Ereignishorizont (innen schneller),
   Farbe von Violett nach Blau über den Winkel. Alerts lösen eine Schockwelle aus, Chat schießt Teilchen hinein. */
const VOIDFX={pulse:0,spawn:0};
function motif(target){
  const cv=document.createElement('canvas');cv.id='void';cv.width=1920;cv.height=1080;target.appendChild(cv);
  target.appendChild(el('div','horizon'));
  const ctx=cv.getContext('2d'),CX=960,CY=400,TILT=.34,N=520,P=[];
  const add=(r)=>P.push({a:Math.random()*Math.PI*2,r:r||140+Math.pow(Math.random(),1.6)*520,s:.6+Math.random()*.8,z:Math.random()});
  for(let i=0;i<N;i++)add();
  const col=a=>{const f=(Math.cos(a-2.4)+1)/2;return [179+(17-179)*f,3+(65-3)*f,248+(228-248)*f]};
  let last=performance.now();
  function frame(now){
    const dt=Math.min(50,now-last)/16.7;last=now;
    ctx.globalCompositeOperation='destination-out';ctx.fillStyle='rgba(0,0,0,.18)';ctx.fillRect(0,0,1920,1080);
    ctx.globalCompositeOperation='lighter';
    const boost=1+VOIDFX.pulse*3;VOIDFX.pulse*=Math.pow(.96,dt);
    while(VOIDFX.spawn>0){VOIDFX.spawn--;for(let k=0;k<14;k++)add(700+Math.random()*120)}
    for(let i=P.length-1;i>=0;i--){const p=P[i];
      p.a+=dt*.0042*p.s*Math.pow(300/p.r,1.5)*boost;p.r-=dt*(.05+(p.r>660?1.6:0))*(1+VOIDFX.pulse*2);
      if(p.r<132){if(P.length>N)P.splice(i,1);else{p.r=560+Math.random()*120;p.a=Math.random()*6.28}continue}
      const x=CX+Math.cos(p.a)*p.r,y=CY+Math.sin(p.a)*p.r*TILT+(p.z-.5)*10,[r,g,b]=col(p.a);
      const al=Math.min(1,(p.r-130)/60)*(.35+.65*(1-p.r/760));
      ctx.fillStyle=`rgba(${r|0},${g|0},${b|0},${al.toFixed(3)})`;const sz=p.r<260?2.6:1.8;ctx.fillRect(x,y,sz,sz);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

/* Achteck-Loch mit abgeschrägten Ecken""")
rep("  sky(stage);halo(stage);wings(stage);","  sky(stage);motif(stage);")
# Reaktionen: Alerts -> Schockwelle, Chat -> neue Teilchen
rep("function pushAlert(e){if(!ALERTS||!FMT[e.type])return;","function pushAlert(e){if(FMT[e.type])VOIDFX.pulse=1;if(!ALERTS||!FMT[e.type])return;")
rep("function addChat(c){\n  if(!chatLog)return;","function addChat(c){\n  VOIDFX.spawn++;\n  if(!chatLog)return;")

# ---------- Layout: Marke im Zentrum der Scheibe, Eyebrow, Titel, Terminal-Statuszeile, Live-Zahlen
rep("  c.append(m,t,rule,st,ct);stage.appendChild(c);","""  const eb=el('div','eyebrow','// enter the void');
  c.append(m,eb,t,st,ct);stage.appendChild(c);
  onState(s=>{const C=s.counts||{},S=s.session||{},ch=document.getElementById('chips');if(!ch)return;
    const parts=[];if(C.followers!=null)parts.push(`<span class="chip"><b>${C.followers.toLocaleString('de-DE')}</b> Follower</span>`);
    if(C.subs!=null)parts.push(`<span class="chip"><b>${C.subs.toLocaleString('de-DE')}</b> Abos</span>`);
    if(S.follows&&S.follows.length)parts.push(`<span class="chip live">${S.follows.length} neu heute</span>`);
    ch.innerHTML=parts.join('')});""")

# ---------- Texte (Terminal-Ton)
rep("start:{title:'Stream startet',subs:['Client wird gepatcht','Charakter wird gewählt','Aether wird gesammelt','Kaffee steht bereit','Gleich geht’s los']}",
    "start:{title:'Stream startet',subs:['> Server fahren hoch','> Discord ist offen','> Kaffee läuft durch','> Szene wird geladen','> Gleich geht’s los']}")
rep("pause:{title:'Kurze Pause',subs:()=>['Bin gleich zurück','Chat bleibt offen',...latestLines(),'Kurz Aether tanken']}",
    "pause:{title:'Kurze Pause',subs:()=>['> Bin gleich zurück','> Chat bleibt offen',...latestLines().map(l=>'> '+l)]}")

# ---------- Typografie, Tipp-Effekt, Chips
rep("@media (prefers-reduced-motion:reduce)","""/* ---------- VOID: Typografie nach Manual ---------- */
.fx{position:relative;display:inline-block;clip-path:inset(-20% 100% -20% 0)}
.fx.in{animation:fxType calc(var(--n)*45ms + 120ms) steps(var(--n),end) forwards}
.fx.out{clip-path:inset(-20% 0 -20% 0);animation:fxErase .28s steps(6,end) forwards}
@keyframes fxType{to{clip-path:inset(-20% 0 -20% 0)}}
@keyframes fxErase{to{clip-path:inset(-20% 0 -20% 100%)}}
.center{justify-content:flex-start;padding-top:325px}
.vmark.mark{width:150px;margin-bottom:96px}
.eyebrow{font-family:"JetBrains Mono";font-weight:500;font-size:22px;color:var(--vtext);margin-bottom:18px;opacity:0;animation:appear .8s 1s forwards}
.title{font-weight:700;font-size:112px;letter-spacing:-.01em;line-height:1.02;color:#F2F3FA;text-shadow:0 0 40px rgba(179,3,248,.25)}
.status{font-family:"JetBrains Mono";font-weight:500;font-size:28px;color:#A3A6C2;margin-top:26px;text-shadow:none;letter-spacing:0}
.status::after{content:"_";color:var(--vtext);animation:blink 1s steps(1) infinite;margin-left:4px}
@keyframes blink{50%{opacity:0}}
.rule{display:none}
.head .title{font-size:60px;letter-spacing:-.01em}
.plate .title{font-size:20px;letter-spacing:.02em}
.a-name{font-weight:700;font-size:60px;letter-spacing:-.01em;color:#F2F3FA}
.a-detail{font-family:"JetBrains Mono";font-weight:500;font-size:22px;letter-spacing:0;color:var(--vtext)}
.m-name{font-weight:700;font-size:17px;letter-spacing:0}
.g-v{font-family:"JetBrains Mono";font-size:14px;letter-spacing:0}
.chips{gap:12px!important}
.chip{padding:8px 14px;border-radius:6px;background:#0F1024;border:1px solid #262947;font-size:18px;color:#A3A6C2}
.chip b{color:#F2F3FA;font-weight:700;margin-right:4px}
.chip.live{color:#F2F3FA}
.chip.live::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:#7C9BFF;margin-right:8px;vertical-align:1px}

/* STINGER-CSS-START */
/* STINGER-CSS-END */

@media (prefers-reduced-motion:reduce)""")

# ---------- Stinger: schwarzes Loch reißt auf, Marke baut sich auf, Kollaps in einen Punkt
t=re.sub(r'/\* STINGER-CSS-START \*/.*?/\* STINGER-CSS-END \*/','',t,count=1,flags=re.S)
t=re.sub(r'/\* STINGER-CSS-START \*/.*?/\* STINGER-CSS-END \*/',lambda m:'''/* STINGER-CSS-START */
.bh{position:absolute;left:50%;top:50%;width:2400px;height:2400px;margin:-1200px 0 0 -1200px;border-radius:50%;will-change:transform;
  background:radial-gradient(circle,#000 0 40%,#07071A 60%,#07071A 97%,rgba(7,7,26,0) 100%);animation:bhOpen 1.95s both}
@keyframes bhOpen{0%{transform:scale(0);animation-timing-function:cubic-bezier(.6,0,.2,1)}25%{transform:scale(1)}
  74%{transform:scale(1);animation-timing-function:cubic-bezier(.7,0,.9,.4)}100%{transform:scale(0)}}
.bh-ring{position:absolute;left:50%;top:50%;width:1000px;height:1000px;margin:-500px 0 0 -500px;border-radius:50%;
  background:conic-gradient(from 0deg,#B303F8,#1141E4,#7C9BFF,#B303F8,#1141E4,#D27BFF,#B303F8);
  -webkit-mask:radial-gradient(circle,transparent 0 46%,#000 47% 49%,transparent 52%);mask:radial-gradient(circle,transparent 0 46%,#000 47% 49%,transparent 52%);
  animation:bhRing 1.95s both}
@keyframes bhRing{0%{transform:scale(0) rotate(0);opacity:0}8%{opacity:1}25%{transform:scale(1.9) rotate(200deg)}
  74%{transform:scale(1.9) rotate(560deg);opacity:1}100%{transform:scale(0) rotate(900deg);opacity:0}}
.bh-glow{position:absolute;inset:0;background:radial-gradient(circle at 50% 50%,rgba(179,3,248,.35),rgba(17,65,228,.15) 30%,transparent 55%);opacity:0;animation:bhGlow 1.95s both}
@keyframes bhGlow{0%,20%{opacity:0}35%,72%{opacity:1}90%,100%{opacity:0}}
/* STINGER-CSS-END */''',t,count=1,flags=re.S)
t=re.sub(r'/\* STINGER-THEME-START \*/.*?/\* STINGER-THEME-END \*/',lambda m:'''/* STINGER-THEME-START */
/* VOID: ein schwarzes Loch reißt aus der Mitte auf, ein Ring im Markenverlauf rotiert am Rand,
   die Bildmarke baut sich auf, dann kollabiert alles zurück in einen Punkt */
function stingerTheme(root){root.append(el('div','bh'),el('div','bh-glow'),el('div','bh-ring'))}
function stingerMark(m,root){m.style.zIndex=5}
/* STINGER-THEME-END */''',t,flags=re.S)
open('tpl_void.html','w').write(t)
print('ok, AION übrig:',len(re.findall('AION',t)))
