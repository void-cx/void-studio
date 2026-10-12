# VOID Szenen-Pack: IRL

Neun OBS-Szenen für Streams unterwegs, mit einer bis vier Kameras: Stream startet, Unterwegs, Zwei Kameras, Bild im Bild, Vier Kameras, Just Chatting, Kurze Pause, Verbindung weg, Stream endet. Dazu ein eigener Szenenübergang, verwaltet über VOID Studio. Vorschau in `preview/`.

## Installation

1. Einmalig VOID Studio einrichten: Python 3.11 oder 3.12 (64 Bit) installieren und in OBS unter Werkzeuge → Skripte → Python-Einstellungen eintragen. Dann `void-studio.py` aus dem neuesten Release unter Werkzeuge → Skripte → `+` hinzufügen.
2. Im VOID-Studio-Fenster „IRL“ auswählen und „Installieren / aktualisieren“ klicken. VOID Studio richtet die Szenensammlung dabei gleich in OBS ein.
3. In OBS Szenensammlung → „VOID IRL“ wählen. Steht sie noch nicht im Menü, OBS einmal neu starten. (Alternativ: Szenensammlung → Importieren → `import.json` aus dem Pack-Ordner.)
4. Kameras einrichten (siehe unten).
5. „Mit Twitch verbinden“ – nur einmal für alle Packs.

## Kameras

Die Sammlung bringt vier Medienquellen mit, **Kamera 1** bis **Kamera 4**. Sie warten als SRT-Empfänger auf den Ports 9000 bis 9003 (`srt://0.0.0.0:9000?mode=listener` usw.). Vom Handy (z. B. Larix Broadcaster, IRL Pro) oder einem Encoder (z. B. BELABOX) auf `srt://<IP des Rechners>:9000` senden; Port im Router freigeben oder über ein VPN wie Tailscale gehen.

Lieber über einen Relay-Server, RTMP oder eine Kamera am Rechner? In OBS die Quelle doppelklicken und die Eingabe ändern bzw. die Quelle durch ein Videoaufnahmegerät ersetzen – der Name muss bleiben, die Szenen benutzen ihn.

| Szene | Kameras |
| --- | --- |
| Unterwegs | Kamera 1 formatfüllend |
| Zwei Kameras | Kamera 1 und 2 nebeneinander |
| Bild im Bild | Kamera 1 formatfüllend, Kamera 2 oben rechts |
| Vier Kameras | Kamera 1 bis 4 im Raster |
| Just Chatting | Kamera 1 mit Chat daneben |

## Verbindung weg – automatisch

VOID Studio überwacht **Kamera 1**. Bricht das Signal in einer Kamera-Szene ab, schaltet es nach 3 Sekunden auf „Verbindung weg“; ist es wieder 5 Sekunden stabil da, geht es zurück in die Szene von vorher. Die Szene zeigt, seit wann das Signal weg ist, und meldet die Rückkehr. Einstellbar in VOID Studio unter „IRL“ (an/aus, überwachte Quelle, Sekunden). Mit dieser Sammlung ist es bereits an.

## Ort, Wetter und Kameranamen

In der Szene **„VOID · Infos“** stehen die Textquellen „Info · Ort“, „Info · Wetter-Ort“, „Info · Kamera 1“ bis „Info · Kamera 4“ sowie „Info · Titel“ und „Info · Statuszeilen“. Doppelklick, Text eintragen – das HUD übernimmt ihn sofort, auch unterwegs per Fernsteuerung von OBS. Das Wetter (Open-Meteo) sucht den Ort bis zum „·“, also reicht z. B. „Hamburg · Speicherstadt“; „Info · Wetter-Ort“ nimmt einen anderen Ort fürs Wetter.

## HUD und feste Parameter

Die Kamera-Szenen haben ein schlankes HUD: LIVE, Uhrzeit, Ort, Wetter, Chat als Blasen unten links (verschwinden nach 25 Sekunden), Ziele unten rechts, Alerts als Pille oben. Feste Einstellungen in den Dateien in `obs/` anhängen, z. B. `obs/solo.html#chatlife=40`:

| Parameter | Wirkung |
| --- | --- |
| `place=Hamburg` | Ort im HUD |
| `lat=53.54&lon=9.99` | Wetter genau für diese Koordinaten statt nach Ortsnamen |
| `cam1=Hauptkamera&cam2=Helm` | Namen an den Kameras in den Mehrkamera-Szenen |
| `chatlife=40` | Sekunden, bis eine Chatnachricht verschwindet; `0` = bleibt |
| `clock=0` / `hud=0` / `goals=0` | Uhr / ganzes HUD / Ziele ausblenden |

## Inhalt

| Pfad | Zweck |
| --- | --- |
| `import.json` | Die Datei für OBS (Szenensammlung → Importieren). Erzeugt VOID Studio beim Installieren mit den Pfaden deines Rechners |
| `_vorlage/import.template.json` | Vorlage dafür; nicht in OBS importieren. VOID Studio braucht sie, um `import.json` neu zu erzeugen |
| `pack.json` | Name, Version und Szenen-Fingerabdruck für Updates |
| `obs/` | Einstiegsdateien der Browserquellen |
| `scenes.html` | Alle Szenen. Im Browser testen: `scenes.html?scene=solo&test=1&demo=1` |
| `assets/transition.webm` | Szenenübergang: 1,95 s, transparent, Umschaltpunkt 600 ms |
| `assets/` | Schriften mit Lizenzen, VOID-Bildmarke, Lockup |
| `preview/` | Vorschaubilder |

**Übergang:** Eine Stecknadel fällt, aus ihr öffnet sich kreisförmig eine Höhenlinien-Karte mit der Bildmarke, dann zieht sich alles in die Nadel zurück.

**Bridge-Daten:** Login, Sounds und Session liegen zentral in `%APPDATA%\VOID-Bridge\`, gemeinsam für alle Packs. Eigene Sounds kommen nach `%APPDATA%\VOID-Bridge\sounds\`. Die Token-Datei dort wie ein Passwort behandeln.
