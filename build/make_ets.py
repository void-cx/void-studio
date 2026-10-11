import re
t=open('tpl.html').read()
def rep(a,b):
    global t
    assert a in t, a[:90]; t=t.replace(a,b)

# ---------- Namen
rep("VOID × AION 2 · OBS-Szenenset","VOID × EURO TRUCK SIMULATOR 2 · OBS-Szenenset")
rep("  ?scene=game      AION 2 Game           transparentes Overlay, Kamera UNTER diese Quelle legen",
    "  ?scene=game      ETS2 Fahrt            transparentes Overlay, Kamera UNTER diese Quelle legen\n"
    "  ?scene=drive     ETS2 Telemetrie       Rahmen mit Spielbild-Loch (x 24 y 24 1472 × 828), Kamera (x 1520 y 24 376 × 212),\n"
    "                                        Route, Ladung, Tempo, Tank, Ruhezeit – Daten über die Bridge (Telemetry-Server nötig)")
rep("<title>VOID × AION 2 · Szenen</title>","<title>VOID × ETS2 · Szenen</title>")
rep('<span class="aion">AION 2</span>','<span class="aion">Euro Truck Simulator 2</span>')
rep(">AION 2</span>'));",">ETS2</span>'));")
rep("P.get('title')||'AION 2'","P.get('title')||'ETS2'")
rep("'Welche Klasse spielst du in AION 2?','Kantor, natürlich.','Die Flügel im Overlay sind schick'",
    "'Wohin geht die Fuhre?','Blinker nicht vergessen!','Das Schild im Overlay ist schick'")

# ---------- Farben: Wegweiser-Blau + Signalgelb
rep("--aether:#BFE6FF;     /* Runenlicht */","--aether:#FFD86B;     /* Signalgelb hell */")
rep("--sky:#7FC8FF;","--sky:#FFC20E;        /* Signalgelb */\n  --sign:#00519E;       /* Wegweiser-Blau */\n  --s1:#05071A;--s2:#0B1433;--s3:#1A2547;--night:1;")
for a,b in [("#B303F8,#7FC8FF","#E0A100,#FFC20E"),("#B303F8,#E6F5FF","#FFC20E,#FFF1B8"),
            ("rgba(110,190,255","rgba(255,200,80"),("rgba(80,160,255","rgba(255,170,40"),("#E6F5FF","#FFFFFF"),
            ("#CFE3FF","#F3F0E6"),("#BFE6FF","#FFD86B"),("rgba(191,230,255","rgba(255,230,170"),
            ("rgba(127,200,255","rgba(255,200,80"),("rgba(80,150,255","rgba(255,200,80")]:
    rep(a,b)

# ---------- Schriften: Barlow (DIN-artig wie Wegweiser), Fallblatt-Effekt
rep('@font-face{font-family:"VOID Runes";src:url(data:font/woff2;base64,__RUNES__) format("woff2");font-display:block}\n@font-face{font-family:"VOID Latin";src:url(data:font/woff2;base64,__LATIN__) format("woff2");font-display:block}\n',
 '@font-face{font-family:"Barlow";font-weight:500;src:url(data:font/woff2;base64,__BW5__) format("woff2");font-display:block}\n'
 '@font-face{font-family:"Barlow";font-weight:700;src:url(data:font/woff2;base64,__BW7__) format("woff2");font-display:block}\n'
 '@font-face{font-family:"JetBrains Mono";font-weight:500;src:url(data:font/woff2;base64,__JB5__) format("woff2");font-display:block}\n')
rep('font-family:"VOID Runes";font-weight:400;','font-family:"Barlow";font-weight:700;')
t=t.replace('"VOID Latin"','"Barlow"').replace("\\'VOID Latin\\'","\\'Barlow\\'")
rep('.halo text{font-family:"VOID Runes";fill:var(--aether)}\n','')
rep("rastet Buchstabe für Buchstabe in VOID Latin ein.","rastet Buchstabe für Buchstabe ein (wie eine Fallblattanzeige).")
rep("const POOL='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';","const POOL='ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ0123456789';")
rep("const glyph=c=>KEY&&RUNESET.has(c.toUpperCase())?c:rr();","const glyph=c=>rr();             /* ETS2: Fallblatt-Zeichen, kein Runen-Schlüssel */")

