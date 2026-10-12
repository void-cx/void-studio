import asyncio
from playwright.async_api import async_playwright
from PIL import Image
import os
import sys
import themes
P=os.path.abspath('dist/packs')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1920,'height':1080})
        bad=[];pg.on('requestfailed',lambda r:bad.append(r.url))
        for t in themes.load(sys.argv[1:]):
            theme=t['id']
            if not os.path.isdir(f'{P}/void-theme-{theme}'): continue
            for name,q,ms in t['previews']:      # Name, Query, Wartezeit – aus themes/<id>.json
                await pg.goto(f'file://{P}/void-theme-{theme}/scenes.html?{q}&bridge=0');await pg.wait_for_timeout(ms)
                fonts=await pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family+' '+f.weight)")
                f=f'{P}/void-theme-{theme}/preview/{name}.png';await pg.screenshot(path=f)
                Image.open(f).convert('RGB').resize((960,540),Image.LANCZOS).save(f.replace('.png','.jpg'),quality=85)
                os.remove(f)
            print(theme,'fonts geladen:',sorted(set(fonts)))
        print('fehlgeschlagene Requests (ohne Twitch-CDN):',[u for u in bad if 'jtvnw' not in u])
        await b.close()
asyncio.run(main())
