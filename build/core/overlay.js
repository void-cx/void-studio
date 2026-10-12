/* =========================================================
   Einblendungen aus VOID Studio (build/core/overlay.js) – gemeinsam für alle Packs und die Vorschau der Oberfläche.
   packs.py setzt diese Datei in jedes Pack ein, embed_web.py in die Oberfläche (Markierung @OVERLAY@).

   Nachricht {type:'overlay', o:{template, pos, margin, size, width, title, line, media, video, color, bg, anim, secs, sound, volume}}
   Vorlagen: card (Karte mit Bild), banner (Leiste), media (nur Bild/Video), text (nur Text).
   „pack“ zeigt die Szene als Alert im eigenen Stil (ovlHost). Farbe und Titelschrift kommen aus dem Pack
   (--ovl-acc, --ovl-font), eine eigene Farbe in o.color geht vor.
   ========================================================= */
const OVL_SIZE={card:{s:360,m:480,l:640},banner:{s:64,m:88,l:120},media:{s:320,m:480,l:720},text:{s:44,m:64,l:96}};
const OVL_CSS=`
.ovl-pos{position:absolute;z-index:60;pointer-events:none}
.ovl{--a:var(--ovl-acc,#B303F8);color:#F5F6FA;font-family:var(--ovl-body,inherit);opacity:0;
  transition:opacity .45s ease,transform .6s cubic-bezier(.2,.9,.25,1)}
.ovl.o-in{opacity:1;transform:none!important}
.ovl.o-pop{transform:scale(.55)}.ovl.o-from-l{transform:translateX(-120px)}.ovl.o-from-r{transform:translateX(120px)}
.ovl.o-from-t{transform:translateY(-120px)}.ovl.o-from-b{transform:translateY(120px)}
.ovl .o-t{font-family:var(--ovl-font,inherit);font-weight:700;line-height:1.08;overflow-wrap:anywhere}
.ovl .o-l{opacity:.86;line-height:1.3;overflow-wrap:anywhere}
.ovl .o-m{display:block;width:100%;height:auto}
.ovl.o-bg-solid{background:#0C0E1E;border:1px solid rgba(255,255,255,.10)}
.ovl.o-bg-glass{background:rgba(8,8,24,.70);border:1px solid rgba(255,255,255,.14);backdrop-filter:blur(12px)}
.ovl.o-bg-none .o-t,.ovl.o-bg-none .o-l{text-shadow:0 2px 14px rgba(0,0,0,.75),0 0 2px rgba(0,0,0,.9)}
.ovl.o-card{width:calc(var(--w)*1px);border-radius:14px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.45)}
.ovl.o-card.bg-none{box-shadow:none}
.ovl.o-card .o-m{max-height:calc(var(--w)*.75px);object-fit:cover}
.ovl.o-card .o-b{padding:calc(var(--w)*.045px) calc(var(--w)*.055px);border-top:4px solid var(--a)}
.ovl.o-card .o-t{font-size:calc(var(--w)*.066px)}.ovl.o-card .o-l{font-size:calc(var(--w)*.042px);margin-top:calc(var(--w)*.014px)}
.ovl.o-banner{display:flex;align-items:center;gap:calc(var(--h)*.3px);height:calc(var(--h)*1px);border-radius:10px;overflow:hidden;
  padding-right:calc(var(--h)*.4px);border-left:calc(var(--h)*.09px) solid var(--a)}
.ovl.o-banner .o-m{width:auto;height:100%;flex:none}
.ovl.o-banner .o-x{display:flex;align-items:baseline;gap:calc(var(--h)*.3px);min-width:0;padding-left:calc(var(--h)*.25px)}
.ovl.o-banner .o-t{font-size:calc(var(--h)*.4px);white-space:nowrap}
.ovl.o-banner .o-l{font-size:calc(var(--h)*.28px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ovl.o-media{width:calc(var(--w)*1px);border-radius:12px;overflow:hidden}
.ovl.o-media.bg-none{border-radius:0}
.ovl.o-text{text-align:center;padding:calc(var(--w)*.25px) calc(var(--w)*.45px);border-radius:14px}
.ovl.o-text .o-t{font-size:calc(var(--w)*1px)}.ovl.o-text .o-l{font-size:calc(var(--w)*.5px);margin-top:calc(var(--w)*.12px)}
.ovl.o-text .o-t{color:var(--a)}
`;
function ovlCss(doc=document){
  if(doc.getElementById('ovl-css'))return;
  const s=doc.createElement('style');s.id='ovl-css';s.textContent=OVL_CSS;doc.head.prepend(s);   /* vorne: Packs dürfen überschreiben */
}
/* Aufbau ohne Animation; Wrapper sitzt an der Position, das innere Element wird animiert */
function ovlNode(o){
  ovlCss();
  const tpl=OVL_SIZE[o.template]?o.template:'card',sz=OVL_SIZE[tpl],m=Math.max(0,+o.margin||0);
  const size=o.size==='custom'?Math.max(16,Math.min(1920,+o.width||sz.m)):(sz[o.size]||sz.m);
  const pos=/^[tmb][lcr]$/.test(o.pos||'')?o.pos:'tc',row=pos[0],col=pos[1];
  const wrap=document.createElement('div');wrap.className='ovl-pos';
  const st=wrap.style,tf=[];
  if(tpl==='banner'){st.left=m+'px';st.right=m+'px'}
  else if(col==='l')st.left=m+'px';else if(col==='r')st.right=m+'px';else{st.left='50%';tf.push('translateX(-50%)')}
  if(row==='t')st.top=m+'px';else if(row==='b')st.bottom=m+'px';else{st.top='50%';tf.push('translateY(-50%)')}
  if(tf.length)st.transform=tf.join(' ');
  const box=document.createElement('div');
  const from=tpl==='banner'?(row==='b'?'b':'t'):col==='l'?'l':col==='r'?'r':row==='b'?'b':'t';
  box.className=`ovl o-${tpl} o-bg-${['solid','glass','none'].includes(o.bg)?o.bg:'glass'} ${o.anim==='pop'?'o-pop':o.anim==='fade'?'':'o-from-'+from}`;
  box.style.setProperty(tpl==='banner'?'--h':'--w',size);
  if(/^#[0-9a-fA-F]{6}$/.test(o.color||''))box.style.setProperty('--a',o.color);
  let media=null;
  if(o.media&&tpl!=='text'){
    media=document.createElement(o.video?'video':'img');media.className='o-m';media.src=o.media;
    if(o.video){media.autoplay=true;media.loop=true;media.playsInline=true;media.muted=!!o.sound||!!o.mute}
    else media.alt='';
  }
  const t=document.createElement('div');t.className='o-t';t.textContent=o.title||'';
  const l=document.createElement('div');l.className='o-l';l.textContent=o.line||'';
  if(tpl==='media'){if(media)box.append(media)}
  else if(tpl==='banner'){if(media)box.append(media);const x=document.createElement('div');x.className='o-x';x.append(t);if(o.line)x.append(l);box.append(x)}
  else if(tpl==='text'){box.append(t);if(o.line)box.append(l)}
  else{if(media)box.append(media);const b=document.createElement('div');b.className='o-b';b.append(t);if(o.line)b.append(l);box.append(b)}
  wrap.append(box);
  return {wrap,box,media};
}
/* Ein-, Stehen-, Ausblenden. hold(ms) kann der Host ersetzen (Überspringen); volume = Gesamtlautstärke 0…1 */
async function ovlPlay(o,root,{hold=null,volume=1}={}){
  const n=ovlNode(o),pause=ms=>new Promise(r=>setTimeout(r,ms));
  root.append(n.wrap);
  if(n.media&&n.media.play){n.media.volume=Math.max(0,Math.min(1,volume*(o.volume??100)/100));n.media.play().catch(()=>{})}
  await pause(40);n.box.classList.add('o-in');
  if(o.sound){const v=volume*(o.volume??100)/100;if(v>0){const a=new Audio(o.sound);a.volume=Math.min(1,v);a.play().catch(()=>{})}}
  const ms=Math.max(1,Math.min(120,+o.secs||6))*1000;
  await (hold?hold(ms):pause(ms));
  n.box.classList.remove('o-in');await pause(650);n.wrap.remove();
}
/* In den Szenen: eigene Warteschlange neben den Alerts, hält bei „Pausieren“ an */
const OQ=[];let ovlBusy=false;
function ovlHost(o){
  if(typeof ALERTS!=='undefined'&&!ALERTS)return;
  if(o.template==='pack'){
    pushAlert({type:o.event||'redeem',user:o.user||'',title:o.title,texts:[o.title||'',o.line||''],hold:Math.max(1,+o.secs||6)*1000,sound:o.sound||''});
    return;
  }
  OQ.push(o);if(!ovlBusy)ovlNext();
}
async function ovlNext(){
  if(!OQ.length){ovlBusy=false;return}ovlBusy=true;
  while(STATE.paused)await new Promise(r=>setTimeout(r,300));
  try{await ovlPlay(OQ.shift(),stage,{volume:(STATE.volume??70)/100})}catch(_){}
  ovlNext();
}
