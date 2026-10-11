#!/usr/bin/env bash
# Baut alle Szenen-Packs, rendert die Übergänge und Vorschauen und erzeugt das Release in dist/release/.
# Voraussetzungen: Python 3.11+, pip install playwright pillow numpy && playwright install chromium, ffmpeg
set -euo pipefail
cd "$(dirname "$0")"
for t in wd mc ets gta void; do python3 make_$t.py >/dev/null; done
python3 packs.py "$@"
python3 stg.py render "$@"
python3 prev_packs.py "$@"
bash readme.sh
python3 build_release.py
echo "Fertig: dist/release/"
