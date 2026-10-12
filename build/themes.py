"""Pack-Beschreibungen aus themes/<id>.json – eine Datei je Szenen-Pack, alles Weitere (Build, Prüfung, Vorschauen,
Übergang, LIESMICH) liest von hier. Neues Pack: Beschreibung anlegen, Version in versions.json eintragen.

Felder:
  id, order, label            Pack-ID (Ordner void-theme-<id>), Reihenfolge, Name in VOID Studio
  game                        Spielname in Szenen- und Quellennamen („GTA Spielaufnahme“, Sammlung „VOID × GTA“)
  capname, collname           optional: Name der Spielaufnahme bzw. der Szenensammlung
  generator                   optional: make_*.py, das das Template aus tpl.html ableitet (ältere Packs)
  template                    HTML der Szenen; mit "core": true wird /*@CORE@*/ durch core/core.js ersetzt
  layout                      "game" (Start, Pause, Ende, Just Chatting, Spiel) oder "irl" (Kameras statt Spiel)
  cam                         Position der Game-Kamera (416 × 234) im Layout "game"
  scenes                      Einstiegsdateien obs/<scene>.html, in dieser Reihenfolge; geprüft von smoke.py
  game_params                 optional: Parameter, die obs/game.html anhängt
  infos                       optional: weitere Felder für die Szene „VOID · Infos“ in OBS (Titel und Statuszeilen gibt es immer);
                              Namen wie in INFO_KEYS in core/core.js
  script_settings             optional: Voreinstellungen für VOID Studio in der Szenensammlung
  fonts, licenses             Schriften {Platzhalter: [Dateiname, Quelle]} und Lizenzen {Name: fontsource-Ordner}
  extra                       optional: Ordner, dessen Dateien nach assets/ kopiert werden
  previews                    [[Name, Query, Wartezeit ms], …] für prev_packs.py
  readme                      Texte für LIESMICH.md (siehe readme.py) oder {"file": …} für eine eigene
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(only=None):
    out = []
    for f in glob.glob(os.path.join(HERE, 'themes', '*.json')):
        t = json.load(open(f, encoding='utf-8'))
        assert t['id'] == os.path.basename(f)[:-5], f'{f}: id passt nicht zum Dateinamen'
        if not only or t['id'] in only:
            out.append(t)
    return sorted(out, key=lambda t: (t.get('order', 99), t['id']))


if __name__ == '__main__':
    import sys
    # python3 themes.py generators  → die make_*.py, die vor packs.py laufen müssen
    if sys.argv[1:] == ['generators']:
        print(' '.join(t['generator'] for t in load() if t.get('generator')))
    else:
        print(' '.join(t['id'] for t in load()))
