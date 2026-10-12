/* =========================================================
   VOID Szenen-Kern (build/core/core.js) – gemeinsamer Teil für Packs mit eigenem Template.
   packs.py setzt diese Datei an der Markierung @CORE@ im Template ein. Das Template liefert Aussehen und Szenen:

     boot({start(){…}, pause(){…}, end(){…}, chat(){…}, game(){…}, stinger(){…}, …},
          {alert:async (e,info)=>{…}, samples:{chat:[…], names:[…]}})

   Der Kern kümmert sich um Parameter, Bridge (Alerts, Chat, Ziele, Rückblick, Telemetrie, IRL-Signal),
   Alert-Warteschlange mit Sound, Pause und Überspringen, Testdaten (&test=1) und die animierte Bildmarke.
   ========================================================= */
const MARK  = "data:image/svg+xml;base64,__MARK__";
const LOCKUP= "data:image/svg+xml;base64,__LOCKUP__";

/* Parameter aus ?query und #hash (OBS „Lokale Datei“ erlaubt keine Query, die Einstiegsdateien in obs/ nutzen #) */
const P = new URLSearchParams(location.search.slice(1)+'&'+location.hash.slice(1));
const SCENE = (P.get('scene')||'start').toLowerCase();
const DEMO = P.get('demo')==='1';
const TEST = P.get('test')==='1';
const ALERTS = P.get('alerts')!=='0';
const stage = document.getElementById('stage');

/* Vorschau im Browser auf Fenstergröße skalieren (in OBS 1:1) */
function fit(){const s=Math.min(innerWidth/1920,innerHeight/1080);stage.style.transform=`scale(${s})`}
addEventListener('resize',fit);fit();

const rnd=(a,b)=>a+Math.random()*(b-a);
const el=(tag,cls,html)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;return e};
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const num=n=>Number(n||0).toLocaleString('de-DE');
const list=(key,def)=>{const v=P.get(key);return v?v.split('|').map(s=>s.trim()).filter(Boolean):def};
const put=(parent,cls,html,css)=>{const e=el('div',cls,html);if(css)e.style.cssText=css;parent.appendChild(e);return e};

/* Platzhalter mit &demo=1 (für Vorschau und Test im Browser) */
function demoBox(r,label,bg){
  if(!DEMO)return null;
  const d=put(stage,'demo',label,`position:absolute;left:${r.x}px;top:${r.y}px;width:${r.w}px;height:${r.h}px;`+
    `display:flex;align-items:center;justify-content:center;font:500 22px/1 system-ui,sans-serif;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.55);`+
    `background:${bg||'linear-gradient(160deg,#2a3b66,#121a33 60%,#2b1f4a)'}`);
  return d;
}