# ---------- Dynamischer Himmel (Spieluhr oder echte Uhr)
rep("""    radial-gradient(900px 700px at 8% 18%, rgba(179,3,248,.30), transparent 70%),
    radial-gradient(1000px 760px at 94% 30%, rgba(80,170,255,.26), transparent 70%),
    radial-gradient(1200px 520px at 50% 108%, rgba(17,65,228,.32), transparent 70%),
    radial-gradient(700px 500px at 50% 46%, rgba(255,230,170,.10), transparent 70%),
    linear-gradient(180deg,#080A22 0%,var(--night) 55%,#05061A 100%);}""",
"""    radial-gradient(900px 600px at 6% 8%, rgba(179,3,248,calc(.18*var(--night))), transparent 70%),
    linear-gradient(180deg,var(--s1) 0%,var(--s2) 45%,var(--s3) 62%,#0B0D14 62.2%,#0B0D14 100%);
  transition:background 4s}""")
rep("@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}","@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}\n.beam{display:none}\n.motes{opacity:calc(.6*var(--night))}")
rep("const d=el('div','mote'+(Math.random()<.35?' v':''));const s=rnd(3,8);","const d=el('div','mote'+(Math.random()<.2?' v':''));const s=rnd(2,4);")

rep("@keyframes rise{","""/* ---------- Motiv: Autobahn mit Wegweiser ---------- */
.stars{position:absolute;inset:0 0 40% 0;opacity:var(--night);transition:opacity 4s}
.stars i{position:absolute;width:2px;height:2px;background:#fff;border-radius:50%}
.hills{position:absolute;left:0;top:520px;width:1920px;height:160px}
.road{position:absolute;left:0;right:0;top:668px;bottom:0;perspective:360px;perspective-origin:50% 0;overflow:hidden}
.plane{position:absolute;left:50%;bottom:-120px;width:1500px;margin-left:-750px;height:2600px;transform-origin:50% 100%;transform:rotateX(81deg);
  background:linear-gradient(180deg,#14161C,#272A33)}
.plane .ln{position:absolute;top:-300px;height:3000px;width:14px;will-change:transform;animation:dash .5s linear infinite;
  background:repeating-linear-gradient(180deg,rgba(240,236,220,.85) 0 110px,transparent 110px 300px)}
.plane .ln.a{left:500px}.plane .ln.b{left:986px}
.plane .ed{position:absolute;top:0;bottom:0;width:14px;background:rgba(240,236,220,.7)}
.plane .ed.l{left:30px}.plane .ed.r{right:30px}
@keyframes dash{to{transform:translateY(300px)}}
.headlights{position:absolute;left:0;right:0;bottom:0;height:420px;background:radial-gradient(60% 100% at 50% 100%,rgba(255,230,160,calc(.22*var(--night))),transparent 70%)}
.sign{position:relative;display:flex;align-items:center;gap:44px;background:var(--sign);border:8px solid #fff;outline:6px solid var(--sign);
  border-radius:20px;padding:34px 70px 34px 40px;box-shadow:0 34px 70px rgba(0,0,0,.5);text-align:left;margin-top:-90px;z-index:1}
.sign::before,.sign::after{content:"";position:absolute;top:calc(100% + 14px);width:26px;height:520px;z-index:-1;
  background:linear-gradient(90deg,#3A3F4B,#6B7280 45%,#2A2E38)}
.sign::before{left:18%}.sign::after{right:18%}
.shield{width:176px;height:176px;background:#fff;border-radius:16px;display:flex;align-items:center;justify-content:center;flex:none}
.shield .vmark.mark{width:128px;margin:0}
.sign-txt{display:flex;flex-direction:column;gap:16px;align-items:flex-start}
.sign .title{font-size:112px;color:#fff;text-shadow:none;letter-spacing:.005em;line-height:1}
.sign .status{font-size:40px;color:#fff;text-shadow:none;letter-spacing:.01em;min-height:44px}
.sign .arrow{width:84px;height:110px;flex:none;margin-left:10px}
@keyframes rise{""")

