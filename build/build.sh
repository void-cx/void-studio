#!/usr/bin/env bash
# Baut alle Szenen-Packs, rendert die Übergänge und Vorschauen und erzeugt das Release in dist/release/.
# Voraussetzungen: Python 3.11+, pip install -r requirements.txt && playwright install chromium, ffmpeg
set -euo pipefail
cd "$(dirname "$0")"
for g in $(python3 themes.py generators); do python3 "$g" >/dev/null; done   # ältere Packs: Template aus tpl.html ableiten
python3 packs.py "$@"
python3 stg.py render "$@"
python3 prev_packs.py "$@"
python3 readme.py
python3 build_release.py
echo "Fertig: dist/release/"
