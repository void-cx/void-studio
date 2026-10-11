t=open('tpl.html').read()
def rep(a,b):
    global t
    assert a in t, a[:80]
    t=t.replace(a,b)

rep("VOID × AION 2 · OBS-Szenenset","VOID × WARDOGS · OBS-Szenenset")
rep("  ?scene=game      AION 2 Game           transparentes Overlay, Kamera UNTER diese Quelle legen","  ?scene=game      Wardogs Game          transparentes Overlay, Kamera UNTER diese Quelle legen")
rep("&cam=br|bl|tr|tl|off   (Standard br: x 1472  y 814  416 × 234)","&cam=r|br|bl|tr|tl|off   (Standard r: x 1472  y 330  416 × 234, rechts mittig neben dem HUD)")
rep("<title>VOID × AION 2 · Szenen</title>","<title>VOID × Wardogs · Szenen</title>")
rep('<span class="aion">AION 2</span>','<span class="aion">Wardogs</span>')
rep(">AION 2</span>'));",">Wardogs</span>'));")
rep("P.get('title')||'AION 2'","P.get('title')||'Wardogs'")
rep("'Welche Klasse spielst du in AION 2?','Kantor, natürlich.','Die Flügel im Overlay sind schick'",
    "'Wie viel Cash hast du gerade?','Heli wartet am Funkturm','Die Höhenlinien im Overlay sind schick'")

rep("--aether:#BFE6FF;     /* Runenlicht */","--aether:#FFC860;     /* Spielfarbe hell (Runen, Werte) */")
rep("--sky:#7FC8FF;","--sky:#FFB020;        /* Spielfarbe: Signal-Amber */\n  --moss:#1A2420;       /* kaltes Grau-Grün der Berge */")
for a,b in [("#B303F8,#7FC8FF","#C27400,#FFB020"),("#B303F8,#E6F5FF","#FFB020,#FFE2A8"),
            ("rgba(110,190,255","rgba(255,170,40"),("rgba(80,160,255","rgba(255,140,20"),("#E6F5FF","#F4EFE6"),
            ("#CFE3FF","#E9DCC4"),("#BFE6FF","#FFC860"),("rgba(191,230,255","rgba(255,200,120"),
            ("rgba(127,200,255","rgba(255,176,32"),("rgba(80,150,255","rgba(255,170,40")]:
    rep(a,b)
rep(".ch.v .rn{color:#E6C4FF;text-shadow:0 0 .18em rgba(200,110,255,.9),0 0 .5em rgba(179,3,248,.45)}",
    ".ch.v .rn{color:#FFF1D6;text-shadow:0 0 .18em rgba(255,210,140,.9),0 0 .5em rgba(255,150,30,.4)}")

rep("""    radial-gradient(900px 700px at 8% 18%, rgba(179,3,248,.30), transparent 70%),
    radial-gradient(1000px 760px at 94% 30%, rgba(80,170,255,.26), transparent 70%),
    radial-gradient(1200px 520px at 50% 108%, rgba(17,65,228,.32), transparent 70%),
    radial-gradient(700px 500px at 50% 46%, rgba(255,200,120,.10), transparent 70%),
    linear-gradient(180deg,#080A22 0%,var(--night) 55%,#05061A 100%);}""",
"""    radial-gradient(1100px 620px at 78% -8%, rgba(255,166,40,.30), transparent 70%),
    radial-gradient(800px 600px at 4% 10%, rgba(179,3,248,.14), transparent 70%),
    radial-gradient(1400px 600px at 50% 112%, rgba(26,36,32,.95), transparent 72%),
    radial-gradient(900px 520px at 96% 100%, rgba(17,65,228,.16), transparent 70%),
    linear-gradient(180deg,#0B0B1A 0%,var(--night) 50%,#060A0C 100%);}""")
