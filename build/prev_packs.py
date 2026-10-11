import asyncio
from playwright.async_api import async_playwright
from PIL import Image
import os
P=os.path.abspath('dist/packs')
SHOTS=[('start','scene=start&test=1',7500),('chat','scene=chat&demo=1&test=1',8000),('game','scene=game&demo=1&test=1',4000),('end','scene=end&test=1',16500)]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1920,'height':1080})
        bad=[];pg.on('requestfailed',lambda r:bad.append(r.url))
        import sys
        for theme in (sys.argv[1:] or [t for t in ['aion2','wardogs','minecraft','ets2','gta','void'] if os.path.isdir(f'{P}/void-theme-{t}')]):
            for name,q,ms in SHOTS+([('drive','scene=drive&demo=1&test=1',5000)] if theme=='ets2' else []):
                await pg.goto(f'file://{P}/void-theme-{theme}/scenes.html?{q}&bridge=0');await pg.wait_for_timeout(ms)
                fonts=await pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family+' '+f.weight)")
                f=f'{P}/void-theme-{theme}/preview/{name}.png';await pg.screenshot(path=f)
                Image.open(f).convert('RGB').resize((960,540),Image.LANCZOS).save(f.replace('.png','.jpg'),quality=85)
                import os;os.remove(f)
            print(theme,'fonts geladen:',sorted(set(fonts)))
        print('fehlgeschlagene Requests (ohne Twitch-CDN):',[u for u in bad if 'jtvnw' not in u])
        await b.close()
asyncio.run(main())