rep("/* Achteck-Loch mit abgeschrägten Ecken","""/* Himmel nach Tageszeit: Spieluhr aus der Telemetrie, sonst echte Uhr */
const SKY=[[0,'#03050F','#070C22','#101A33',1],[5,'#0A0F2A','#3B2F5C','#C77A5A',.6],[7,'#3D6FB3','#8FB6E0','#F2D3A2',.1],
  [10,'#2E6FC2','#6FA6E3','#B9D8F2',0],[17,'#2B5FA8','#7E9FD0','#F0C38E',.05],[19,'#1B1F4A','#6B3F6E','#E58A55',.5],[21,'#05071A','#0B1433','#1A2547',1],[24,'#03050F','#070C22','#101A33',1]];
let skyHour=-1;
function applySky(h){
  if(Math.abs(h-skyHour)<.05)return;skyHour=h;
  let i=0;while(SKY[i+1][0]<=h)i++;const a=SKY[i],b=SKY[i+1],f=(h-a[0])/(b[0]-a[0]);
  const mix=(x,y)=>'#'+[1,3,5].map(k=>Math.round(parseInt(x.substr(k,2),16)*(1-f)+parseInt(y.substr(k,2),16)*f).toString(16).padStart(2,'0')).join('');
  const r=document.documentElement.style;r.setProperty('--s1',mix(a[1],b[1]));r.setProperty('--s2',mix(a[2],b[2]));r.setProperty('--s3',mix(a[3],b[3]));
  r.setProperty('--night',(a[4]*(1-f)+b[4]*f).toFixed(2));
}
function localSky(){if(!TELE||!TELE.time){const d=new Date();applySky(d.getHours()+d.getMinutes()/60)}}

/* Autobahn bei Nacht (oder Tag): Sterne, Hügel, Straße mit laufenden Markierungen */
function motif(target){
  const st=el('div','stars');for(let i=0;i<90;i++){const s=el('i');s.style.cssText=`left:${(i*211)%1920}px;top:${(i*97)%420}px;opacity:${.3+(i%4)*.18}`;st.appendChild(s)}
  target.appendChild(st);
  let d='M0,160';for(let x=0;x<=1920;x+=40)d+=` L${x},${(110-50*Math.sin(x/1920*Math.PI*3+.6)-25*Math.sin(x/1920*Math.PI*9)).toFixed(0)}`;
  const h=el('div','hills');h.innerHTML=`<svg width="1920" height="160"><path d="${d} L1920,160Z" fill="#0A0E1A" opacity=".9"/></svg>`;target.appendChild(h);
  const road=el('div','road'),pl=el('div','plane');pl.innerHTML='<i class="ed l"></i><i class="ed r"></i><i class="ln a"></i><i class="ln b"></i>';
  road.appendChild(pl);target.appendChild(road);target.appendChild(el('div','headlights'));
}

/* Achteck-Loch mit abgeschrägten Ecken""")
rep("  sky(stage);halo(stage);wings(stage);","  sky(stage);motif(stage);localSky();setInterval(localSky,60000);")
# Titel auf den Wegweiser
rep("  c.append(m,t,rule,st,ct);stage.appendChild(c);","""  const sign=el('div','sign'),shield=el('div','shield'),txt=el('div','sign-txt');
  shield.appendChild(m);txt.append(t,st);
  sign.append(shield,txt,el('div','arrow','<svg viewBox="0 0 84 110"><path d="M42 4 L80 46 L54 46 L54 106 L30 106 L30 46 L4 46Z" fill="#fff"/></svg>'));
  c.append(sign,ct);stage.appendChild(c);""")

# ---------- Texte
rep("start:{title:'Stream startet',subs:['Client wird gepatcht','Charakter wird gewählt','Aether wird gesammelt','Kaffee steht bereit','Gleich geht’s los']}",
    "start:{title:'Stream startet',subs:['Auflieger wird angekuppelt','Route wird berechnet','Spiegel werden eingestellt','Kaffee für die Fahrt','Gleich geht’s los']}")
rep("pause:{title:'Kurze Pause',subs:()=>['Bin gleich zurück','Chat bleibt offen',...latestLines(),'Kurz Aether tanken']}",
    "pause:{title:'Kurze Pause',subs:()=>['Pause am Rastplatz','Kurz tanken',...latestLines(),'Lenkzeit wird zurückgesetzt','Bin gleich zurück']}")
rep("follow:e=>['Neuer Follow','Danke fürs Folgen'],","follow:e=>['Neuer Follow','ist zugestiegen'],")
rep("sub:   e=>['Neues Abo',(e.tier?`Stufe ${e.tier}`:'')],","sub:   e=>['Neues Abo',`fährt jetzt im Konvoi${tier(e.tier)}`],")
rep("resub: e=>['Abo verlängert',`${e.months} Monate${tier(e.tier)}`],","resub: e=>['Abo verlängert',`${e.months} Monate im Konvoi${tier(e.tier)}`],")
rep("gift:  e=>[e.amount>1?'Abos verschenkt':'Abo verschenkt',`${e.amount} ${e.amount>1?'Abos':'Abo'}${tier(e.tier)}`],",
    "gift:  e=>[e.amount>1?'Abos verschenkt':'Abo verschenkt',`${e.amount} ${e.amount>1?'Abos':'Abo'} geladen${tier(e.tier)}`],")
rep("cheer: e=>['Bits',`${e.amount} Bits`],","cheer: e=>['Bits',`${e.amount} Bits für den Tank`],")
rep("raid:  e=>['Raid',`mit ${e.amount} ${e.amount==1?'Person':'Leuten'}`],","raid:  e=>['Raid',`Konvoi mit ${e.amount} ${e.amount==1?'Person':'Leuten'}`],")

