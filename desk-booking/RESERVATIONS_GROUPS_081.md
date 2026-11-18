> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking 0.8.1

Ersetzt die Beschränkung auf Sicherheitsgruppen aus 0.8.0: Alle von Graph synchronisierten Gruppen werden jetzt als virtuelle Geräte vom Modell `Group` angelegt. Bestehende Mitgliedschaftsprüfung, verschachtelte Gruppen, lokale Nachrichtenfelder und ausschließliche Zustellung an eingecheckte Mitglieder bleiben erhalten. Gelöschte Gruppen werden deaktiviert.

## Reservierungsanzeige

- Freier Tisch ohne Buchung innerhalb der nächsten 60 Minuten: `FREI`, grün.
- Freier Tisch mit Buchung in weniger als 60 Minuten: `RESERVIERT`, gelb; statischer gelber Ring.
- Laufende Buchung (`Start <= jetzt < Ende`): `RESERVIERT`, rot; statischer roter Ring. Dieser Reservierungsstatus hat Vorrang vor dem Check-in-Text; eine bestehende Anmeldung wird nicht verändert.
- Während einer laufenden Buchung zeigt die Buchungszeile deren Ende und den zugehörigen Organisator. Die Entität „Nächste Buchung“ bleibt auf die nächste zukünftige Buchung gerichtet und erhält zusätzlich Attribute zur laufenden Reservierung.
- Nach Buchungsende gilt wieder die nächste Reservierung bzw. der lokale Check-in-Status.
- Aktualisierung der Anzeige weiterhin alle 30 Sekunden aus dem lokalen Kalendercache, Graph-Abfrage standardmäßig alle 5 Minuten. Bei ausgebliebener Aktualisierung greift weiterhin die 90-Sekunden-Ausfallbehandlung auf dem Display. Nachrichten-Overlays behalten ihren bestehenden Vorrang.

## Prüfung

101 lokale Tests erfolgreich, einschließlich exaktem Buchungsbeginn, Buchungsende und nachfolgender Reservierung. Keine produktiven Kalenderbuchungen oder Gruppen-Pushnachrichten zum Testen erzeugt.

Paket-SHA256: `6cf02f9812cabf7821d48700690ddd2bc016007e3743fdea436e2014f271870d`.

Live-Installation abgeschlossen am 15.11.2026: 0.8.1 geladen, acht Group-Geräte mit je fünf Entitäten sichtbar (vier Nachrichten-Steuerungen plus Gruppenstatus). M365- und Kalender-Sync `ok`, keine `desk_booking`-Fehler im Systemprotokoll. Integration vorher gesichert unter `/config/desk_booking_backup_081_20261115_220618`.

Display-Firmware mit ESPHome 2026.10.2 erfolgreich gebaut und per OTA installiert, Exit 0. Build-Konfigurationshash `0xced22d06`, Flash 50,8 %, RAM 38,6 %. Original-Firmwarekonfiguration unter `/config/desk_display_backups/before-reserved-20261115-2209/` gesichert. Physische Rot-/Gelbdarstellung ohne Kamera nicht visuell bestätigt; keine echten Kalendertermine zum Testen verändert.
