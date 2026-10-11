import re
t=open('tpl.html').read()
def rep(a,b):
    global t
    assert a in t, a[:90]; t=t.replace(a,b)

# ---------- Namen
rep("VOID × AION 2 · OBS-Szenenset","VOID × GTA V / ROLEPLAY · OBS-Szenenset")
rep("  ?scene=game      AION 2 Game           transparentes Overlay, Kamera UNTER diese Quelle legen",
    "  ?scene=game      GTA Game              transparentes Overlay, Kamera UNTER diese Quelle legen\n"
    "                                        &char=Name  Charaktername fürs Rollenspiel (Namensplatte an der Kamera)")
rep("&cam=br|bl|tr|tl|off   (Standard br: x 1472  y 814  416 × 234)","&cam=r|br|bl|tr|tl|off   (Standard r: x 1472  y 330  416 × 234, rechts mittig)")
rep("<title>VOID × AION 2 · Szenen</title>","<title>VOID × GTA RP · Szenen</title>")
rep('<span class="aion">AION 2</span>','<span class="aion">GTA V · Roleplay</span>')
rep(">AION 2</span>'));",">GTA RP</span>'));")
rep("subs([P.get('title')||'AION 2','Enter The Void','void.cx'])",
    "subs([P.get('title')||'GTA RP',...(P.get('char')?[P.get('char')]:[]),'Enter The Void','void.cx'])")
rep("'Welche Klasse spielst du in AION 2?','Kantor, natürlich.','Die Flügel im Overlay sind schick'",
    "'Wer hat schon wieder mein Auto geklaut?','Ich ruf die Polizei!','Das Handy im Overlay ist schick'")

# ---------- Farben: Gold + Sonnenuntergang
rep("--aether:#BFE6FF;     /* Runenlicht */","--aether:#FFD978;     /* Gold hell */")
rep("--sky:#7FC8FF;","--sky:#F2C230;        /* GTA-Gold */\n  --sunset:#FF4F8B;     /* Sonnenuntergang Pink */")
for a,b in [("#B303F8,#7FC8FF","#FF4F8B,#F2C230"),("#B303F8,#E6F5FF","#F2C230,#FFF0B0"),
            ("rgba(110,190,255","rgba(255,190,90"),("rgba(80,160,255","rgba(255,120,120"),("#E6F5FF","#FFFFFF"),
            ("#CFE3FF","#F6EDE4"),("#BFE6FF","#FFD978"),("rgba(191,230,255","rgba(255,220,180"),
            ("rgba(127,200,255","rgba(255,190,90"),("rgba(80,150,255","rgba(255,120,140")]:
    rep(a,b)

# ---------- Schriften: Anton (Titel), Space Grotesk (UI)
rep('@font-face{font-family:"VOID Runes";src:url(data:font/woff2;base64,__RUNES__) format("woff2");font-display:block}\n@font-face{font-family:"VOID Latin";src:url(data:font/woff2;base64,__LATIN__) format("woff2");font-display:block}\n',
 '@font-face{font-family:"Anton";src:url(data:font/woff2;base64,__AN4__) format("woff2");font-display:block}\n'
 '@font-face{font-family:"JetBrains Mono";font-weight:500;src:url(data:font/woff2;base64,__JB5__) format("woff2");font-display:block}\n')
t=t.replace('"VOID Latin"','"Anton"').replace("\\'VOID Latin\\'","\\'Anton\\'")
rep('.halo text{font-family:"VOID Runes";fill:var(--aether)}\n','')
rep("const FX='cipher', FXDUR=650;","const FX='thunk', FXDUR=520;      /* GTA: Wörter knallen rein wie Missions-Einblendungen */")