# ---------- Klang: kurzes Zweiton-Horn
rep("const base={follow:523.25,","const base={follow:233.08,")
rep("sub:440,resub:440,gift:392,cheer:587.33,raid:329.63,redeem:493.88}","sub:207.65,resub:207.65,gift:196,cheer:261.63,raid:174.61,redeem:220}")
rep("[[ 'sine',1,.5],['triangle',.5,.18]]","[['sawtooth',1,.16],['square',2,.05]]")
rep("const t=t0+i*.11;","const t=t0+i*.015;")
rep("e.gain.exponentialRampToValueAtTime(.0001,t+1.8);o.connect(e).connect(out);o.start(t);o.stop(t+1.9)",
    "e.gain.setValueAtTime(g,t+.38);e.gain.exponentialRampToValueAtTime(.0001,t+.6);o.connect(e).connect(out);o.start(t);o.stop(t+.65)")
rep("const steps={raid:[1,1.26,1.5,2,2.52],gift:[1,1.5,2,2.52],cheer:[1,1.26,1.5,2]}[type]||[1,1.5,2];","const steps=[1,1.26,1.5];")
open('tpl_ets2.html','w').write(t)
print('Teil 1 ok')

# ===== Teil 2: Typografie, Schild-Alerts, Telemetrie, Telemetrie-Szene, Stinger =====
t=open('tpl_ets2.html').read()
rep("@media (prefers-reduced-motion:reduce)","""/* ---------- ETS2-Typografie, Alerts als Wegweiser ---------- */
.fx{display:inline-block;opacity:0;transform:translateY(.4em)}
.fx.in{animation:fxUp .55s cubic-bezier(.2,.8,.2,1) forwards}
.fx.out{opacity:1;transform:none;animation:fxDown .3s ease-in forwards}
@keyframes fxUp{to{opacity:1;transform:none}}
@keyframes fxDown{to{opacity:0;transform:translateY(-.35em)}}

.title{font-weight:700}
.status{font-weight:500}
.head .title{font-size:64px;color:#fff}
.plate .title{font-size:22px}
.a-name{font-weight:700;font-size:62px;letter-spacing:.005em;color:#fff;text-shadow:none}
.a-detail{font-weight:500;font-size:28px;letter-spacing:.01em;color:#FFD86B}
.foot .aion{font-weight:700;letter-spacing:.01em}
.m-name{font-weight:700;font-size:19px;letter-spacing:.01em}
.g-v{font-family:"JetBrains Mono";font-size:14px;letter-spacing:0}
.ch .rn{font-size:1em;top:0;color:#FFD86B;text-shadow:none}
.ch.v .rn{color:#FFE9A8}
.ch.flick .rn{color:#fff}
.alert{clip-path:none;background:#fff;border-radius:18px;padding:6px}
.alert .body{clip-path:none;border-radius:13px;background:var(--sign)}
.a-kind{color:rgba(255,255,255,.82)}
.goal{clip-path:none;border-radius:10px;background:rgba(0,40,90,.85)}
.plate{clip-path:none;border-radius:10px;background:var(--sign);border:3px solid #fff}

/* ---------- Telemetrie-Szene ---------- */
.tl-col{position:absolute;left:1520px;top:252px;width:376px;height:600px;display:flex;flex-direction:column;gap:14px}
.tl-box{background:rgba(5,10,30,.82);border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:14px 18px}
.tl-lbl{font-size:14px;color:var(--mist);letter-spacing:.02em}
.tl-val{font-family:"Barlow";font-weight:700;font-size:30px;color:#fff;line-height:1.15;font-variant-numeric:tabular-nums}
.tl-speed{display:flex;align-items:center;justify-content:space-between}
.tl-speed .tl-val{font-size:92px;line-height:.95}
.tl-speed small{font-family:"Barlow";font-weight:500;font-size:24px;color:var(--mist);margin-left:8px}
.limit{width:92px;height:92px;border-radius:50%;background:#fff;border:11px solid #D9261C;display:flex;align-items:center;justify-content:center;
  font-family:"Barlow";font-weight:700;font-size:36px;color:#111;transition:opacity .4s}
.limit.off{opacity:0}
.tl-two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.fuel{height:8px;border-radius:4px;background:rgba(255,255,255,.12);margin-top:10px;overflow:hidden}
.fuel i{display:block;height:100%;width:100%;transform-origin:0 50%;background:linear-gradient(90deg,#E0A100,#FFC20E);transition:transform 1s}
.fuel.low i{background:#D9261C}
.tl-brand{margin-top:auto;display:flex;justify-content:center;opacity:.9}
.tl-col .goal{padding:7px 14px 9px}
.tl-col:has(.goals:not(.empty)) .tl-brand{display:none}
.tl-col:has(.goals:not(.empty)) .tl-truckbox{display:none}
.tl-col:has(.lt-list:not(.empty)):has(.goals:not(.lt-list):not(.empty)) .tl-two:nth-of-type(3){display:none}
.tl-brand img{height:44px}
.tl-route{position:absolute;left:24px;top:876px;width:1872px;height:180px;display:grid;grid-template-columns:420px 1fr 420px;grid-template-rows:1fr auto;
  column-gap:36px;align-items:center;background:var(--sign);border:6px solid #fff;border-radius:18px;padding:14px 34px 16px}
.tl-city{font-family:"Barlow";font-weight:700;font-size:44px;color:#fff;line-height:1.05;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tl-comp{font-size:18px;color:rgba(255,255,255,.75);margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tl-end{text-align:right}
.tl-track{position:relative;height:6px;border-radius:3px;background:rgba(255,255,255,.25)}
.tl-track b{position:absolute;inset:0;border-radius:3px;background:#FFC20E;transform-origin:0 50%;transform:scaleX(var(--p,0));transition:transform 1s}
.tl-truck{position:absolute;top:50%;left:calc(var(--p,0)*100%);width:58px;height:30px;margin:-30px 0 0 -29px;transition:left 1s}
.tl-mid{display:flex;flex-direction:column;gap:30px}
.tl-dist{display:flex;justify-content:space-between;font-family:"Barlow";font-weight:700;font-size:26px;color:#fff}
.tl-dist span{font-weight:500;color:rgba(255,255,255,.75)}
.tl-cargo{grid-column:1/-1;display:flex;gap:34px;font-size:19px;color:rgba(255,255,255,.85);border-top:1px solid rgba(255,255,255,.25);padding-top:10px}
.tl-cargo b{font-family:"Barlow";font-weight:700;color:#FFD86B;margin-left:8px}
.tl-off{position:absolute;left:24px;top:24px;width:1472px;height:828px;display:flex;align-items:center;justify-content:center;pointer-events:none;opacity:0;transition:opacity .5s}
.tl-off.on{opacity:1}
.tl-off span{background:rgba(5,10,30,.85);border:2px solid #FFC20E;border-radius:12px;padding:16px 26px;font-size:22px;color:#fff}

/* STINGER-CSS-START */
/* STINGER-CSS-END */

@media (prefers-reduced-motion:reduce)""")

