> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking 0.14.2

16.11.2026: zusätzlicher dauerhaft sichtbarer Reservieren-Link unten links im Grundriss. Verwendet dieselbe Darstellung und zentrale Reservierungs-URL wie die Symbol-Menüs, öffnet separat mit `_blank`/`noopener noreferrer`. Unabhängig von Auswahl, Datum, Belegung und Bearbeitungsmodus.

Lokales Backup `backups/pre-0142`, Live-Quellbackup `/config/desk_booking_backup_0142_20261116_150432`. Baseline-Prüfsummen vor Installation erfolgreich. Vier bestehende Kartenprüfungen und JavaScript-Syntaxprüfung erfolgreich. Backend unverändert; Frontend-Ressource auf `?v=0.14.2` aktualisiert, kein Core-Neustart erforderlich.

Live geprüft: ohne ausgewählte Symbole sichtbar, 12 px vom linken und 24 px vom unteren Bildrand; Ziel entspricht dem zentral konfigurierten Places-Gebäudelink, `_blank` bestätigt. Screenshot `floorplan-reserve-0142.jpg`. Keine Reservierung angelegt.

Paket SHA256: `a9a190e3ae0d8466651ad8959235f4c7819c003533013841271ccefb5ec97ae8`.