rep("""  100%{transform:translate3d(var(--dx),-340px,0);opacity:0}}""",
"""  100%{transform:translate3d(var(--dx),-50px,0);opacity:0}}

/* ---------- Motiv: Lagekarte mit Kontrollzone ---------- */
.map{position:absolute;inset:-40px;will-change:transform;animation:drift 70s ease-in-out infinite alternate}
.map svg{width:100%;height:100%}
@keyframes drift{to{transform:translate3d(-36px,18px,0) scale(1.035)}}
.zone{position:absolute;left:50%;top:50%;width:620px;height:620px;margin:-330px 0 0 -310px}
.zone svg{position:absolute;inset:0;overflow:visible}
.zone .pulse{transform-origin:310px 310px;animation:zone 3.2s ease-in-out infinite;will-change:transform,opacity}
@keyframes zone{50%{transform:scale(1.035);opacity:.45}}
.zone .lbl{font-family:"Space Grotesk";font-size:15px;fill:var(--sky);letter-spacing:.06em}
.sweep{position:absolute;top:0;bottom:0;left:-420px;width:420px;will-change:transform;
  background:linear-gradient(90deg,transparent,rgba(255,176,32,.035) 70%,rgba(255,176,32,.09) 97%,rgba(255,176,32,.0));
  animation:sweep 14s linear infinite}
@keyframes sweep{to{transform:translateX(2760px)}}""")
rep("--dx:${rnd(-60,60)|0}px","--dx:${rnd(90,260)|0}px")
rep("const d=el('div','mote'+(Math.random()<.35?' v':''));const s=rnd(3,8);","const d=el('div','mote'+(Math.random()<.12?' v':''));const s=rnd(2,5);")

rep("/* Achteck-Loch mit abgeschrägten Ecken","""/* Lagekarte: Höhenlinien, Raster, Kontrollzone (ersetzt wings() + halo()) */
function motif(target){
  const peaks=[[-520,180,15,1.0],[560,-90,12,1.7],[80,430,7,2.6]];   /* x, y, Ringe, Phase */
  let lines='';
  for(let gx=-960;gx<=960;gx+=120)lines+=`<line x1="${gx}" y1="-540" x2="${gx}" y2="540" stroke="rgba(255,200,120,.045)"/>`;
  for(let gy=-540;gy<=540;gy+=120)lines+=`<line x1="-960" y1="${gy}" x2="960" y2="${gy}" stroke="rgba(255,200,120,.045)"/>`;
  peaks.forEach(([cx,cy,n,ph])=>{
    for(let i=0;i<n;i++){
      const r=40+i*46,pts=[];
      for(let a=0;a<=360;a+=6){const rad=a*Math.PI/180;
        const d=r*(1+.16*Math.sin(3*rad+ph+i*.21)+.09*Math.cos(5*rad-ph*1.3)+.05*Math.sin(7*rad+i*.4));
        pts.push(`${(cx+d*Math.cos(rad)).toFixed(1)},${(cy+d*.66*Math.sin(rad)).toFixed(1)}`)}
      const major=i%5===4;
      lines+=`<polyline points="${pts.join(' ')}" fill="none" stroke="rgba(255,176,32,${((major?.2:.11)*(1-i/(n+4))).toFixed(3)})" stroke-width="${major?1.4:1}"/>`;
    }});
  const m=el('div','map');m.innerHTML=`<svg viewBox="-960 -540 1920 1080" preserveAspectRatio="xMidYMid slice">${lines}</svg>`;
  target.appendChild(m);target.appendChild(el('div','sweep'));
  const L=46,S=620;
  const br=(x,y,sx,sy)=>`<path d="M${x},${y+sy*L} L${x},${y} L${x+sx*L},${y}" fill="none" stroke="#FFB020" stroke-width="2.4"/>`;
  const z=el('div','zone');z.innerHTML=`<svg viewBox="0 0 ${S} ${S}">
    <rect x="1" y="1" width="${S-2}" height="${S-2}" fill="rgba(255,176,32,.025)" stroke="rgba(255,176,32,.3)" stroke-dasharray="6 10"/>
    <g class="pulse">${br(0,0,1,1)}${br(S,0,-1,1)}${br(0,S,1,-1)}${br(S,S,-1,-1)}</g>
    <text class="lbl" x="0" y="-14">Kontrollzone · 2 × 2 km</text>
    <text class="lbl" x="${S}" y="${S+28}" text-anchor="end">44°12′ N · 41°48′ E</text></svg>`;
  target.appendChild(z);
}

/* Achteck-Loch mit abgeschrägten Ecken""")
rep("  sky(stage);halo(stage);wings(stage);","  sky(stage);motif(stage);")
rep("   ${dia(cx,y)}${dia(cx,y+h)}`;","""   ${[[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]].map(([px,py,sx,sy])=>
      `<path d="M${px+sx*4},${py+sy*34} L${px+sx*4},${py+sy*4} L${px+sx*34},${py+sy*4}" fill="none" stroke="#FFB020" stroke-width="2.4"/>`).join('')}`;""")