# Stinger: VOID-Sattelzug fährt formatfüllend durchs Bild
t=re.sub(r'/\\* STINGER-CSS-START \\*/.*?/\\* STINGER-CSS-END \\*/','',t,count=1,flags=re.S) if False else t
t=re.sub(r'/\* STINGER-CSS-START \*/.*?/\* STINGER-CSS-END \*/','',t,count=1,flags=re.S)   # alte AION-Regeln raus
t=re.sub(r'/\* STINGER-CSS-START \*/.*?/\* STINGER-CSS-END \*/',lambda m:'''/* STINGER-CSS-START */
.tk{position:absolute;left:0;top:0;width:5600px;height:1080px;will-change:transform;animation:tkMove 1.95s both}
@keyframes tkMove{0%{transform:translateX(1920px);animation-timing-function:cubic-bezier(.4,0,.6,1)}
  25%{transform:translateX(-1000px);animation-timing-function:linear}74%{transform:translateX(-2700px);animation-timing-function:cubic-bezier(.4,0,.6,1)}
  100%{transform:translateX(-5650px)}}
.tk>*{position:absolute;top:0;height:1080px}
.tk-cab{left:0;width:900px;border-radius:220px 0 0 0;background:linear-gradient(180deg,#2B1650 0%,#1A0F38 55%,#120A26 100%)}
.tk-win{position:absolute;left:150px;top:90px;width:560px;height:330px;border-radius:120px 20px 20px 20px;
  background:linear-gradient(160deg,rgba(150,180,255,.35),rgba(20,25,60,.9) 60%);border:10px solid #0B0718}
.tk-door{position:absolute;left:120px;top:470px;width:640px;height:520px;border:6px solid rgba(255,255,255,.08);border-radius:18px}
.tk-light{position:absolute;left:20px;top:820px;width:120px;height:70px;border-radius:30px;background:#FFE7A3;box-shadow:0 0 80px 30px rgba(255,210,120,.55)}
.tk-gap{left:900px;width:40px;background:#05050C}
.tk-trl{left:940px;width:3800px;background:
  linear-gradient(180deg,#2A2E3A 0 70px,transparent 70px calc(100% - 150px),#1C1F28 calc(100% - 150px)),
  repeating-linear-gradient(90deg,#0F1024 0 46px,#141633 46px 86px,#0C0D1E 86px 92px)}
.tk-stripe{position:absolute;left:0;right:0;top:820px;height:26px;background:linear-gradient(90deg,#B303F8,#1141E4)}
.tk-brand{position:absolute;left:1500px;top:250px;width:1000px;text-align:center}
.tk-brand .vmark{width:420px;margin:0 auto}
.tk-brand p{margin-top:34px;font-family:"Barlow";font-weight:700;font-size:96px;color:#fff;letter-spacing:.02em}
.tk-wheel{position:absolute;top:960px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,#555 0 18%,#222 19% 52%,#0A0A0A 53%)}
.tk-tail{left:4740px;width:70px;background:#15161D}
.tk-tail i{position:absolute;left:10px;top:860px;width:46px;height:110px;background:#E3201B;box-shadow:0 0 60px 18px rgba(227,32,27,.6)}
.tk-blur{position:absolute;inset:0;background:repeating-linear-gradient(90deg,rgba(255,255,255,.035) 0 2px,transparent 2px 160px);mix-blend-mode:screen}
/* STINGER-CSS-END */''',t,count=1,flags=re.S)
t=re.sub(r'/\* STINGER-THEME-START \*/.*?/\* STINGER-THEME-END \*/',lambda m:'''/* STINGER-THEME-START */
/* ETS2: ein VOID-Sattelzug fährt formatfüllend durchs Bild, die Bildmarke baut sich auf der Plane auf */
function stingerTheme(root){
  const k=el('div','tk');
  k.innerHTML=`<div class="tk-cab"><i class="tk-win"></i><i class="tk-door"></i><i class="tk-light"></i><i class="tk-wheel" style="left:300px"></i></div><div class="tk-gap"></div>
    <div class="tk-trl"><i class="tk-stripe"></i><div class="tk-brand"><p>void.cx</p></div>
      ${[2900,3160,3420].map(x=>`<i class="tk-wheel" style="left:${x}px"></i>`).join('')}<i class="tk-blur"></i></div>
    <div class="tk-tail"><i></i></div>`;
  root.appendChild(k);
}
function stingerMark(m,root){            /* Marke sitzt auf der Plane und fährt mit */
  m.classList.remove('st-mark');m.style.cssText='width:420px;margin:0 auto';m.style.setProperty('--d','420ms');m.style.setProperty('--t','450ms');
  const b=root.querySelector('.tk-brand');b.insertBefore(m,b.firstChild);
}
/* STINGER-THEME-END */''',t,flags=re.S)

