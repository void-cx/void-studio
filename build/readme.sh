cd dist/packs
for k in aion2 wardogs minecraft ets2 gta void; do
 case $k in aion2) G="AION 2";; wardogs) G="Wardogs";; minecraft) G="Minecraft";; ets2) G="Euro Truck Simulator 2";; gta) G="GTA V / Roleplay";; void) G="VOID (ohne Spielbezug)";; esac
 N=$([ $k = ets2 ] && echo "Sechs" || echo "Fünf")
 GS=$(case $k in ets2) echo "ETS2-Fahrt und ETS2-Telemetrie";; void) echo "Spiel-Overlay";; *) echo "$G-Overlay";; esac)
 GN=$(case $k in ets2) echo "ETS2";; gta) echo "GTA";; void) echo "VOID";; *) echo "$G";; esac)
 GSP=$([ $k = void ] && echo "Spielaufnahme" || echo "$GN Spielaufnahme")
 case $k in wardogs) CAM="rechts mittig (unten rechts liegt das Waffen-HUD)";; gta) CAM="rechts mittig (oben rechts liegen Geld und Fahndungslevel)";; *) CAM="unten rechts";; esac
 case $k in
  aion2) STG="Ein Aether-Portal öffnet sich, Federn brechen aus, Runenkranz und Lichtschwingen entfalten sich um die Bildmarke, raus geht es mit einem Teleport-Blitz";;
  wardogs) STG="Eine schräge Lagekarte wischt durchs Bild, die Bildmarke baut sich auf und stört kurz wie ein Funksignal";;
  minecraft) STG="Blöcke laden diagonal ein wie Chunks, die Bildmarke baut sich auf, dann brechen die Blöcke weg und fallen";;
  ets2) STG="Ein VOID-Sattelzug fährt formatfüllend durchs Bild, die Bildmarke baut sich auf der Plane auf";;
  void) STG="Ein schwarzes Loch reißt aus der Mitte auf, ein Ring im Markenverlauf rotiert am Rand, die Bildmarke baut sich auf, dann kollabiert alles in einen Punkt";;
  gta) STG="Vier Sonnenuntergangs-Bänder fegen schräg durchs Bild wie beim Charakterwechsel, die Bildmarke baut sich auf, dann kaskadieren die Farben wieder raus";;
 esac
 cat > void-theme-$k/LIESMICH.md <<EOF
# VOID Szenen-Pack: $G

$N OBS-Szenen im VOID-Design für $G (Stream startet, Kurze Pause, Stream endet, Just Chatting, $GS), ein eigener Szenenübergang, verwaltet über VOID Studio. Vorschau in \`preview/\`.

## Installation

1. Einmalig VOID Studio einrichten: Python 3.11 oder 3.12 (64 Bit) installieren und in OBS unter Werkzeuge → Skripte → Python-Einstellungen eintragen. Dann \`void-studio.py\` aus dem neuesten Release unter Werkzeuge → Skripte → \`+\` hinzufügen.
2. Im VOID-Studio-Fenster „$G“ auswählen und „Pack installieren / aktualisieren“ klicken.
3. „Pack-Ordner öffnen“, dann OBS → Szenensammlung → Importieren → \`import.json\` → Sammlung „$([ $k = void ] && echo VOID || echo "VOID × $GN")“ aktivieren.
4. Kamera-Gerät und bei „$GSP“ das Spielfenster wählen.
5. „Mit Twitch verbinden“ – nur einmal für alle Packs.

Updates: „Nach Updates suchen“ und „Alle Pack-Updates installieren“. Die Szenen übernehmen neue Versionen sofort; nur wenn sich die Szenen selbst ändern, meldet VOID Studio, dass \`import.json\` neu importiert werden muss.

## Inhalt

| Pfad | Zweck |
| --- | --- |
| \`import.template.json\` | Vorlage der Szenensammlung; VOID Studio erzeugt daraus \`import.json\` mit den Pfaden deines Rechners |
| \`pack.json\` | Name, Version und Szenen-Fingerabdruck für Updates |
| \`obs/\` | Einstiegsdateien der Browserquellen. Parameter hier anhängen, z. B. \`#scene=game&cam=bl\` |
| \`scenes.html\` | Alle Szenen. Im Browser testen: \`scenes.html?scene=start&test=1&demo=1\` |
| \`assets/transition.webm\` | Szenenübergang: 1,95 s, transparent, Umschaltpunkt 600 ms |
| \`assets/\` | Schriften mit Lizenzen, VOID-Bildmarke, Lockup |
| \`preview/\` | Vorschaubilder |

**Übergang:** $STG.

**Logo-Animation:** Start, Pause und Ende bauen die Bildmarke beim Szenenwechsel auf. Bei Raids, ab 5 Geschenk-Abos und ab 1.000 Bits auch im Alert.

**Game-Kamera:** sitzt $CAM, verschiebbar über \`obs/game.html\`.

**Letzte Unterstützer in Spielszenen:** In den Skript-Einstellungen der Bridge an- und ausschaltbar, dazu Häkchen für Follow, Abo, Geschenk, Bits und Raid. Erscheint an der Game-Kamera über den Zielen.

**Bridge-Daten:** Login, Sounds und Session liegen zentral in \`%APPDATA%\\VOID-Bridge\\\`, gemeinsam für alle Packs. Eigene Sounds kommen nach \`%APPDATA%\\VOID-Bridge\\sounds\\\` (\`follow.mp3\`, \`sub.mp3\`, \`resub.mp3\`, \`gift.mp3\`, \`cheer.mp3\`, \`raid.mp3\`, \`redeem.mp3\` oder \`default.mp3\`). Die Token-Datei dort wie ein Passwort behandeln.
EOF
done
cat >> void-theme-ets2/LIESMICH.md <<'EOF'

## Telemetrie einrichten (Szene „ETS2 Telemetrie“)

Die Szene zeigt Start, Ziel, Firma, Ladung, Gewicht, Lohn, Restdistanz, Ankunftszeit, Tempo mit Tempolimit-Schild, Gang, Tank, Spielzeit, nächste Ruhepause und die heute gefahrenen Kilometer.

1. Einen Telemetrie-Server installieren, der das Funbit-Format auf `http://127.0.0.1:25555/api/ets2/telemetry` liefert (aktuelle Forks des Funbit ETS2 Telemetry Servers, z. B. die Version für SDK 1.10). Alternativ den scs-telemetry-json-service und in der Bridge die Telemetrie-URL auf `http://127.0.0.1:6969/` stellen.
2. In der Bridge ist „Spiel-Telemetrie weiterreichen“ nach dem Import bereits an.
3. Ohne laufende Telemetrie zeigt die Szene einen Hinweis statt leerer Werte.

