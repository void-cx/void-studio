"""Web-Oberfläche (studio/web.html) in studio/void-studio.py einbetten – das Skript bleibt eine einzelne Datei.
python3 embed_web.py          einbetten
python3 embed_web.py --check  nur prüfen, ob beide gleich sind (CI)"""
import os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'studio')
START, END = 'WEB_HTML = r"""', '"""  # Ende WEB_HTML'
html = open(os.path.join(ROOT, 'web.html'), encoding='utf-8').read()
# Einblendungen: derselbe Baustein wie in den Packs, für die Vorschau im Editor
html = html.replace('/*@OVERLAY@*/', open(os.path.join(ROOT, '..', 'build', 'core', 'overlay.js'), encoding='utf-8').read())
assert '"""' not in html and not html.endswith('\\'), 'web.html darf keine """ enthalten'
py_path = os.path.join(ROOT, 'void-studio.py')
py = open(py_path, encoding='utf-8').read()
block = START + html + END
if START in py:
    a = py.index(START); b = py.index(END, a) + len(END)
    new = py[:a] + block + py[b:]
else:
    new = py.rstrip('\n') + '\n\n\n# ---------------------------------------------------------------- Web-Oberfläche (aus studio/web.html, build/embed_web.py)\n' + block + '\n'
if '--check' in sys.argv:
    if new != py:
        sys.exit('studio/web.html ist nicht in void-studio.py eingebettet: python3 build/embed_web.py')
    print('Web-Oberfläche eingebettet: ok')
else:
    open(py_path, 'w', encoding='utf-8').write(new)
    print('eingebettet')