# Telemetrie: normalisieren (Funbit-Format und RenCloud/scs-telemetry-json-service), Testdaten
rep("/* ---------- Verbindung zur Bridge ---------- */","""/* ---------- Spiel-Telemetrie (ETS2/ATS) ---------- */
let TELE=null;const teleHooks=[];
const iso2min=s=>s?(Date.parse(s)-Date.parse('0001-01-01T00:00:00Z'))/60000:null;
function normTele(r){
  if(!r)return null;
  const g=(...ps)=>{for(const p of ps){let v=r;for(const k of p.split('.')){if(v==null)break;v=v[k]}if(v!=null&&v!=='')return v}return null};
  const fb=!!r.game;
  if(fb&&g('game.connected')===false)return null;
  return {
    time:fb?iso2min(g('game.time')):g('CommonValues.GameTime.Value'),
    speed:Math.abs(+g('truck.speed','TruckValues.CurrentValues.DashboardValues.Speed.Kph')||0),
    limit:+g('navigation.speedLimit','NavigationValues.SpeedLimit.Kph')||0,
    gear:g('truck.displayedGear','truck.gear','TruckValues.CurrentValues.DashboardValues.GearDashboards'),
    fuel:+g('truck.fuel','TruckValues.CurrentValues.DashboardValues.FuelValue.Amount')||0,
    fuelCap:+g('truck.fuelCapacity','TruckValues.ConstantsValues.CapacityValues.Fuel')||0,
    truck:[g('truck.make','TruckValues.ConstantsValues.Brand'),g('truck.model','TruckValues.ConstantsValues.Name')].filter(Boolean).join(' '),
    src:g('job.sourceCity','JobValues.CitySource')||'',srcCo:g('job.sourceCompany','JobValues.CompanySource')||'',
    dst:g('job.destinationCity','JobValues.CityDestination')||'',dstCo:g('job.destinationCompany','JobValues.CompanyDestination')||'',
    cargo:g('cargo.cargo','trailer.name','job.cargo','JobValues.CargoValues.Name')||'',
    mass:+g('cargo.mass','trailer.mass','JobValues.CargoValues.Mass')||0,
    income:+g('job.income','JobValues.Income')||0,
    dist:+g('navigation.estimatedDistance','NavigationValues.NavigationDistance')||0,
    eta:fb?iso2min(g('navigation.estimatedTime')):(+g('NavigationValues.NavigationTime')||0)/60,
    rest:fb?iso2min(g('game.nextRestStopTime')):g('CommonValues.NextRestStop.Value'),
  };
}
function setTele(raw){TELE=normTele(raw);if(TELE&&TELE.time!=null)applySky((TELE.time%1440)/60);teleHooks.forEach(f=>f(TELE))}
function fakeTele(){            /* Testdaten im Funbit-Format */
  let k=0;const job={sourceCity:'Neuss',sourceCompany:'VOID Logistik',destinationCity:'Rotterdam',destinationCompany:'Hafen Maasvlakte',income:8450};
  setInterval(()=>{k++;const m=7*1440+21*60+k;
    const iso=x=>new Date(Date.parse('0001-01-01T00:00:00Z')+x*60000).toISOString().replace('.000','');
    setTele({game:{connected:true,time:iso(m),nextRestStopTime:iso(252-k%60)},truck:{make:'VOID',model:'Nightliner',speed:80+6*Math.sin(k/7),
      displayedGear:12,fuel:620-k*.4,fuelCapacity:800,odometer:120000+k},job,cargo:{cargo:'Server-Racks',mass:12400},
      navigation:{estimatedDistance:Math.max(0,212000-k*350),estimatedTime:iso(Math.max(0,190-k*.3)),speedLimit:k%40<25?80:100}})},400);
}

/* ---------- Verbindung zur Bridge ---------- */""")
rep("    case 'control':if(e.action==='skip'&&skipNow)skipNow();break;","    case 'control':if(e.action==='skip'&&skipNow)skipNow();break;\n    case 'telemetry':setTele(e.data);break;")
rep("  if(TEST)testMode();","  if(TEST){testMode();fakeTele()}")

