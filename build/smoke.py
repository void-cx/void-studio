"""Schnellprüfung: jede Szene jedes gebauten Packs im Browser öffnen (Testdaten) und auf JS-Fehler prüfen."""
import asyncio, os, sys
from playwright.async_api import async_playwright
P = os.path.abspath('dist/packs')
SC = ['start', 'pause', 'end', 'chat', 'game', 'drive', 'alerts', 'goals', 'stinger']

async def main():
    fails = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for d in sorted(os.listdir(P)):
            pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            for sc in SC:
                if sc == 'drive' and d != 'void-theme-ets2':
                    continue
                errs.clear()
                await pg.goto(f'file://{P}/{d}/scenes.html?scene={sc}&test=1&demo=1&bridge=0')
                await pg.wait_for_timeout(1500)
                if errs:
                    fails.append(f'{d} / {sc}: {errs[0]}')
            missing = [f for f in ('pack.json', '_vorlage/import.template.json', 'scenes.html') if not os.path.isfile(f'{P}/{d}/{f}')]
            if missing:
                fails.append(f'{d}: fehlt {", ".join(missing)}')
            await pg.close()
            print(f'{d}: ok' if not any(x.startswith(d) for x in fails) else f'{d}: FEHLER')
        await b.close()
    if fails:
        print('\n'.join(fails))
        sys.exit(1)

asyncio.run(main())