/* Text austauschen: Theme gestaltet .sw (sichtbar), .sw.out (geht) und .sw.in (kommt) */
async function swap(node,text,ms=420){
  if(node.textContent===text&&node.classList.contains('sw'))return;
  node.classList.add('sw','out');await wait(ms);
  node.textContent=text;node.classList.remove('out');node.classList.add('in');
  void node.offsetWidth;node.classList.remove('in');await wait(ms);
}
/* Zeilen im Wechsel; src darf eine Funktion sein (dann live aus dem Bridge-Zustand) */
async function cycle(node,src,every=5200){
  const get=()=>{const l=typeof src==='function'?src():src;return l&&l.length?l:['void.cx']};
  let i=0;node.textContent=get()[0];node.classList.add('sw');
  for(;;){await wait(every);const l=get();i=(i+1)%l.length;await swap(node,l[i])}
}
/* Countdown mit &min=5: ruft tick(sekunden) jede Viertelsekunde, 0 heißt „gleich live“ */
function countdown(tick){
  const min=parseFloat(P.get('min'));if(!(min>0))return false;
  const end=Date.now()+min*60000;
  const f=()=>tick(Math.max(0,Math.round((end-Date.now())/1000)));f();setInterval(f,250);return true;
}
const mmss=s=>`${String(s/60|0).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;

/* ---------- Animierte Bildmarke ---------- */
const MARKPARTS={"defs": "<linearGradient id=\"g1\" x1=\"489.4\" y1=\"175.54\" x2=\"1047.5\" y2=\"733.65\" gradientUnits=\"userSpaceOnUse\"><stop offset=\"0\" stop-color=\"#b303f8\"/><stop offset=\"1\" stop-color=\"#1141e4\"/></linearGradient><linearGradient id=\"g2\" x1=\"411.53\" y1=\"66.17\" x2=\"1339.31\" y2=\"993.94\" gradientUnits=\"userSpaceOnUse\"><stop offset=\"0\" stop-color=\"#b303f8\"/><stop offset=\"1\" stop-color=\"#1141e4\"/></linearGradient><linearGradient id=\"g3\" x1=\"167.42\" y1=\"154.17\" x2=\"1129.31\" y2=\"1116.05\" gradientUnits=\"userSpaceOnUse\"><stop offset=\"0\" stop-color=\"#b303f8\"/><stop offset=\"1\" stop-color=\"#1141e4\"/></linearGradient><linearGradient id=\"tw\" x1=\"182\" y1=\"0\" x2=\"748\" y2=\"0\" gradientUnits=\"userSpaceOnUse\"><stop offset=\"0\" stop-color=\"#2741e5\"/><stop offset=\"1\" stop-color=\"#b303f8\"/></linearGradient>", "tri": "m280.3,228.09l408.95,707.27,412.68-707.27H280.3Zm407.08,507.23l-219.39-396.6h441.26l-221.88,396.6Z", "wing": "m1357.98,83.9s-41.95,104.41-670.29,1187.13C59.35,188.31,14.29,88.87,14.29,88.87c0,0,77.07,94.47,185.21,130.51l488.19,847.9,483.84-847.9s60.91-3.73,186.45-135.49Z", "r": "m1321.81,411.2c-12.12-28.03-26.07-55.05-41.78-80.99l-43.62,67.17c43.92,82.82,68.74,176.79,68.74,276.33,0,316.26-250.59,576.4-567.99,600.95l-38.87,72.68c89.14-1.27,175.64-19.01,257.26-52.78,81.9-33.88,155.47-82.4,218.66-144.2,63.23-61.85,112.89-133.9,147.59-214.14,35.96-83.16,54.19-171.47,54.19-262.51s-18.23-179.35-54.19-262.51Z", "l": "M70.85,673.71c0-98.01,24.06-190.63,66.74-272.52l-40.51-72.78c-16.17,26.49-30.48,54.11-42.88,82.78C18.23,494.35,0,582.67,0,673.71s18.23,179.35,54.19,262.51c34.7,80.25,84.36,152.29,147.59,214.14,63.18,61.8,136.74,110.32,218.66,144.2,79.5,32.89,163.63,50.58,250.3,52.64l-31.17-72.48c-317.75-24.2-568.72-284.52-568.72-601.01Z", "t": "M955.56,52.85C870.78,17.79,780.77,0,688,0s-182.78,17.79-267.56,52.85c-70.37,29.11-134.58,69.01-191.32,118.88h117.46c97.84-63.72,215.26-100.88,341.41-100.88s243.58,37.17,341.41,100.88h117.46c-56.76-49.87-120.97-89.77-191.32-118.88Z"};
let markSeq=0;
/* makeMark({d:Verzögerung, t:Dauer, mono:'#fff'}) – mono färbt die Marke einfarbig (z. B. auf Papier oder Karbon) */
function makeMark({cls='',d=0,t=700,mono=null}={}){
  const n=++markSeq, w=el('div','vmark play '+cls);
  w.style.setProperty('--d',d+'ms');w.style.setProperty('--t',t+'ms');
  const defs=MARKPARTS.defs.replace(/id="(g\d)"/g,`id="$1m${n}"`);
  const p=(c,g,d)=>`<path class="${c}" fill="${mono||`url(#${g}m${n})`}" d="${d}"/>`;
  w.innerHTML=`<i class="glow"></i><svg viewBox="0 0 1372 1348" aria-label="VOID"><defs>${defs}</defs>
    ${p('seg-t','g3',MARKPARTS.t)}${p('seg-l','g3',MARKPARTS.l)}${p('seg-r','g3',MARKPARTS.r)}
    ${p('wing','g2',MARKPARTS.wing)}${p('tri','g1',MARKPARTS.tri)}</svg>`;
  return w;
}
/* vor das Theme-CSS, damit das Theme alles überschreiben kann */
document.head.prepend(el('style','',`
.vmark{position:relative;display:block;--d:0ms;--t:700ms}
.vmark svg{position:relative;display:block;width:100%;height:auto;overflow:visible}
.vmark .glow{position:absolute;left:-70%;top:-70%;width:240%;height:240%;border-radius:50%;opacity:0;pointer-events:none;
  background:radial-gradient(circle,rgba(179,3,248,.55) 0,rgba(17,65,228,.28) 30%,transparent 62%)}
