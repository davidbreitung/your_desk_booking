> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Display: lokale Belegung

Die Firmware liest die Belegung und den angemeldeten Mitarbeiter direkt aus den beiden Sensoren von Schreibtisch 01 in Home Assistant.

- `free`: FREI und ein statischer grüner Ring mit Leuchteffekt, ohne Animation.
- `checked_in`: EINGECHECKT und Mitarbeitername; der grüne Ring verschwindet.
- Während einer Änderung, bei Fehlern oder fehlender Verbindung erscheint kein grüner Ring.
- Der Mitarbeitername erscheint groß auf der Arbeitsplatzseite und zusätzlich klein am oberen Rand der anderen normalen Seiten.
- Bestehende Höhenbedienung, Favoriten, Dimmer, Nachrichten und Standby-Helligkeit bleiben erhalten. Nachrichten können die Statusanzeige vorübergehend überdecken.
- Die Statusübernahme löst keine Höhenänderung aus.

Quelldateien im Projekt:

- `schreibtisch-display-01.vor-belegung.redacted.yaml`: vorherige Konfiguration ohne Zugangsdaten.
- `schreibtisch-display-01.belegung.redacted.yaml`: neue Konfiguration ohne Zugangsdaten.
- `desk-booking/update_display_firmware.py`: gezielte Umstellung mit Prüfung der Ausgangsstruktur und Sicherung vor dem Schreiben.

Die vollständige ursprüngliche Konfiguration einschließlich bestehender Zugangsdaten bleibt ausschließlich auf dem Home-Assistant-System gesichert unter `/config/desk_display_backups/schreibtisch-display-01-before-occupancy-20261115_160129.yaml`.

## Prüfung

Am 15.11.2026 mit ESPHome 2026.10.2 erfolgreich kompiliert und per verschlüsseltem OTA installiert. Das Gerät ist wieder verbunden und meldet einen erfolgreichen Start.

Im Live-Protokoll des Displays geprüft: `applying` → Mitarbeitername `[TEST] Demo Mitarbeiter` → `checked_in`, danach `applying` → `free` und leerer Mitarbeitername. Die Sitz-/Steh-Favoriten wurden nach dem Test wieder auf 74/110 cm zurückgesetzt; der Höhen-Sollwert blieb durchgehend bei 74 cm. Das zuvor ausgewählte Profil `[TEST] Alex Beispiel` wurde wieder ausgewählt, der Tisch bleibt frei.

Der Build belegt 97,6 % der App-Partition. Für spätere Erweiterungen ist deshalb wenig Flash-Spielraum vorhanden. Ein einzelner LVGL-Zeitschwellwert wurde beim Auschecken überschritten (526 ms); es trat kein Neustart oder Funktionsfehler auf. Eine optische Kontrolle am physischen Display ist aus der Ferne ohne Kamera nicht möglich.

Build-Ende, OTA-Ergebnis und relevante Empfangsmeldungen sind in `display-build.log`, `display-upload.log` und `display-runtime-verification.log` gespeichert.
