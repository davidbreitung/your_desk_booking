> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Nachrichtenanimation und Raffstore-Schrift

## Final installiert am 15. November 2026

Ursache: Der grüne Frei-Ring mit seinem weichen Schatten liegt auf der oberen
LVGL-Ebene hinter der Nachricht. Obwohl er verdeckt ist, verursachte sein
Neuzeichnen während der Nachrichtenanimation erhebliche Zeichenarbeit.

Die finale Firmware blendet diesen Ring während einer Nachricht aus. Beim
Bestätigen und beim automatischen Ablauf wird der aktuelle Belegungsstatus neu
gerendert. Auch Statusänderungen während einer Nachricht berücksichtigen diese
Sperre. Der ursprüngliche Spinner und alle Prioritätsfarben bleiben erhalten.

„Höhe“ verwendet an Positionsanzeige und Auswahltaste explizit die bereits
vorhandene Roboto-Schrift mit GF_Latin_Core. Die Seite erbt dieselbe Schrift.
Der Nutzer hat flüssigere Animation und korrektes „ö“ am Display bestätigt.

## Messung am Gerät

Rote Nachricht, 40 Sekunden; Schleifenzeitmaximum in 30-Sekunden-Fenstern.
Boot sowie Öffnen/Schließen getrennt von der laufenden Animation bewertet.

| Variante | Schleifenzeitspitzen |
|---|---:|
| Ursprünglicher Spinner, 50 % Puffer | 551–562 ms |
| Spinner, 12 % Puffer | 1.022–1.065 ms |
| Vier bewegte Punkte, statischer Ring | 751–753 ms |
| Vier bewegte Punkte, ohne statischen Ring | 733–740 ms |
| 60 feste Segmente mit Farbwechsel | 650 ms |
| **Originalspinner, verdeckter Frei-Ring ausgeblendet** | **80 ms** |

Die finale volle Animationsmessung lief von 18:45:13 bis 18:45:53 CET.
Der Messwert um 18:45:46 betrug 80 ms. Die CPU-Auslastung lag im entsprechenden
30-Sekunden-Fenster bei 23,1 % statt zuvor 48,4 % (Mittel über beide Kerne).
Beim Öffnen/Schließen lagen einzelne Spitzen noch bei 443–447 ms. Diese sind
kein dauerhaftes Ruckeln während der Animation. Im Leerlauf zuvor etwa 22 ms.

Das zusätzliche VERBOSE-Profil maß 17–19 ms Übertragung pro halbem Bild
(472 × 230/244 Pixel). Die Hauptverzögerung lag davor beim Zeichnen.
Der kleinere Grafikpuffer und alle experimentellen Ringvarianten wurden verworfen;
50 % Puffer und normaler Logger sind wieder aktiv.

## Validierung und Sicherung

ESPHome 2026.10.2: Build und OTA erfolgreich, Gerät wieder online. Rote,
gelbe und ringlose Nachrichten über die Integration übertragen. Physische
Leuchten, Rollo und Tischhöhe wurden nicht über Testbefehle bewegt.

Firmware: 1.855.427 Bytes, 50,6 % des Slots; statischer RAM 38,5 %.
Build-Konfigurationshash: 0x7b191fa1.
OTA SHA256: d45b06a9eab76c5ebfb5b10129fb4b781072c3e17331c89f48ad1dd5da660073.

Sicherung vorher und Vergleichskonfigurationen:
`/config/desk_display_backups/before-performance-20261115_181833`.
Dort liegen auch `final-overlay-config.yaml` und `final-overlay-firmware.ota.bin`.
Die Testkonfigurationen wurden aus dem ESPHome-Dashboard archiviert.

Lokale aktive redigierte Konfiguration: `../schreibtisch-display-01.redacted.yaml`.
Reproduzierbare Änderung ab Ausgangsstand: `update_display_overlay.py`.
Die anderen Performance-Skripte dokumentieren verworfene Versuche und sind
nicht Teil der aktiven Firmware. Keine Änderung an der HA-Integration nötig.

## Nachkorrektur: Lamellen nach Display-Neustart

Die Lamellenfähigkeit war in HA korrekt (`cover_tilt: true`), die drei
Bedienelemente blieben aber nach Neustart ausgeblendet. Der interne
Home-Assistant-Binärsensor aktualisierte ihre Sichtbarkeit nur in `on_state`.
Mit `trigger_on_initial_state: true` wird nun auch der erste empfangene Status
verarbeitet. Die spätere Umschaltung bei Änderung der Zuordnung bleibt erhalten.
Der Firmware-Generator wurde entsprechend angepasst. Es werden dabei keine
Positionsbefehle ausgelöst.