.vmark path{transform-box:fill-box;transform-origin:center}
.vmark.play .seg-t{animation:vmT var(--t) cubic-bezier(.2,.9,.2,1) var(--d) both}
.vmark.play .seg-l{animation:vmL var(--t) cubic-bezier(.2,.9,.2,1) calc(var(--d) + var(--t)*.12) both}
.vmark.play .seg-r{animation:vmR var(--t) cubic-bezier(.2,.9,.2,1) calc(var(--d) + var(--t)*.24) both}
.vmark.play .wing{animation:vmW var(--t) cubic-bezier(.2,.9,.2,1) calc(var(--d) + var(--t)*.5) both}
.vmark.play .tri{animation:vmTri var(--t) cubic-bezier(.2,.9,.25,1.15) calc(var(--d) + var(--t)*.85) both}
.vmark.play .glow{animation:vmGlow calc(var(--t)*1.4) ease-out calc(var(--d) + var(--t)*1.25) both}
.vmark.noglow .glow{display:none}
@keyframes vmT{from{opacity:0;transform:translateY(-70%) rotate(-30deg)}}
@keyframes vmL{from{opacity:0;transform:translateX(-80%) rotate(-50deg)}}
@keyframes vmR{from{opacity:0;transform:translateX(80%) rotate(50deg)}}
@keyframes vmW{from{opacity:0;transform:translateY(-40%) scale(.8)}}
@keyframes vmTri{from{opacity:0;transform:scale(.15) rotate(180deg)}}
@keyframes vmGlow{0%{opacity:0;transform:scale(.5)}30%{opacity:1}100%{opacity:0;transform:scale(1.25)}}
.goals.empty,.msg.gone{display:none}
.goal{--p:0}
.g-fill{transform-origin:0 50%;transform:scaleX(var(--p));transition:transform 1.4s cubic-bezier(.2,.8,.2,1)}
`));

/* =========================================================
   Bridge-Zustand und Hooks
   Schnittstelle (Server-Sent Events unter /events, JSON pro Nachricht):
     {type:'follow'|'sub'|'resub'|'gift'|'cheer'|'raid'|'redeem', user, amount, months, tier, title, text}
     {type:'state', paused, volume, sounds, latest, session, goals, counts, show_latest, latest_items}
     {type:'chat', id, uid, user, color, badges, frags} · chat_delete · chat_delete_user · chat_clear
     {type:'badges', map} · {type:'control', action:'skip'} · {type:'telemetry', data} · {type:'irl', live, since}
     {type:'info', data:{Label: Text}} – Textquellen „Info · …“ aus OBS
   ========================================================= */
let STATE={paused:false,volume:70,sounds:{},latest:{},session:null,goals:[],counts:{}};
let BADGES={};
const hooks={state:[],chat:[],tele:[],irl:[]};
const onState=f=>{hooks.state.push(f);f(STATE)};
const onTele=f=>hooks.tele.push(f);
const onIrl=f=>hooks.irl.push(f);
let THEME={};

const tier=t=>t?` · Stufe ${t}`:'';
const FMT={
  follow:e=>['Neuer Follow','Danke fürs Folgen'],
  sub:   e=>['Neues Abo',(e.tier?`Stufe ${e.tier}`:'')],
  resub: e=>['Abo verlängert',`${e.months} Monate${tier(e.tier)}`],
  gift:  e=>[e.amount>1?'Abos verschenkt':'Abo verschenkt',`${e.amount} ${e.amount>1?'Abos':'Abo'}${tier(e.tier)}`],
  cheer: e=>['Bits',`${num(e.amount)} Bits`],
  raid:  e=>['Raid',`mit ${e.amount} ${e.amount==1?'Person':'Leuten'}`],
  redeem:e=>['Kanalpunkte',e.title||''],
};
/* große Momente: Raid, ab 5 Geschenk-Abos, ab 1.000 Bits */
const isBig=e=>e.type==='raid'||(e.type==='gift'&&e.amount>=5)||(e.type==='cheer'&&e.amount>=1000);

/* ---------- Sound: eigene Datei aus %APPDATA%\VOID-Bridge\sounds oder eingebauter Klang ---------- */
let AC=null;
function chime(type,vol){
  try{AC=AC||new AudioContext();if(AC.state==='suspended')AC.resume();
    const base={follow:523.25,sub:440,resub:440,gift:392,cheer:587.33,raid:329.63,redeem:493.88}[type]||440;
    const steps={raid:[1,1.26,1.5,2,2.52],gift:[1,1.5,2,2.52],cheer:[1,1.26,1.5,2]}[type]||[1,1.5,2];
    const t0=AC.currentTime+.02,out=AC.createGain();out.gain.value=vol*.5;out.connect(AC.destination);
    steps.forEach((m,i)=>{[['sine',1,.5],['triangle',.5,.18]].forEach(([w,o8,g])=>{
      const o=AC.createOscillator(),e=AC.createGain();o.type=w;o.frequency.value=base*m*o8;
      const t=t0+i*.11;e.gain.setValueAtTime(0,t);e.gain.linearRampToValueAtTime(g,t+.012);
      e.gain.exponentialRampToValueAtTime(.0001,t+1.8);o.connect(e).connect(out);o.start(t);o.stop(t+1.9)})});
  }catch(_){}
}
function playSound(type){
  const v=(STATE.volume??70)/100;if(v<=0)return;
  const src=STATE.sounds&&(STATE.sounds[type]||STATE.sounds.default);
  if(src){const a=new Audio(src);a.volume=v;a.play().catch(()=>chime(type,v))}else chime(type,v);
}

/* ---------- Alert-Warteschlange mit Pause und Überspringen ----------
   THEME.alert(e,{kind,detail,big,hold}) baut den Alert auf, wartet mit await hold() und räumt wieder ab. */
const alertBox=el('div','alerts');
const AQ=[];let busy=false,skipNow=null;
const holdFor=ms=>new Promise(r=>{skipNow=r;setTimeout(r,ms)});
function pushAlert(e){if(!ALERTS||!FMT[e.type]||!THEME.alert)return;AQ.push(e);if(!busy)nextAlert()}
async function nextAlert(){
  if(!AQ.length){busy=false;return}busy=true;
  while(STATE.paused)await wait(300);
  const e=AQ.shift(),[kind,detail]=FMT[e.type](e);
  try{await THEME.alert(e,{kind,detail,big:isBig(e),name:(e.user||'Anonym').slice(0,25),
    hold:async()=>{await holdFor(e.text?8000:5500);skipNow=null},sound:()=>playSound(e.type)})}catch(_){}
  await wait(500);nextAlert();
}

/* ---------- Ziele: .goal > .g-top(.g-l .g-v) + .g-track > .g-fill; --p ist der Anteil 0…1 ---------- */
function goalsInto(box){
  const map={};
  onState(s=>{
    const gs=s.goals||[],keys=new Set(gs.map(g=>g.key));
    Object.keys(map).forEach(k=>{if(!keys.has(k)){map[k].remove();delete map[k]}});
    gs.forEach(g=>{
      let d=map[g.key];
      if(!d){d=el('div','goal');d.innerHTML='<div class="g-top"><span class="g-l"></span><span class="g-v"></span></div><div class="g-track"><div class="g-fill"></div></div>';
        box.appendChild(d);map[g.key]=d}
      const full=g.cur>=g.target;d.classList.toggle('full',full);
      d.querySelector('.g-l').textContent=full?'Ziel erreicht':g.label;
      d.querySelector('.g-v').textContent=`${num(g.cur)} / ${num(g.target)}`;
      requestAnimationFrame(()=>requestAnimationFrame(()=>d.style.setProperty('--p',Math.max(0,Math.min(1,g.cur/g.target)))));
    });
    box.classList.toggle('empty',!gs.length);
  });
}

/* ---------- Letzte Unterstützer (in VOID Studio an/aus und Auswahl) ---------- */
const LT_LBL={follow:'Letzter Follow',sub:'Letztes Abo',gift:'Letztes Geschenk',cheer:'Letzte Bits',raid:'Letzter Raid'};
function latest(max=5){
  const s=STATE,L=s.latest||{};
  return (s.show_latest===false?[]:(s.latest_items||['follow','sub','cheer'])).filter(k=>L[k]).slice(0,max)
    .map(k=>({key:k,label:LT_LBL[k],user:L[k].user,amount:L[k].amount,value:L[k].user+(L[k].amount&&k!=='sub'&&k!=='follow'?` · ${num(L[k].amount)}`:'')}));
}
function latestInto(box,{max=5}={}){
  onState(()=>{
    const items=latest(max);box.innerHTML='';
    items.forEach(i=>{const d=el('div','goal lt '+i.key);d.innerHTML='<div class="g-top"><span class="g-l"></span><span class="g-v"></span></div>';
      d.querySelector('.g-l').textContent=i.label;d.querySelector('.g-v').textContent=i.value;box.appendChild(d)});
    box.classList.toggle('empty',!items.length);
  });
}
const names=(a,n=2)=>a.length<=n?a.join(', '):`${a.slice(0,n).join(', ')} und ${a.length-n} weitere`;
function latestLines(){
  const L=STATE.latest||{},o=[];
  if(L.follow)o.push(`Letzter Follow: ${L.follow.user}`);
  if(L.sub)o.push(`Letztes Abo: ${L.sub.user}`);
  if(L.gift)o.push(`Letztes Geschenk: ${L.gift.user} · ${L.gift.amount}`);
  if(L.cheer)o.push(`Letzte Bits: ${L.cheer.user} · ${num(L.cheer.amount)}`);
  return o;
}
function recapLines(){
  const s=STATE.session;if(!s)return [];
  const o=[],top=obj=>Object.entries(obj||{}).sort((a,b)=>b[1]-a[1]);
  if(s.follows?.length)o.push(`Neu dabei: ${names(s.follows)}`);
  if(s.subs?.length)o.push(`Abos: ${names(s.subs)}`);
  const g=top(s.gifts);if(g.length)o.push(`Verschenkt: ${g.slice(0,2).map(([n,c])=>`${n} (${c})`).join(', ')}`);
  const b=top(s.bits);if(b.length)o.push(`Bits: ${b.slice(0,2).map(([n,c])=>`${n} (${num(c)})`).join(', ')}`);
  (s.raids||[]).slice(-2).forEach(r=>o.push(`Raid: ${r.user} mit ${r.amount}`));
  return o;
}
/* Rückblick als Liste je Person, gewichtet: Raid > Geschenk-Abos > Bits > Abo > Follow (für Klassement, Abspann …) */
function supporters(){
  const s=STATE.session;if(!s)return [];
  const m={},add=(u,w,txt)=>{if(!u)return;const x=m[u]||(m[u]={user:u,score:0,parts:[]});x.score+=w;x.parts.push(txt)};
  (s.raids||[]).forEach(r=>add(r.user,10000+r.amount*50,`Raid mit ${r.amount}`));
  Object.entries(s.gifts||{}).forEach(([u,c])=>add(u,c*500,`${c} ${c>1?'Abos':'Abo'} verschenkt`));
  Object.entries(s.bits||{}).forEach(([u,c])=>add(u,c,`${num(c)} Bits`));
  (s.subs||[]).forEach(u=>add(u,400,'Abo'));
  (s.follows||[]).forEach(u=>add(u,1,'Follow'));
  return Object.values(m).sort((a,b)=>b.score-a.score);
}

/* ---------- Chat: chatInto(box,{max, life}) – life in ms lässt Nachrichten wieder verschwinden ---------- */
function readable(hex,name){
  let h,s=.7,l=.72;
  const m=/^#?([0-9a-f]{6})$/i.exec(hex||'');
  if(m){const n=parseInt(m[1],16),r=(n>>16)/255,g=(n>>8&255)/255,b=(n&255)/255;
    const mx=Math.max(r,g,b),mn=Math.min(r,g,b);l=(mx+mn)/2;
    if(mx===mn){h=0;s=0}else{const d=mx-mn;s=l>.5?d/(2-mx-mn):d/(mx+mn);
      h=mx===r?(g-b)/d+(g<b?6:0):mx===g?(b-r)/d+2:(r-g)/d+4;h*=60}
    l=Math.max(l,.68);s=Math.min(s,.85);
  }else{h=[...(name||'?')].reduce((a,c)=>a+c.charCodeAt(0)*7,0)%360}
  return `hsl(${h|0} ${(s*100)|0}% ${(l*100)|0}%)`;
}
const chatLogs=[];
function chatInto(box,{max=40,life=0,render=null}={}){chatLogs.push({box,max,life,render})}
function chatNode(c){
  const m=el('div','msg');m.dataset.id=c.id||'';m.dataset.uid=c.uid||'';
  const head=el('div','m-head');
  (c.badges||[]).forEach(k=>{if(BADGES[k]){const i=el('img','m-badge');i.src=BADGES[k];i.alt='';head.appendChild(i)}});
  const nm=el('span','m-name');nm.textContent=c.user;nm.style.color=readable(c.color,c.user);m.style.setProperty('--uc',readable(c.color,c.user));head.appendChild(nm);
  const tx=el('div','m-text');
  (c.frags||[]).forEach(f=>{
    if(f.e){const i=el('img','m-emote');i.src=`https://static-cdn.jtvnw.net/emoticons/v2/${f.e}/default/dark/2.0`;i.alt=f.t;tx.appendChild(i)}
    else tx.appendChild(document.createTextNode(f.t));
  });
  m.append(head,tx);return m;
}
function addChat(c){
  chatLogs.forEach(L=>{
    const m=chatNode(c);if(L.render)L.render(m,c);L.box.appendChild(m);
    if(L.life)setTimeout(()=>{m.classList.add('fade');setTimeout(()=>m.remove(),900)},L.life);
    while(L.box.children.length>L.max)L.box.firstChild.remove();
  });
  hooks.chat.forEach(f=>f(c));
}
function chatRemove(sel){chatLogs.forEach(L=>L.box.querySelectorAll(sel).forEach(n=>n.classList.add('gone')))}

