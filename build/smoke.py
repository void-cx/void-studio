"""Schnellprüfung: jede Szene jedes gebauten Packs im Browser öffnen (Testdaten) und auf JS-Fehler prüfen."""
import asyncio, os, sys
import themes
from playwright.async_api import async_playwright
P = os.path.abspath('dist/packs')
EXTRA = ['alerts', 'goals', 'stinger']          # gibt es in jedem Pack zusätzlich zu den Einstiegsdateien

async def main():
    fails = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for t in themes.load(sys.argv[1:]):
            d = f"void-theme-{t['id']}"
            if not os.path.isdir(f'{P}/{d}'):
                fails.append(f'{d}: nicht gebaut')
                continue
            pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            for sc in t['scenes'] + EXTRA:
                errs.clear()
                await pg.goto(f'file://{P}/{d}/scenes.html?scene={sc}&test=1&demo=1&bridge=0')
                await pg.wait_for_timeout(1500)
                if errs:
                    fails.append(f'{d} / {sc}: {errs[0]}')
            missing = [f for f in ('pack.json', '_vorlage/import.template.json', 'scenes.html') + tuple(f'obs/{s}.html' for s in t['scenes'])
                       if not os.path.isfile(f'{P}/{d}/{f}')]
            if missing:
                fails.append(f'{d}: fehlt {", ".join(missing)}')
            await pg.close()
            print(f'{d}: ok' if not any(x.startswith(d) for x in fails) else f'{d}: FEHLER')
        await b.close()
    if fails:
        print('\n'.join(fails))
        sys.exit(1)

asyncio.run(main())