# ---------- Himmel: Los Santos bei Sonnenuntergang
rep("""    radial-gradient(900px 700px at 8% 18%, rgba(179,3,248,.30), transparent 70%),
    radial-gradient(1000px 760px at 94% 30%, rgba(80,170,255,.26), transparent 70%),
    radial-gradient(1200px 520px at 50% 108%, rgba(17,65,228,.32), transparent 70%),
    radial-gradient(700px 500px at 50% 46%, rgba(255,220,180,.10), transparent 70%),
    linear-gradient(180deg,#080A22 0%,var(--night) 55%,#05061A 100%);}""",
"""    radial-gradient(700px 420px at 72% 70%, rgba(255,170,80,.55), transparent 70%),
    linear-gradient(180deg,#140A2E 0%,#3A1450 26%,#8A2A6A 46%,#E2566A 60%,#FF9A5A 70%,#5A1E3C 77.5%,#1A0A24 86%,#120818 100%);}""")
rep("@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}","@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}\n.beam{display:none}")
rep("const d=el('div','mote'+(Math.random()<.35?' v':''));const s=rnd(3,8);","const d=el('div','mote'+(Math.random()<.3?' v':''));const s=rnd(2,4);")

rep("@keyframes rise{","""/* ---------- Motiv: Los Santos, Sonnenuntergang ---------- */
.ls-sun{position:absolute;left:1210px;top:560px;width:360px;height:360px;border-radius:50%;
  background:radial-gradient(circle,#FFF3C4 0,#FFD27A 45%,#FF9A5A 70%,rgba(255,120,90,0) 72%);box-shadow:0 0 160px 60px rgba(255,170,90,.35)}
.ls-city{position:absolute;left:0;top:0;width:1920px;height:1080px}
.ls-palm{position:absolute;bottom:-20px;transform-origin:50% 100%;animation:sway 7s ease-in-out infinite alternate;will-change:transform}
@keyframes sway{to{transform:rotate(1.6deg)}}
.ls-shade{position:absolute;left:0;right:0;bottom:0;height:520px;background:linear-gradient(0deg,rgba(10,4,20,.92),transparent)}
@keyframes rise{""")
rep("/* Achteck-Loch mit abgeschrägten Ecken","""/* Los Santos: Sonne, Skyline mit Fenstern, Palmen im Vordergrund */
function palmSVG(h,flip){
  const fr=[[-150,-40],[-120,30],[-60,60],[60,55],[130,20],[150,-45],[40,-70],[-40,-75]].map(([dx,dy])=>
    `<path d="M0,0 Q${dx*.5},${dy*.6-30} ${dx},${dy}" stroke="#12081C" stroke-width="14" fill="none" stroke-linecap="round"/>`).join('');
  return `<svg width="360" height="${h+120}" viewBox="-180 -120 360 ${h+120}" style="${flip?'transform:scaleX(-1)':''}">
    <path d="M-10,${h} Q20,${h*.5} 0,0 L12,0 Q36,${h*.5} 12,${h}Z" fill="#12081C"/>${fr}</svg>`;
}
function motif(target){
  target.appendChild(el('div','ls-sun'));
  let b='';let x=0,i=0;
  while(x<1920){const w=40+((i*53)%5)*22,h=50+((i*97)%9)*24+(x>760&&x<1150?90:0)+(x>1180&&x<1560?-30:0);
    b+=`<rect x="${x}" y="${830-h}" width="${w}" height="${h+300}" fill="#1E0C2C"/>`;
    for(let wy=830-h+14;wy<810;wy+=22)for(let wx=x+8;wx<x+w-8;wx+=14)if((wx*7+wy*3+i)%11===0)b+=`<rect x="${wx}" y="${wy}" width="6" height="8" fill="#FFC27A" opacity=".75"/>`;
    x+=w+4;i++}
  const c=el('div','ls-city');c.innerHTML=`<svg width="1920" height="1080">${b}<rect x="0" y="828" width="1920" height="260" fill="#160822"/></svg>`;target.appendChild(c);
  target.appendChild(el('div','ls-shade'));
  [[60,640,0,0],[260,520,1,-1.2],[1600,600,1,-.8],[1760,700,0,-2]].forEach(([l,h,f,d])=>{
    const p=el('div','ls-palm');p.style.cssText=`left:${l}px;animation-delay:${d}s`;p.innerHTML=palmSVG(h,f);target.appendChild(p)});
}

/* Achteck-Loch mit abgeschrägten Ecken""")
rep("  sky(stage);halo(stage);wings(stage);","  sky(stage);motif(stage);stage.classList.add('sc-'+SCENE);")