/* ---------- Infos aus OBS: Szene „VOID · Infos“, Textquellen „Info · …“ (VOID Studio schickt sie) ----------
   Ein Wert ersetzt den gleichnamigen Parameter der Einstiegsdatei; die Szene lädt dafür einmal neu (nach einem
   laufenden Alert). Leerer Text = Parameter bzw. Standard. Mehrere Zeilen werden zu A|B|C. */
const INFO_KEYS={'Titel':'title','Statuszeilen':'sub','Charakter':'char','Spiel':'game','Entwickler':'dev','Status':'status',
  'Wunschliste':'wish','Spiele des Abends':'games','Strecke':'track','Auto':'car','Serie':'series','Ort':'place','Wetter-Ort':'wx',
  'Splash':'splash','Kamera 1':'cam1','Kamera 2':'cam2','Kamera 3':'cam3','Kamera 4':'cam4'};
function applyInfo(d){
  const want={};
  Object.entries(d||{}).forEach(([label,raw])=>{const k=INFO_KEYS[label];if(!k)return;
    let v=String(raw||'').split(/\r?\n/).map(s=>s.trim()).filter(Boolean).join('|');
    if(k==='wish'&&v)v=/^(ja|an|1|x|yes|true)$/i.test(v)?'1':'0';
    if(v)want[k]=v});
  const h=new URLSearchParams(location.hash.slice(1)),had=(h.get('_info')||'').split(',').filter(Boolean);
  let changed=false;
  had.forEach(k=>{if(!(k in want)){h.delete(k);changed=true}});
  Object.entries(want).forEach(([k,v])=>{if(h.get(k)!==v){h.set(k,v);changed=true}});
  const keys=Object.keys(want).sort().join(',');
  if(keys)h.set('_info',keys);else h.delete('_info');
  if(!changed)return;
  const go=()=>{if(busy)return setTimeout(go,500);history.replaceState(null,'','#'+h.toString());location.reload()};
  go();
}

