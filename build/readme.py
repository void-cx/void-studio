"""LIESMICH.md je Pack aus der Beschreibung in themes/<id>.json; ein eigenes Kapitel kommt aus themes/<id>.md.

readme-Felder (alle optional außer stinger):
  name          Spielname im Text (Standard: label)
  for           statt „für <name>“, z. B. „ohne Spielbezug“
  game_scenes   wie die Spielszenen heißen (Standard: „<name>-Overlay“)
  cam           wo die Game-Kamera sitzt (Standard: „unten rechts“)
  stinger       Beschreibung des Übergangs
  logo          eigener Satz zur Logo-Animation
  file          eigene, vollständige LIESMICH (dann gilt nichts von oben)
"""
import os
import sys
import themes

PACKS = 'dist/packs'
WORDS = {5: 'Fünf', 6: 'Sechs', 7: 'Sieben', 8: 'Acht', 9: 'Neun'}


def text(t):
    r = t.get('readme', {})
    if r.get('file'):
        return open(r['file'], encoding='utf-8').read()
    g = r.get('name', t['label'])
    gn = t['game']
    coll = t.get('collname', f'VOID × {gn}')
    cap = t.get('capname', f'{gn} Spielaufnahme')
    infos = ', '.join(f'„{x}“' for x in ['Titel', 'Statuszeilen'] + t.get('infos', []))
    logo = r.get('logo', 'Start, Pause und Ende bauen die Bildmarke beim Szenenwechsel auf. Bei Raids, ab 5 Geschenk-Abos und ab 1.000 Bits auch im Alert.')
    out = f"""# VOID Szenen-Pack: {g}

{WORDS[len(t['scenes'])]} OBS-Szenen im VOID-Design {r.get('for', 'für ' + g)} (Stream startet, Kurze Pause, Stream endet, Just Chatting, {r.get('game_scenes', g + '-Overlay')}), ein eigener Szenenübergang, verwaltet über VOID Studio. Vorschau in `preview/`.

## Installation

1. Einmalig VOID Studio einrichten: Python 3.11 oder 3.12 (64 Bit) installieren und in OBS unter Werkzeuge → Skripte → Python-Einstellungen eintragen. Dann `void-studio.py` aus dem neuesten Release unter Werkzeuge → Skripte → `+` hinzufügen.
2. Im VOID-Studio-Fenster „{g}“ auswählen und „Installieren / aktualisieren“ klicken. VOID Studio richtet die Szenensammlung dabei gleich in OBS ein.
3. OBS einmal neu starten (OBS liest Szenensammlungen nur beim Start ein), dann Szenensammlung → „{coll}“ wählen. (Alternativ wie bisher: Szenensammlung → Importieren → `import.json` aus dem Pack-Ordner.)
4. Kamera-Gerät und bei „{cap}“ das Spielfenster wählen.
5. „Mit Twitch verbinden“ – nur einmal für alle Packs.

Updates: „Nach Updates suchen“ und „Alle Pack-Updates installieren“. Die Szenen übernehmen neue Versionen sofort; nur wenn sich die Szenen selbst ändern, meldet VOID Studio das. Dann kurz eine andere Szenensammlung wählen und „In OBS einrichten“ klicken – Kamera, Spielaufnahme und eigene Quellen bleiben erhalten.

## Texte anpassen

In der VOID-Studio-Oberfläche unter **Infos** (im Skript-Fenster „Im Browser öffnen“ oder als Dock in OBS): {infos}. Die Overlays übernehmen Änderungen sofort. Leer heißt Standard, mehrere Zeilen werden zu wechselnden Zeilen bzw. einer Liste.

## Inhalt

| Pfad | Zweck |
| --- | --- |
| `import.json` | Die Datei für OBS (Szenensammlung → Importieren). Erzeugt VOID Studio beim Installieren mit den Pfaden deines Rechners |
| `_vorlage/import.template.json` | Vorlage dafür; nicht in OBS importieren. VOID Studio braucht sie, um `import.json` neu zu erzeugen |
| `pack.json` | Name, Version und Szenen-Fingerabdruck für Updates |
| `obs/` | Einstiegsdateien der Browserquellen. Feste Parameter hier anhängen, z. B. `#scene=game&cam=bl` |
| `scenes.html` | Alle Szenen. Im Browser testen: `scenes.html?scene=start&test=1&demo=1` |
| `assets/transition.webm` | Szenenübergang: 1,95 s, transparent, Umschaltpunkt 600 ms |
| `assets/` | Schriften mit Lizenzen, VOID-Bildmarke, Lockup |
| `preview/` | Vorschaubilder |

**Übergang:** {r['stinger']}.

**Logo-Animation:** {logo}

**Game-Kamera:** sitzt {r.get('cam', 'unten rechts')}, verschiebbar über `obs/game.html`.

**Letzte Unterstützer in Spielszenen:** In den Skript-Einstellungen der Bridge an- und ausschaltbar, dazu Häkchen für Follow, Abo, Geschenk, Bits und Raid. Erscheint an der Game-Kamera über den Zielen.

**Bridge-Daten:** Login, Sounds und Session liegen zentral in `%APPDATA%\\VOID-Bridge\\`, gemeinsam für alle Packs. Eigene Sounds lädst du in der VOID-Studio-Oberfläche unter **Alerts** hoch (dort auch Lautstärke, Mindestwerte, Texte und Kanalpunkt-Regeln); sie liegen in `%APPDATA%\\VOID-Bridge\\sounds\\` (`follow.mp3`, `sub.mp3`, `resub.mp3`, `gift.mp3`, `cheer.mp3`, `raid.mp3`, `redeem.mp3` oder `default.mp3`). Die Token-Datei dort wie ein Passwort behandeln.
"""
    extra = f"themes/{t['id']}.md"
    if os.path.isfile(extra):
        out += open(extra, encoding='utf-8').read()
    return out


for t in themes.load(sys.argv[1:]):
    d = os.path.join(PACKS, f"void-theme-{t['id']}")
    if os.path.isdir(d):
        with open(os.path.join(d, 'LIESMICH.md'), 'w', encoding='utf-8') as f:
            f.write(text(t))
