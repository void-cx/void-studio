
## Telemetrie einrichten (Szene „ETS2 Telemetrie“)

Die Szene zeigt Start, Ziel, Firma, Ladung, Gewicht, Lohn, Restdistanz, Ankunftszeit, Tempo mit Tempolimit-Schild, Gang, Tank, Spielzeit, nächste Ruhepause und die heute gefahrenen Kilometer.

1. Einen Telemetrie-Server installieren, der das Funbit-Format auf `http://127.0.0.1:25555/api/ets2/telemetry` liefert (aktuelle Forks des Funbit ETS2 Telemetry Servers, z. B. die Version für SDK 1.10). Alternativ den scs-telemetry-json-service und in der Bridge die Telemetrie-URL auf `http://127.0.0.1:6969/` stellen.
2. In der Bridge ist „Spiel-Telemetrie weiterreichen“ nach dem Import bereits an.
3. Ohne laufende Telemetrie zeigt die Szene einen Hinweis statt leerer Werte.

**Dynamischer Himmel:** Alle Szenen folgen der Spieluhr – Nacht, Morgendämmerung, Tag, Abendrot. Ohne Telemetrie richten sie sich nach der echten Uhrzeit.

**Text-Animation:** Titel, Statuszeilen und Städtenamen gleiten weich ein, wie eine Wechselverkehrszeichen-Tafel, die umschaltet – auch wenn sich das Ziel ändert.

Getestet mit simulierten Daten im Funbit-Format über die Bridge. Mit einem laufenden Spiel bisher ungetestet; falls ein Wert fehlt, kurz melden, welcher Server läuft.