rep("start:{title:'Stream startet',subs:['Client wird gepatcht','Charakter wird gewählt','Aether wird gesammelt','Kaffee steht bereit','Gleich geht’s los']}",
    "start:{title:'Stream startet',subs:['Loadout wird gekauft','Zone wird markiert','Funkcheck läuft','Helikopter wartet','Gleich geht’s los']}")
rep("pause:{title:'Kurze Pause',subs:()=>['Bin gleich zurück','Chat bleibt offen',...latestLines(),'Kurz Aether tanken']}",
    "pause:{title:'Kurze Pause',subs:()=>['Kurz in Deckung','Munition auffüllen',...latestLines(),'Bin gleich zurück']}")

rep("const T=new Cipher(t,{stagger:95,shuffle:700});","const T=new Cipher(t,{stagger:80,shuffle:520});")
rep("const S=new Cipher(st,{stagger:40,shuffle:360});","const S=new Cipher(st,{stagger:35,shuffle:300});")
rep("const base={follow:523.25,","const base={follow:392,")
rep("sub:440,resub:440,gift:392,cheer:587.33,raid:329.63,redeem:493.88}","sub:329.63,resub:329.63,gift:293.66,cheer:440,raid:246.94,redeem:370}")
rep("[[ 'sine',1,.5],['triangle',.5,.18]]","[['triangle',1,.5],['square',.5,.05]]")
rep("const t=t0+i*.11;","const t=t0+i*.07;")
rep("e.gain.exponentialRampToValueAtTime(.0001,t+1.8);o.connect(e).connect(out);o.start(t);o.stop(t+1.9)",
    "e.gain.exponentialRampToValueAtTime(.0001,t+.6);o.connect(e).connect(out);o.start(t);o.stop(t+.7)")

rep("const pos=(P.get('cam')||'br').toLowerCase();","const pos=(P.get('cam')||'r').toLowerCase();\n  const below=pos.includes('t')||pos==='r';      /* Ziele unter der Kamera */")
rep("y=pos.includes('t')?M+8+PL+6:1080-M-8-H;","y=pos==='r'?330:pos.includes('t')?M+8+PL+6:1080-M-8-H;")
rep("if(pos.includes('t'))gb.style.top=","if(below)gb.style.top=")
open('tpl_wardogs.html','w').write(t)
import re; print('AION übrig:',len(re.findall('AION',t)))

# ===== Schriften: keine Runen / kein VOID Latin im Wardogs-Theme =====
t=open('tpl_wardogs.html').read()
rep('@font-face{font-family:"VOID Runes";src:url(data:font/woff2;base64,__RUNES__) format("woff2");font-display:block}\n@font-face{font-family:"VOID Latin";src:url(data:font/woff2;base64,__LATIN__) format("woff2");font-display:block}\n',
 '@font-face{font-family:"Barlow Condensed";font-weight:500;src:url(data:font/woff2;base64,__BC5__) format("woff2");font-display:block}\n'
 '@font-face{font-family:"Barlow Condensed";font-weight:700;src:url(data:font/woff2;base64,__BC7__) format("woff2");font-display:block}\n'
 '@font-face{font-family:"JetBrains Mono";font-weight:500;src:url(data:font/woff2;base64,__JB5__) format("woff2");font-display:block}\n')