/* ---------- Verbindung zur Bridge ---------- */
function onMessage(e){
  switch(e.type){
    case 'state':STATE=Object.assign(STATE,e);hooks.state.forEach(f=>f(STATE));break;
    case 'badges':BADGES=e.map||{};break;
    case 'chat':addChat(e);break;
    case 'chat_delete':chatRemove(`[data-id="${CSS.escape(e.id||'')}"]`);break;
    case 'chat_delete_user':chatRemove(`[data-uid="${CSS.escape(e.uid||'')}"]`);break;
    case 'chat_clear':chatLogs.forEach(L=>L.box.innerHTML='');break;
    case 'control':if(e.action==='skip'&&skipNow)skipNow();break;
    case 'telemetry':hooks.tele.forEach(f=>f(e.data));break;
    case 'irl':hooks.irl.forEach(f=>f(e));break;
    case 'info':applyInfo(e.data);break;
    default:pushAlert(e);
  }
}
const SAMPLES=[
  {type:'follow',user:'Nachtfalke'},
  {type:'sub',user:'Sternenstaub',tier:1},
  {type:'resub',user:'Kaelthas_DE',months:14,tier:1,text:'Seit Tag eins dabei!'},
  {type:'gift',user:'Lichtbringerin',amount:5,tier:1},
  {type:'cheer',user:'Runenleser',amount:500,text:'Für neue Server-Hardware'},
  {type:'raid',user:'VOIDCrew',amount:23},
  {type:'redeem',user:'Mondsichel',title:'Trink was!'},
];
function testMode(){
  const S=THEME.samples||{};
  onMessage({type:'state',show_latest:true,latest_items:['follow','sub','cheer'],counts:{followers:412,subs:37},
    latest:{follow:{user:'Nachtfalke'},sub:{user:'Kaelthas_DE'},cheer:{user:'Runenleser',amount:500}},
    session:{follows:['Nachtfalke','Mondsichel','Sternenstaub','Pixelpilot'],subs:['Sternenstaub','Kaelthas_DE'],
      gifts:{Lichtbringerin:5},bits:{Runenleser:500,Abyssgaenger:100},raids:[{user:'VOIDCrew',amount:23}]},
    goals:[{key:'follow',label:'Follower-Ziel',cur:412,target:500},{key:'sub',label:'Abo-Ziel',cur:37,target:50}]});
  BADGES={'broadcaster/1':'https://static-cdn.jtvnw.net/badges/v1/5527c58c-fb7d-422d-b71b-f309dcb85cc1/2'};
  const lines=S.chat||['Guten Abend zusammen!','Was steht heute an?','Das Overlay ist schick','GG!','Wann ist der nächste LAN-Abend?'];
  const who=[['Sternenstaub','#9B6BFF'],['Nachtfalke','#1E90FF'],['Kaelthas_DE',''],['Mondsichel','#FF7F50'],['Runenleser','#2E8B57']];
  let i=0;const tick=()=>{const [u,c]=who[i%who.length];
    addChat({id:'t'+i,uid:u,user:u,color:c,badges:i%5===0?['broadcaster/1']:[],frags:[{t:lines[i%lines.length]+' '},...(i%3===1?[{e:'25',t:'Kappa'}]:[])]});i++};
  for(let k=0;k<(S.chatStart??6);k++)tick();setInterval(tick,S.chatEvery||2600);
  const al=S.alerts||SAMPLES;let j=0;
  setTimeout(()=>{pushAlert(al[j++]);setInterval(()=>pushAlert(al[j++%al.length]),12000)},S.alertDelay??0);
  if(THEME.testExtra)THEME.testExtra();
}
function bridge(){
  if(ALERTS)stage.appendChild(alertBox);
  if(TEST)testMode();
  if(P.get('bridge')==='0')return;
  const url=`http://${P.get('host')||'127.0.0.1'}:${P.get('port')||8787}/events`;
  try{const es=new EventSource(url);es.onmessage=m=>{try{onMessage(JSON.parse(m.data))}catch(_){}}}catch(_){}
}

/* Start: Szene aus ?scene=, sonst start; stinger läuft ohne Bridge (wird als WebM gerendert) */
function boot(scenes,theme={}){
  THEME=theme;
  document.fonts.ready.then(()=>{
    if(SCENE==='stinger'){
      const build=()=>{stage.innerHTML='';const r=el('div','');r.id='stg';stage.appendChild(r);scenes.stinger(r)};
      build();if(P.get('render')!=='1')setInterval(build,2600);return;
    }
    if(SCENE==='goals'){const gb=el('div','goals stack');gb.style.cssText='position:absolute;left:48px;top:48px;width:380px';stage.appendChild(gb);goalsInto(gb)}
    else if(SCENE!=='alerts')(scenes[SCENE]||scenes.start)();
    bridge();
  });
}