# ---------- Kamera rechts mittig (oben rechts liegen Geld und Fahndungslevel)
rep("const pos=(P.get('cam')||'br').toLowerCase();","const pos=(P.get('cam')||'r').toLowerCase();\n  const below=pos.includes('t')||pos==='r';")
rep("y=pos.includes('t')?M+8+PL+6:1080-M-8-H;","y=pos==='r'?330:pos.includes('t')?M+8+PL+6:1080-M-8-H;")
rep("if(pos.includes('t'))gb.style.top=","if(below)gb.style.top=")

# ---------- Chat als Smartphone: kein Rahmen-Ornament um den Chat
rep("  frameSVG(stage,[cam,box]);","  frameSVG(stage,OWN?[cam]:[cam,box]);")

# ---------- Texte
rep("start:{title:'Stream startet',subs:['Client wird gepatcht','Charakter wird gewählt','Aether wird gesammelt','Kaffee steht bereit','Gleich geht’s los']}",
    "start:{title:'Stream startet',subs:['Charakter wird geladen','Ausweis wird gedruckt','Auto wird ausgeparkt','Funkgerät an','Gleich geht’s los']}")
rep("pause:{title:'Kurze Pause',subs:()=>['Bin gleich zurück','Chat bleibt offen',...latestLines(),'Kurz Aether tanken']}",
    "pause:{title:'Kurze Pause',subs:()=>['Kurz in der Wohnung','Charakter macht Pause',...latestLines(),'Bin gleich zurück']}")
rep("follow:e=>['Neuer Follow','Danke fürs Folgen'],","follow:e=>['Neuer Follow!','ist in der Stadt angekommen'],")
rep("sub:   e=>['Neues Abo',(e.tier?`Stufe ${e.tier}`:'')],","sub:   e=>['Mission erfüllt!',`neues Abo${tier(e.tier)}`],")
rep("resub: e=>['Abo verlängert',`${e.months} Monate${tier(e.tier)}`],","resub: e=>['Respekt +',`${e.months} Monate dabei${tier(e.tier)}`],")
rep("gift:  e=>[e.amount>1?'Abos verschenkt':'Abo verschenkt',`${e.amount} ${e.amount>1?'Abos':'Abo'}${tier(e.tier)}`],",
    "gift:  e=>['Abos verschenkt!',`${e.amount} ${e.amount>1?'Abos':'Abo'} für die Crew${tier(e.tier)}`],")
rep("cheer: e=>['Bits',`${e.amount} Bits`],","cheer: e=>[`+${e.amount} Bits`,'auf die Hand'],")
rep("raid:  e=>['Raid',`mit ${e.amount} ${e.amount==1?'Person':'Leuten'}`],","raid:  e=>['Raid!',`die Crew rückt mit ${e.amount} ${e.amount==1?'Person':'Leuten'} an`],")

# ---------- Klang: kurzer Missions-Stab
rep("const base={follow:523.25,","const base={follow:392,")
rep("[[ 'sine',1,.5],['triangle',.5,.18]]","[['sawtooth',1,.12],['square',.5,.06]]")
rep("const t=t0+i*.11;","const t=t0+i*.09;")
rep("e.gain.exponentialRampToValueAtTime(.0001,t+1.8);o.connect(e).connect(out);o.start(t);o.stop(t+1.9)",
    "e.gain.exponentialRampToValueAtTime(.0001,t+.9);o.connect(e).connect(out);o.start(t);o.stop(t+1)")