rep('font-family:"VOID Runes";font-weight:400;','font-family:"JetBrains Mono";font-weight:500;')
t=t.replace('"VOID Latin"','"Barlow Condensed"').replace("\\'VOID Latin\\'","\\'Barlow Condensed\\'")
rep('.halo text{font-family:"VOID Runes";fill:var(--aether)}\n','')
rep("rastet Buchstabe für Buchstabe in VOID Latin ein.","rastet Buchstabe für Buchstabe in Barlow Condensed ein (Funkspruch-Effekt).")
rep("const POOL='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';","const POOL='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#/<>';")
rep("const glyph=c=>KEY&&RUNESET.has(c.toUpperCase())?c:rr();","const glyph=c=>rr();             /* Wardogs: immer zufällige Zeichen, kein Runen-Schlüssel */")
rep("@media (prefers-reduced-motion:reduce)","""/* ---------- Wardogs-Typografie ---------- */
.fx{position:relative;display:inline-block;clip-path:inset(-20% 100% -20% 0)}
.fx.in{animation:fxWipe .65s cubic-bezier(.65,0,.2,1) forwards}
.fx.in::after{content:"";position:absolute;top:-6%;bottom:-6%;width:4px;left:0;background:#FFB020;box-shadow:0 0 12px rgba(255,176,32,.8);animation:fxBar .65s cubic-bezier(.65,0,.2,1) forwards}
.fx.out{clip-path:inset(-20% 0 -20% 0);animation:fxWipeOut .32s cubic-bezier(.6,0,.4,1) forwards}
@keyframes fxWipe{to{clip-path:inset(-20% 0 -20% 0)}}
@keyframes fxBar{0%{left:0;opacity:1}85%{opacity:1}100%{left:100%;opacity:0}}
@keyframes fxWipeOut{to{clip-path:inset(-20% 0 -20% 100%)}}

.title,.status,.a-name,.a-detail,.foot .aion,.m-name,.brand span:last-child,.plate .title{text-transform:uppercase}
.title{font-weight:700;font-size:150px;letter-spacing:.02em;text-shadow:0 0 .12em rgba(255,150,30,.25)}
.status{font-weight:500;font-size:34px;letter-spacing:.12em}
.head .title{font-size:66px;letter-spacing:.03em}
.plate .title{font-size:24px;font-weight:700;letter-spacing:.08em}
.a-name{font-weight:700;font-size:66px;letter-spacing:.03em}
.a-detail{font-weight:500;font-size:28px;letter-spacing:.12em}
.foot .aion{font-weight:700;letter-spacing:.08em}
.m-name{font-weight:700;font-size:19px;letter-spacing:.06em}
.g-v{font-family:"JetBrains Mono";font-size:14px;letter-spacing:0}
.ch .rn{font-size:.62em;top:.36em;color:var(--sky);text-shadow:0 0 .3em rgba(255,150,30,.6)}
.ch.v .rn{color:#FFF1D6;text-shadow:0 0 .3em rgba(255,200,120,.5)}

@media (prefers-reduced-motion:reduce)""")
open('tpl_wardogs.html','w').write(t)
t=open('tpl_wardogs.html').read()
rep("function bridge(){\n  if(ALERTS)stage.appendChild(alertBox);","function bridge(){\n  if(SCENE==='game')alertBox.style.top='96px';      /* Wardogs-Kompass oben mittig frei lassen */\n  if(ALERTS)stage.appendChild(alertBox);")
open('tpl_wardogs.html','w').write(t)

