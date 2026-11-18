> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Räume – Desk Booking 0.11.0

## Umfang

Microsoft-Places-Räume werden als eigenständige virtuelle Geräte (Modell Room) unter der Kategorie Raum importiert. Später angelegte Räume werden bei der regulären M365-Synchronisierung übernommen. Identität: Tenant + Places-ID, nicht Anzeigename. Umbenennungen aktualisieren den Namen; entfernte Räume werden lokal inaktiv, nicht gelöscht.

Je Raum fünf Sensoren: Raumstatus, Nächste Buchung, Gebucht durch, Aktuelle Buchung, Aktuell gebucht durch. Buchungssensoren enthalten Beginn, Ende, Datenaktualität, letzten erfolgreichen Abruf, Fehler sowie die Verknüpfung zum Mitarbeitergerät. Die vorhandene eindeutige Entra-Auflösung anhand des Organisators wird wiederverwendet; mehrdeutige/externe Organisatoren werden nicht einem Mitarbeiter geraten zugeordnet.

Kalenderabfrage im gemeinsamen zentralen Buchungsintervall (Standard 5 Minuten), manuell über Buchungen aktualisieren. Verzeichnisintervall standardmäßig 15 Minuten. Bestehender lokaler Kalendercache wird kompatibel erweitert; sein interner Schlüssel `desks` enthält nun auch Räume. Veraltete Daten bleiben bei Fehlern erhalten und werden als nicht aktuell markiert.

Räume bekommen keine Check-in/out-, Display-, Licht-, Rollo-, Push- oder Auswahlentitäten. Raumkalender werden ausschließlich gelesen. Die No-show-Automatik hat zusätzlich eine explizite Typprüfung, die Räume ausschließt. Schreibtischwarnungen und täglicher Check-out bleiben auf Schreibtische beschränkt.

## Prüfung und Sicherung

- 134 lokale Tests erfolgreich (explizite HA-Testdoubles, keine vollständige HA-Testinstallation).
- Neue Prüfungen: Raumprojektion mit E-Mail und Entra-ID; Umbenennung/Deaktivierung/Reaktivierung; idempotenter Import; Ausschluss alter Ressourcen aus Mitarbeiterimport; Kalendercache und Fehlererhalt; laufende/nächste Reservierung mit Mitarbeiterlink; kein Aufruf der Schreibtisch-Automatik und keine Raumkalenderlöschung.
- Lesender Live-Graph-Test: ein Raum Besprechungsraum gefunden, Kalenderzugriff erfolgreich, aktuell 0 Termine im 365-Tage-Fenster. Keine Testreservierung angelegt oder geändert.
- HA-Backup d3aef195, 15.11.2026 23:01:17 Europe/Berlin, Konfiguration einschließlich Datenbank und ssl, auf NASHome. Keine Apps enthalten.
- Lokale Quellkopie: backups/pre-rooms-0110.
- Paket: dist/desk-booking-0.11.0.zip, 32 Dateien.
- SHA256: fcfdea335e48bd8cc003b912e32af37f899fb2ae2db3323cb7d54f1d2edd9882.
- Installer prüft sämtliche Live-Quelldateien gegen die gesicherte 0.10.0-Basis und alle neuen Dateihashes vor Änderungen. Zusätzliche Quellkopie auf HA vor Installation, keine direkten Änderungen an HA-Konfigurationsspeicherdateien.

## Deployment

Paket installiert; alle 32 Dateihashes und die unveränderte 0.10.0-Basis erfolgreich geprüft. Remote-Quellbackup: /config/desk_booking_backup_0110_20261115_230516. `ha core check` und Neustart erfolgreich.

Live verifiziert am 15.11.2026 gegen 23:07 Europe/Berlin:

- Integrationsseite Version 0.11.0, 22 Geräte/Dienste, 119 Entitäten, neue Kategorie Raum.
- Besprechungsraum als Room-Gerät cd4f5168ab9b4f7285caf8ece4f16667 mit genau fünf Sensoren; keine Bedienelemente.
- M365-Sync ok: 10 Mitarbeiter, 8 Gruppen, 2 Schreibtische, 1 Raum.
- Buchungs-Sync ok: Intervall 5 Minuten, failed_desks=0, failed_rooms=0, errors=[].
- Raumstatus active, data_current=true, error=null. Kalender ist leer, deshalb Zeitpunkt-Sensoren unknown und Buchende „—“; kein erfolgreicher Buchungsabruf mit einem echten Raumtermin behauptet. Zuordnung und aktuelle/nächste Buchung sind mit synthetischen Ereignissen getestet.
- Live-Registry-Vergleich: alle bisherigen 114 Entitäten behalten entity_id, unique_id, device_id, config_subentry_id und disabled_by unverändert. Genau fünf neue Raumsensoren.
- Keine Desk-Booking-Einträge im Systemfehlerprotokoll nach Neustart.
- UI-Beleg: rooms-installation-0110.png.