# Telemetrie-Szene
rep("function game(){","""function drive(){
  const g={x:24,y:24,w:1472,h:828,c:14},cam={x:1520,y:24,w:376,h:212,c:12};
  if(DEMO){[[g,'Spielbild'],[cam,'Kamera']].forEach(([r,n])=>{const d=el('div','demo',n);Object.assign(d.style,{left:r.x+'px',top:r.y+'px',width:r.w+'px',height:r.h+'px'});stage.appendChild(d)})}
  const mat=el('div','matte');mat.style.clipPath=holes(1920,1080,[g,cam]);sky(mat);stage.appendChild(mat);
  frameSVG(stage,[g,cam]);
  const col=el('div','tl-col');col.innerHTML=`
    <div class="tl-box tl-speed"><div><div class="tl-lbl">Tempo</div><div class="tl-val"><span id="sp">–</span><small>km/h</small></div></div><div class="limit off" id="lim"></div></div>
    <div class="tl-two"><div class="tl-box"><div class="tl-lbl">Gang</div><div class="tl-val" id="gr">–</div></div>
      <div class="tl-box"><div class="tl-lbl">Tank</div><div class="tl-val" id="fu">–</div><div class="fuel" id="fb"><i></i></div></div></div>
    <div class="tl-two"><div class="tl-box"><div class="tl-lbl">Spielzeit</div><div class="tl-val" id="ck">–</div></div>
      <div class="tl-box"><div class="tl-lbl">Ruhepause in</div><div class="tl-val" id="rs">–</div></div></div>
    <div class="tl-box tl-truckbox"><div class="tl-lbl">Zugmaschine</div><div class="tl-val" id="tr" style="font-size:24px">–</div></div>
    <div class="tl-brand"><img src="${LOCKUP}" alt="Enter The Void"></div>`;
  stage.appendChild(col);
  const lb=el('div','goals stack lt-list empty');lb.style.cssText='position:static;gap:8px';   /* letzte Unterstützer */
  const gb=el('div','goals stack empty');gb.style.cssText='position:static;gap:8px';            /* Ziele der Bridge */
  col.insertBefore(lb,col.querySelector('.tl-brand'));col.insertBefore(gb,col.querySelector('.tl-brand'));latestInto(lb,{max:2});goalsInto(gb);
  const rt=el('div','tl-route');rt.innerHTML=`
    <div><div class="tl-city" id="sc">–</div><div class="tl-comp" id="so"></div></div>
    <div class="tl-mid"><div class="tl-dist"><b id="ds">–</b><span id="et"></span></div>
      <div class="tl-track"><b></b><svg class="tl-truck" viewBox="0 0 58 30"><rect x="0" y="2" width="38" height="20" rx="3" fill="#fff"/><path d="M40 8h10l6 7v7H40z" fill="#FFC20E"/>
        <circle cx="10" cy="25" r="4" fill="#0B1433" stroke="#fff" stroke-width="2"/><circle cx="46" cy="25" r="4" fill="#0B1433" stroke="#fff" stroke-width="2"/></svg></div></div>
    <div class="tl-end"><div class="tl-city" id="dc">–</div><div class="tl-comp" id="do"></div></div>
    <div class="tl-cargo"><span>Ladung<b id="cg">–</b></span><span>Gewicht<b id="ms">–</b></span><span>Lohn<b id="in">–</b></span><span>Heute gefahren<b id="km">–</b></span></div>`;
  stage.appendChild(rt);
  const off=el('div','tl-off on','<span>Telemetrie offline · Telemetry-Server starten und in der Bridge aktivieren</span>');stage.appendChild(off);
  const $=id=>document.getElementById(id);
  const hm=m=>m==null||m<0?'–':`${Math.floor(m/60)}:${String(Math.round(m%60)).padStart(2,'0')} h`;
  const DAYS=['Mo','Di','Mi','Do','Fr','Sa','So'];
  const C={sc:new Cipher($('sc'),{stagger:40,shuffle:380}),dc:new Cipher($('dc'),{stagger:40,shuffle:380})};
  let job='',maxDist=0;
  const setCity=(k,v)=>{if(C[k].text!==v)C[k].show(v,200)};
  onState(s=>{const km=s.session&&s.session.km;$('km').textContent=km?`${km.toLocaleString('de-DE')} km`:'–'});
  teleHooks.push(T=>{
    off.classList.toggle('on',!T);if(!T)return;
    $('sp').textContent=Math.round(T.speed);
    const lim=$('lim');lim.classList.toggle('off',!(T.limit>0));if(T.limit>0)lim.textContent=Math.round(T.limit);
    $('gr').textContent=T.gear>0?T.gear:T.gear<0?'R':'N';
    const fp=T.fuelCap?T.fuel/T.fuelCap:0;$('fu').textContent=T.fuelCap?`${Math.round(fp*100)} %`:'–';
    $('fb').firstChild.style.transform=`scaleX(${fp})`;$('fb').classList.toggle('low',fp<.15);
    if(T.time!=null){const d=Math.floor(T.time/1440)%7,m=T.time%1440;$('ck').textContent=`${DAYS[d]} ${String(Math.floor(m/60)).padStart(2,'0')}:${String(Math.floor(m%60)).padStart(2,'0')}`}
    $('rs').textContent=hm(T.rest);$('tr').textContent=T.truck||'–';
    const jk=T.src+'>'+T.dst;if(jk!==job){job=jk;maxDist=0}
    if(T.dst){setCity('sc',T.src);setCity('dc',T.dst);$('so').textContent=T.srcCo;$('do').textContent=T.dstCo;
      maxDist=Math.max(maxDist,T.dist);rt.style.setProperty('--p',maxDist?Math.min(1,1-T.dist/maxDist):0);
      $('ds').textContent=T.dist>=10000?`noch ${Math.round(T.dist/1000).toLocaleString('de-DE')} km`:`noch ${(T.dist/1000).toFixed(1).replace('.',',')} km`;
      $('et').textContent=T.eta?`Ankunft in ${hm(T.eta)}`:'';
      $('cg').textContent=T.cargo||'–';$('ms').textContent=T.mass?`${(T.mass/1000).toFixed(1).replace('.',',')} t`:'–';
      $('in').textContent=T.income?`${Math.round(T.income).toLocaleString('de-DE')} €`:'–';
    }else{setCity('sc','Freie Fahrt');setCity('dc','');$('so').textContent='Kein Auftrag';$('do').textContent='';
      rt.style.setProperty('--p',0);$('ds').textContent='';$('et').textContent='';$('cg').textContent='–';$('ms').textContent='–';$('in').textContent='–'}
  });
}

function game(){""")
rep("  else if(SCENE==='game')game();","  else if(SCENE==='game')game();\n  else if(SCENE==='drive')drive();")
open('tpl_ets2.html','w').write(t)
print('Teil 2 ok, AION übrig:',len(re.findall('AION',t)))

# ===== Eigene Text-Animation statt Zeichen-Mischen =====
t=open('tpl_ets2.html').read()
rep("const FX='cipher', FXDUR=650;","const FX='slide', FXDUR=650;")
open('tpl_ets2.html','w').write(t)