# ---------- Layout wie ein Ladebildschirm, Missions-Banner, Smartphone-Chat
rep("@media (prefers-reduced-motion:reduce)","""/* ---------- GTA: Ladebildschirm-Layout ---------- */
.fx{display:inline-block;opacity:0;transform:scale(1.4)}
.fx.in{animation:fxThunk .52s cubic-bezier(.2,.9,.3,1.25) forwards}
.fx.out{opacity:1;transform:none;animation:fxOff .26s ease-in forwards}
@keyframes fxThunk{to{opacity:1;transform:none}}
@keyframes fxOff{to{opacity:0;transform:scale(.94)}}
.center{align-items:flex-start;justify-content:flex-end;text-align:left;padding:0 0 150px 120px}
.vmark.mark{width:120px;margin-bottom:24px}
.title{font-size:168px;line-height:.95;letter-spacing:.01em;text-transform:uppercase;color:#fff;
  -webkit-text-stroke:4px #000;paint-order:stroke fill;text-shadow:8px 8px 0 rgba(0,0,0,.55)}
.rule{display:none}
.status{position:absolute;right:120px;bottom:70px;font-size:28px;letter-spacing:.02em;text-transform:uppercase;color:#fff;
  text-shadow:2px 2px 0 rgba(0,0,0,.6);display:flex;align-items:center;gap:18px}
.status::after{content:"";order:2;width:30px;height:30px;border-radius:50%;border:5px solid rgba(255,255,255,.25);border-top-color:#fff;animation:spin .9s linear infinite}
#stage.sc-end .status::after{display:none}
.count{margin-top:8px;font-size:24px;color:#fff;text-shadow:2px 2px 0 rgba(0,0,0,.6)}
.foot{top:56px;bottom:auto}
.head .title{font-size:72px;-webkit-text-stroke:3px #000;text-shadow:5px 5px 0 rgba(0,0,0,.5)}
.ticker .status{position:static;font-size:26px}
.ticker .status::after{display:none}
.plate .title{font-size:24px;-webkit-text-stroke:0;text-shadow:none;letter-spacing:.04em}
.g-v{font-family:"JetBrains Mono";font-size:14px}
/* Alerts: Missions-Banner quer übers Bild */
.alerts{left:0;right:0;top:110px}
.alert{clip-path:none;background:none;padding:0;width:100%;transform:scale(1.12)}
.alert.in{transform:none}
.alert .body{min-width:0;max-width:none;width:100%;clip-path:none;padding:16px 0 22px;
  background:linear-gradient(90deg,transparent,rgba(0,0,0,.75) 22%,rgba(0,0,0,.75) 78%,transparent)}
.a-kind{font-family:"Anton";font-size:78px;line-height:1;text-transform:uppercase;color:#F2C230;margin:0;
  -webkit-text-stroke:3px #000;paint-order:stroke fill;text-shadow:5px 5px 0 rgba(0,0,0,.6)}
.a-name{font-size:46px;color:#fff;letter-spacing:.02em;text-shadow:3px 3px 0 rgba(0,0,0,.6);margin-top:6px}
.a-detail{font-family:"Space Grotesk";font-weight:500;font-size:22px;letter-spacing:.02em;color:#fff;margin-top:8px}
/* Chat als Smartphone */
.chatpanel{clip-path:none;border-radius:46px;background:#0B0A12;border:12px solid #1D1B26;box-shadow:0 30px 80px rgba(0,0,0,.6);padding:58px 18px 22px}
.chatpanel::before{content:"Nachrichten";position:absolute;left:0;right:0;top:16px;text-align:center;font-weight:500;font-size:17px;color:#fff}
.chatpanel::after{content:"";position:absolute;left:50%;top:-2px;width:120px;height:22px;margin-left:-60px;border-radius:0 0 14px 14px;background:#1D1B26}
.chatlog{-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 60px);mask-image:linear-gradient(180deg,transparent 0,#000 60px)}
.msg{border:0;background:#24222E;border-radius:18px 18px 18px 6px;padding:10px 14px 12px;margin-top:10px}
.msg:last-child{background:#2E2B3B}
.m-name{font-family:"Space Grotesk";font-weight:500;font-size:15px;letter-spacing:0}
.m-text{font-size:18px}

/* STINGER-CSS-START */
/* STINGER-CSS-END */

@media (prefers-reduced-motion:reduce)""")

