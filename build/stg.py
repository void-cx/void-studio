import asyncio,sys,os,shutil,subprocess
from playwright.async_api import async_playwright
from PIL import Image
import os
import themes
P=os.path.abspath('dist/packs'); FPS=60; DUR=1.95
async def frames(pg,theme,times,outdir):
    await pg.goto(f'file://{P}/void-theme-{theme}/scenes.html?scene=stinger&render=1&bridge=0&alerts=0')
    await pg.evaluate("document.fonts.ready");await pg.wait_for_timeout(400)
    for i,t in enumerate(times):
        await pg.evaluate("t=>document.getAnimations().forEach(a=>{a.pause();a.currentTime=t})",t)
        await pg.screenshot(path=f'{outdir}/{i:04d}.png',omit_background=True)
async def main(mode):
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1920,'height':1080})
        pg.on('pageerror',lambda e:print('ERR',e))
        for theme in [t['id'] for t in themes.load(sys.argv[2:]) if os.path.isdir(f"{P}/void-theme-{t['id']}")]:
            if mode=='check':
                d=f'/tmp/chk_{theme}';shutil.rmtree(d,ignore_errors=True);os.makedirs(d)
                ts=[250,520,900,1300,1650];await frames(pg,theme,ts,d)
                ims=[Image.open(f'{d}/{i:04d}.png').convert('RGBA') for i in range(len(ts))]
                sheet=Image.new('RGBA',(480*len(ts),270),(40,90,40,255))   # grüner Grund zeigt Transparenz
                for i,im in enumerate(ims): sheet.alpha_composite(im.resize((480,270)),(480*i,0))
                sheet.convert('RGB').save(f'/tmp/sheet_{theme}.png')
            else:
                d=f'/tmp/fr_{theme}';shutil.rmtree(d,ignore_errors=True);os.makedirs(d)
                n=int(DUR*FPS);await frames(pg,theme,[i*1000/FPS for i in range(n+1)],d)
                import numpy as np
                cov=[i for i in range(n+1) if np.array(Image.open(f'{d}/{i:04d}.png').convert('RGBA'))[:,:,3].min()==255]
                print(theme,'voll deckend Frames',cov[0],'bis',cov[-1],'=',round(cov[0]*1000/FPS),'-',round(cov[-1]*1000/FPS),'ms')
                out=f'{P}/void-theme-{theme}/assets/transition.webm'
                subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{d}/%04d.png','-c:v','libvpx-vp9',
                  '-pix_fmt','yuva420p','-auto-alt-ref','0','-b:v','6M','-row-mt','1',out],check=True)
                print(theme,os.path.getsize(out)//1024,'KB')
        await b.close()
asyncio.run(main(sys.argv[1]))