**Dynamischer Himmel:** Alle Szenen folgen der Spieluhr – Nacht, Morgendämmerung, Tag, Abendrot. Ohne Telemetrie richten sie sich nach der echten Uhrzeit.

**Text-Animation:** Titel, Statuszeilen und Städtenamen gleiten weich ein, wie eine Wechselverkehrszeichen-Tafel, die umschaltet – auch wenn sich das Ziel ändert.

Getestet mit simulierten Daten im Funbit-Format über die Bridge. Mit einem laufenden Spiel bisher ungetestet; falls ein Wert fehlt, kurz melden, welcher Server läuft.
EOF
cat >> void-theme-void/LIESMICH.md <<'EOF'

## Besonderheiten

- **Ereignishorizont:** Hinter der Bildmarke kreist eine Akkretionsscheibe aus Lichtteilchen im Markenverlauf. Jeder Alert schickt eine Schockwelle durch, jede Chatnachricht schießt neue Teilchen hinein.
- **Echte Live-Zahlen:** Unten links Follower, Abos und neue Follows heute, direkt aus der Bridge. Ohne Bridge bleiben die Chips leer statt Fantasiezahlen zu zeigen.
- **Terminal-Ton:** `// enter the void` als Eyebrow, Titel und Statuszeilen werden getippt, mit blinkendem Cursor.
- **Ohne Spielbezug:** Passt zu jedem Spiel, Just Chatting oder Community-Streams. Den Titel im Game-Overlay setzt du mit `#title=…` in `obs/game.html`.
EOF
cat >> void-theme-gta/LIESMICH.md <<'EOF'

## Besonderheiten

- **Ladebildschirm-Look:** Los Santos bei Sonnenuntergang mit Palmen und Skyline, großer Titel unten links, Statuszeile mit Lade-Kringel unten rechts.
- **Alerts als Missions-Banner:** breites dunkles Band mit großer goldener Schrift („Mission erfüllt!“, „Respekt +“, „Raid!“).
- **Chat als Smartphone:** Nachrichtenblasen im Handy statt Kasten.
- **Charaktername fürs Rollenspiel:** in `obs/game.html` z. B. `#char=Vinnie%20Kowalski` anhängen, die Namensplatte an der Kamera zeigt ihn im Wechsel.
- **Schrift:** Anton als freie Alternative zur GTA-Schrift Pricedown (die ist nur privat frei).
EOF
cat >> void-theme-minecraft/LIESMICH.md <<'EOF'

## Besonderheiten

- **Blocky-Logo:** Die VOID-Bildmarke als Pixel-Blöcke, wird Block für Block von unten nach oben gebaut (Intro, Übergang, Alert-Icon).
- **Splash-Text:** Gelber, pulsierender Spruch am Titel wie im Hauptmenü, zufällig pro Szenenstart. Eigener Spruch: in `obs/start.html` z. B. `&splash=GG!` anhängen.
- **Alerts als Fortschritts-Toast:** gleiten oben rechts herein, mit Logo-Slot links.
EOF
sed -i "s/im VOID-Design für VOID (ohne Spielbezug) (/im VOID-Design ohne Spielbezug (/" void-theme-void/LIESMICH.md
