# VOID Studio

OBS-Szenen-Packs für Enter The Void plus **VOID Studio** – ein OBS-Skript, das die Packs installiert, aktuell hält und die Twitch-Bridge (Alerts, Sounds, Chat, Ziele, Rückblick, Spiel-Telemetrie) mitbringt.

## Für Streamer

1. Python 3.11/3.12 (64 Bit) installieren, in OBS unter Werkzeuge → Skripte → Python-Einstellungen eintragen.
2. `void-studio.py` aus dem [neuesten Release](../../releases/latest) laden und unter Werkzeuge → Skripte → `+` hinzufügen.
3. Im Skript-Fenster Pack wählen → „Pack installieren“ → „Pack-Ordner öffnen“ → OBS: Szenensammlung → Importieren → `import.json`.
4. „Mit Twitch verbinden“ – einmal für alle Packs.
5. Optional: im Portal unter Konto → Login Twitch verknüpfen. Dann zeigt [my.void.cx/studio](https://my.void.cx/studio) deine Stream-Statistiken, und der Discord kann deinen Go-Live ankündigen.

## Für Entwickler

| Pfad | Inhalt |
| --- | --- |
| `studio/void-studio.py` | VOID Studio (Pack-Manager + Bridge) |
| `build/tpl.html` | Kern aller Szenen; die Themes entstehen über `make_*.py` daraus |
| `build/make_*.py` | ein Generator pro Theme (Wardogs, Minecraft, ETS2, GTA, VOID); AION 2 nutzt `tpl.html` direkt |
| `build/packs.py` | baut die Pack-Ordner inklusive OBS-Vorlage und `pack.json` |
| `build/stg.py` / `prev_packs.py` | rendert Übergänge (WebM mit Alpha) und Vorschaubilder |
| `build/versions.json` | Versionen pro Pack und Studio; Packs unter `hold` landen nicht im Release |
| `build/font/` | eigene VOID-Schriften: VOID Runes (nur AION 2) und VOID Latin |
| `build/changelog.json` | Änderungen pro Studio-Version |
| `build/smoke.py` / `ci_release_check.py` | Schnellprüfung und Release-Entscheidung für die CI |
| `build/requirements.txt` | Python-Abhängigkeiten für Build und CI |
| `.github/workflows/build.yml` | GitHub Actions: Prüfung bei PRs, Build und Release auf `main` |

Ablauf für ein Update: Änderung machen, Version des Packs (und bei Studio-Änderungen `studio`) in `versions.json` hochzählen, Eintrag in `changelog.json`, pushen. Den Rest erledigt GitHub Actions:

| Auslöser | Was passiert |
| --- | --- |
| Pull Request | Schnellprüfung: Generatoren, Packs bauen, jede Szene im Browser auf JS-Fehler prüfen, Studio kompilieren (~3 min) |
| Push auf `main` | Schnellprüfung, dann voller Build mit Übergängen und Vorschauen und ein neues Release – **nur wenn sich eine Version geändert hat** (~15 min) |
| Actions → „Build & Release“ → Run workflow | wie Push, optional mit erzwungenem Release |

Ohne Versionssprung gibt es kein Release, damit VOID Studio keine Schein-Updates meldet. Lokal geht es weiterhin mit `pip install -r build/requirements.txt`, `build/build.sh` und `build/publish.sh`.
Einzelnes Pack bauen: `build/build.sh wardogs`.

Die Theme-Anleitung (Regeln, Aufbau, Beispiel) liegt als Claude-Doc vor und sollte als `docs/THEMES.md` ins Repo exportiert werden.

**Runen-Schrift:** `build/font/VOIDRunes-Regular.woff2` ist öffentlich im Repo und im AION-2-Pack enthalten – die Runen-Zuordnung lässt sich daraus auslesen.