# ===== Runde 2: spieltypischer (Fraktionen, Hot Zone, Kompass, Begriffe) =====
t=open('tpl_wardogs.html').read()
# Welt etwas grauer, weniger Violett-Dunst
rep("radial-gradient(800px 600px at 4% 10%, rgba(179,3,248,.14), transparent 70%),",
    "radial-gradient(800px 600px at 4% 10%, rgba(179,3,248,.07), transparent 70%),\n    radial-gradient(1600px 700px at 30% 60%, rgba(120,128,124,.07), transparent 70%),")
# Zonen-Beschriftung oben, Kolchia
rep('<text class="lbl" x="0" y="-14">Kontrollzone · 2 × 2 km</text>\n    <text class="lbl" x="${S}" y="${S+28}" text-anchor="end">44°12′ N · 41°48′ E</text></svg>`;',
    '''<text class="lbl" x="0" y="-14">Kontrollzone · 2 × 2 km</text>
    <text class="lbl dim" x="${S}" y="-14" text-anchor="end">Kolchia</text>
    <g transform="translate(${S/2},${S/2})"><g class="hz">
      <circle r="58" fill="rgba(255,176,32,.07)" stroke="#FFB020" stroke-width="1.6" stroke-dasharray="3 7"/>
      <circle r="4" fill="#FFB020"/>
      <text class="lbl" x="72" y="5">Hot Zone · zählt doppelt</text></g></g></svg>`;
  /* Drei Fraktionen unter der Zone: wer führt, wechselt (nur Deko, keine Zahlen) */
  const fb=el('div','factions');
  [['Lonestar','#3D8BFF'],['Valkyra','#E5484D'],['Manticore','#3FBF6A']].forEach(([n,c],i)=>{
    const f=el('div','fac');f.style.setProperty('--c',c);f.style.animationDelay=`${-i*6}s`;
    f.innerHTML=`<i></i><span>${n}</span>`;fb.appendChild(f)});
  target.appendChild(fb);
  /* Kompass wie im Spiel-HUD, läuft langsam durch */
  const dirs={0:'N',45:'NO',90:'O',135:'SO',180:'S',225:'SW',270:'W',315:'NW'};
  let cs='';for(let d=0;d<720;d+=15){const a=d%360;
    cs+=`<span class="${dirs[a]!==undefined?'cd':'cn'}">${dirs[a]??a}</span>`}
  const cp=el('div','compass',`<div class="strip">${cs}</div><b></b>`);target.appendChild(cp);''')
rep(".zone .lbl{",""".zone .lbl.dim{fill:var(--mist)}
.zone .hz{animation:hz 46s ease-in-out infinite alternate;will-change:transform}
@keyframes hz{0%{transform:translate(-230px,236px)}35%{transform:translate(-40px,226px)}
  70%{transform:translate(20px,244px)}100%{transform:translate(-170px,232px)}}   /* unterhalb von Titel und Statuszeile */
.factions{position:absolute;left:50%;top:850px;width:620px;margin-left:-310px;display:flex;gap:10px}
.fac{flex:1;opacity:.55;animation:lead 18s ease-in-out infinite}
.fac i{display:block;height:4px;background:var(--c)}
.fac span{display:block;margin-top:8px;font-size:15px;color:var(--mist);letter-spacing:.04em}
@keyframes lead{0%,28%{opacity:1}36%,100%{opacity:.45}}
.compass{position:absolute;left:50%;top:22px;width:760px;height:42px;margin-left:-380px;overflow:hidden;
  -webkit-mask-image:linear-gradient(90deg,transparent,#000 18%,#000 82%,transparent);mask-image:linear-gradient(90deg,transparent,#000 18%,#000 82%,transparent)}
.compass .strip{display:flex;width:1920px;will-change:transform;animation:compass 120s linear infinite}
.compass span{flex:0 0 40px;text-align:center;font-family:"JetBrains Mono";font-size:12px;line-height:22px;color:rgba(244,239,230,.42);
  border-bottom:1px solid rgba(244,239,230,.18)}
.compass span.cd{color:#F4EFE6;font-size:14px;font-weight:500}
.compass b{position:absolute;left:50%;bottom:6px;width:0;height:0;margin-left:-6px;border:6px solid transparent;border-bottom-color:#FFB020}
@keyframes compass{to{transform:translateX(-960px)}}
.zone .lbl{""")
# Alerts mit Wardogs-Begriffen (Söldner, Verträge, Kriegskasse)
rep("follow:e=>['Neuer Follow','Danke fürs Folgen'],","follow:e=>['Neuer Follow','Willkommen im Trupp'],")
rep("sub:   e=>['Neues Abo',(e.tier?`Stufe ${e.tier}`:'')],","sub:   e=>['Neues Abo',`Vertrag unterschrieben${tier(e.tier)}`],")
rep("resub: e=>['Abo verlängert',`${e.months} Monate${tier(e.tier)}`],","resub: e=>['Abo verlängert',`${e.months} Monate unter Vertrag${tier(e.tier)}`],")
rep("gift:  e=>[e.amount>1?'Abos verschenkt':'Abo verschenkt',`${e.amount} ${e.amount>1?'Abos':'Abo'}${tier(e.tier)}`],",
    "gift:  e=>[e.amount>1?'Abos verschenkt':'Abo verschenkt',`${e.amount} ${e.amount>1?'Verträge':'Vertrag'} für den Trupp${tier(e.tier)}`],")