# ---------- Stinger: Sonnenuntergangs-Bänder fegen schräg durch, Marke knallt rein
t=re.sub(r'/\* STINGER-CSS-START \*/.*?/\* STINGER-CSS-END \*/','',t,count=1,flags=re.S)
t=re.sub(r'/\* STINGER-CSS-START \*/.*?/\* STINGER-CSS-END \*/',lambda m:'''/* STINGER-CSS-START */
.gs-b{position:absolute;top:-60px;left:0;width:2700px;height:1200px;will-change:transform;box-shadow:-14px 0 0 rgba(0,0,0,.35)}
.gs-back{position:absolute;inset:0;background:#1A0A28;opacity:0;animation:gsBack 1.95s steps(1) both}
@keyframes gsBack{0%{opacity:0}26.5%{opacity:1}74%,100%{opacity:0}}
.gs-city{position:absolute;left:0;right:0;bottom:60px;height:420px}
.gs-line{position:absolute;top:-60px;height:1200px;width:6px;background:#fff;opacity:0;transform:skewX(-18deg);animation:gsLine 1.95s both}
@keyframes gsLine{0%,24%{opacity:0}27%{opacity:.9}40%,100%{opacity:0}}
/* STINGER-CSS-END */''',t,count=1,flags=re.S)
t=re.sub(r'/\* STINGER-THEME-START \*/.*?/\* STINGER-THEME-END \*/',lambda m:'''/* STINGER-THEME-START */
/* GTA: vier Sonnenuntergangs-Bänder fegen schräg durchs Bild (wie beim Charakterwechsel), die Marke knallt rein */
function stingerTheme(root){
  root.appendChild(el('div','gs-back'));
  const B=[['#FF9A5A',0],['#FF4F8B',4],['#7A2A8A',8],['#1A0A28',12]];let css='';
  B.forEach(([c,o],i)=>{
    const a=o,b=o+13,cc=74+(3-i)*3,d=cc+15;          /* Abgang: dunkles Band zuerst, dann die Farben */
    css+=`@keyframes gs${i}{0%,${a}%{transform:translateX(-3000px) skewX(-18deg);animation-timing-function:cubic-bezier(.6,0,.2,1)}
      ${b}%,${cc}%{transform:translateX(-400px) skewX(-18deg);animation-timing-function:cubic-bezier(.7,0,.4,1)}${d}%,100%{transform:translateX(2400px) skewX(-18deg)}}`;
    const s=el('div','gs-b');s.style.cssText=`background:${c};animation:gs${i} 1.95s both;z-index:${i}`;
    if(i===3){let sk='';let x=0,k=0;while(x<2700){const w=50+(k*37%4)*24,h=80+(k*71%7)*40;sk+=`<rect x="${x}" y="${420-h}" width="${w}" height="${h}" fill="#2B1240"/>`;x+=w+6;k++}
      s.innerHTML=`<svg class="gs-city" viewBox="0 0 2700 420" preserveAspectRatio="none" width="2700" height="420">${sk}</svg>`}
    root.appendChild(s);
  });
  [700,1180].forEach(x=>{const l=el('div','gs-line');l.style.left=x+'px';l.style.zIndex=4;root.appendChild(l)});
  const st=document.createElement('style');st.textContent=css;root.appendChild(st);
}
function stingerMark(m,root){m.style.zIndex=6}
/* STINGER-THEME-END */''',t,flags=re.S)
open('tpl_gta.html','w').write(t)
print('ok, AION übrig:',len(re.findall('AION',t)))