rep("cheer: e=>['Bits',`${e.amount} Bits`],","cheer: e=>['Bits',`${e.amount} Bits in die Kriegskasse`],")
rep("raid:  e=>['Raid',`mit ${e.amount} ${e.amount==1?'Person':'Leuten'}`],","raid:  e=>['Raid',`Verstärkung: ${e.amount} ${e.amount==1?'Person rückt':'Leute rücken'} an`],")
# Statuszeilen
rep("subs:['Loadout wird gekauft','Zone wird markiert','Funkcheck läuft','Helikopter wartet','Gleich geht’s los']",
    "subs:['Loadout wird gekauft','Kontrollzone wird ausgewürfelt','Tower-Code wird geknackt','Heli fliegt zur Zone','Gleich geht’s los']")
rep("subs:()=>['Kurz in Deckung','Munition auffüllen',...latestLines(),'Bin gleich zurück']",
    "subs:()=>['Kurz in der Safe Zone','Munition auffüllen',...latestLines(),'Hot Zone läuft nicht weg','Bin gleich zurück']")
open('tpl_wardogs.html','w').write(t)

# ===== Stinger Wardogs: schräge Lagekarte als Wischblende, Glitch an der Bildmarke =====
import re as _re
t=open('tpl_wardogs.html').read()
t=_re.sub(r'/\* STINGER-CSS-START \*/.*?/\* STINGER-CSS-END \*/','''/* STINGER-CSS-START */
.wd-panel{position:absolute;left:0;top:-12px;width:2400px;height:1104px;overflow:hidden;will-change:transform;
  background:linear-gradient(90deg,#07071A 0%,#0B0F14 55%,#151B17 100%);animation:wdP 1.95s both}
.wd-back{position:absolute;inset:0;background:#0B0F14;opacity:0;animation:wdBack 1.95s steps(1) both}
@keyframes wdBack{0%{opacity:0}26.5%{opacity:1}74%,100%{opacity:0}}
.wd-panel svg{position:absolute;inset:0;width:100%;height:100%}
.wd-edge{position:absolute;top:0;bottom:0;right:0;width:8px;background:#FFB020}
.wd-edge.b{right:30px;width:2px;opacity:.55}
.wd-edge.l{right:auto;left:0}
.wd-edge.lb{right:auto;left:30px;width:2px;opacity:.55}
@keyframes wdP{0%{transform:translateX(-2700px) skewX(-12deg);animation-timing-function:cubic-bezier(.6,0,.25,1)}
  25.6%{transform:translateX(-240px) skewX(-12deg)}74.4%{transform:translateX(-240px) skewX(-12deg);animation-timing-function:cubic-bezier(.7,0,.4,1)}
  100%{transform:translateX(2250px) skewX(-12deg)}}
.wd-bar{position:absolute;left:0;right:0;height:3px;background:rgba(255,176,32,.5);opacity:0;animation:wdBar 1.95s steps(1) both}
@keyframes wdBar{0%,30%{opacity:0}31%{opacity:1}33%{opacity:0}52%{opacity:.8}53%{opacity:0}61%{opacity:1}62%,100%{opacity:0}}
.wd-slice{position:absolute;inset:0;animation:wdJit 1.95s steps(1) both}
.wd-slice.a{clip-path:inset(28% 0 56% 0)} .wd-slice.b{clip-path:inset(60% 0 22% 0);animation-name:wdJit2}
@keyframes wdJit{0%,48%{transform:none;opacity:0}49%{transform:translateX(-18px);opacity:1}51%{transform:translateX(12px)}
  53%{transform:translateX(-6px)}55%{transform:none;opacity:0}63%{transform:translateX(10px);opacity:1}64%,100%{transform:none;opacity:0}}
@keyframes wdJit2{0%,49%{transform:none;opacity:0}50%{transform:translateX(16px);opacity:1}52%{transform:translateX(-10px)}
  54%,100%{transform:none;opacity:0}}
.st-mark .wd-slice .vmark{width:100%}
/* STINGER-CSS-END */''',t,flags=_re.S)
t=_re.sub(r'/\* STINGER-THEME-START \*/.*?/\* STINGER-THEME-END \*/','''/* STINGER-THEME-START */
/* Wardogs: schräge Lagekarte wischt durch, Bildmarke baut sich auf und stört kurz wie ein Funksignal */
function stingerTheme(root){
  let l='';
  for(let gx=0;gx<=2400;gx+=120)l+=`<line x1="${gx}" y1="0" x2="${gx}" y2="1080" stroke="rgba(255,200,120,.09)"/>`;
  for(let gy=0;gy<=1080;gy+=120)l+=`<line x1="0" y1="${gy}" x2="2400" y2="${gy}" stroke="rgba(255,200,120,.06)"/>`;
  [[700,560,14,.6],[1700,420,12,2.1]].forEach(([cx,cy,n,ph])=>{for(let i=0;i<n;i++){const r=40+i*48,pts=[];
    for(let a=0;a<=360;a+=6){const q=a*Math.PI/180,d=r*(1+.16*Math.sin(3*q+ph+i*.2)+.08*Math.cos(5*q-ph));
      pts.push(`${(cx+d*Math.cos(q)).toFixed(1)},${(cy+d*.66*Math.sin(q)).toFixed(1)}`)}
    l+=`<polyline points="${pts.join(' ')}" fill="none" stroke="rgba(255,176,32,${(.3*(1-i/(n+3))).toFixed(3)})"/>`}});
  root.appendChild(el('div','wd-back'));        /* deckt Rasterlücken der schrägen Kante ab */
  const p=el('div','wd-panel');p.innerHTML=`<svg viewBox="0 0 2400 1080">${l}</svg><i class="wd-edge"></i><i class="wd-edge b"></i><i class="wd-edge l"></i><i class="wd-edge lb"></i>`;
  root.appendChild(p);
  [380,566,742].forEach((y,i)=>{const b=el('i','wd-bar');b.style.top=y+'px';b.style.animationDelay=`${i*-90}ms`;root.appendChild(b)});
}
function stingerMark(m,root){            /* zwei versetzte Streifen derselben Marke = Funk-Glitch */
  ['a','b'].forEach(k=>{const s=el('div','wd-slice '+k);s.appendChild(makeMark({d:480,t:450}));m.appendChild(s)});
}
/* STINGER-THEME-END */''',t,flags=_re.S)
open('tpl_wardogs.html','w').write(t)

# ===== Eigene Text-Animation statt Zeichen-Mischen =====
t=open('tpl_wardogs.html').read()
rep("const FX='cipher', FXDUR=650;","const FX='wipe', FXDUR=650;")
open('tpl_wardogs.html','w').write(t)
