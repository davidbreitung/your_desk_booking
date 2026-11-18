> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking 0.8.0

Mitarbeiter und Schreibtische entstehen ausschließlich durch M365/Places-Sync.
Lokale Einstellungen bleiben unter **Konfigurieren → Schreibtisch bearbeiten / Mitarbeiter bearbeiten** zugänglich.
NFC-Zuordnung, Höhen, Display und Zubehör werden erhalten.

## Buchungen

- Zusätzliche Graph-Anwendungsberechtigung: `Calendars.ReadBasic.All`, mit Administratorzustimmung.
- Eigener zentraler Abrufintervall, standardmäßig 5 Minuten, einstellbar zwischen 1 und 1440 Minuten.
- Manueller Abruf über „Buchungen aktualisieren“ oder `desk_booking.sync_bookings`.
- `calendarView` liest pro Ressourcenkalender die nächsten 365 Tage einschließlich Serieninstanzen und Ausnahmen; alle Ergebnisseiten werden gelesen. Bereits laufende, abgesagte, freie und abgelehnte Termine gelten nicht als nächste Buchung.
- Organisatoradresse wird zunächst gegen den eindeutigen Entra-Anmeldenamen (UPN), anschließend gegen Mail/SMTP-Aliasse aufgelöst. Die Mitarbeiter-Verknüpfung erfolgt über Mandant + Objekt-ID; unbekannte/mehrdeutige Alias-Zuordnungen bleiben unverknüpft. Dies berücksichtigt Konten mit derselben Kontaktadresse, aber verschiedenen UPNs.
- Tischentitäten „Nächste Buchung“ und „Gebucht durch“, mit Mitarbeiter-Geräte-/Entitäts-ID, Geräte-Link, Aktualität, Fehler, letzter erfolgreicher Abfrage und Suchhorizont.
- Lokaler Cache bleibt bei Fehlern erhalten, wird jedoch als nicht aktuell markiert. Graph-Retry-After und Authentifizierung werden mit dem Verzeichnissync geteilt.
- Kein Kalenderinhalt wird verändert; Betreff, Text und Anhänge werden nicht angefordert.

## Display

Zusätzliche ESPHome-Textentität „Naechste Buchung“ empfängt ein kleines JSON mit Zeit, Name und Warnung. Die Zuordnung folgt dem konfigurierten Display-Gerät. Übertragung alle 30 Sekunden; nach 90 Sekunden ohne Empfang wird der Hinweis als veraltet gekennzeichnet und der gelbe Ring entfernt.

Unter 120 Minuten: aufgerundete Restminuten; ansonsten lokales Datum/Uhrzeit. Unter 60 Minuten: statischer gelber Ring. Benachrichtigungs-Overlays behalten Vorrang. Lange Namen werden begrenzt, ohne UTF-8-Zeichen zu zerschneiden. Bestehende Firmware-Entitätsverweise müssen zum zugeordneten Tisch passen.

## Sicherheitsgruppen

Jede `securityEnabled=true`-Gruppe erhält ein virtuelles Gerät mit Modell **Group** und Text-, Prioritäts-, Dauer- und Senden-Entität. Verteilungsgruppen erzeugen kein Gerät. Direkte und verschachtelte Mitgliedschaften werden anhand der Graph-IDs ausgewertet; Zyklen sind abgesichert. Versand geht nur an aktive, eingecheckte Mitglieder mit zugeordnetem Display. Displays werden dedupliziert; Ausfälle einzelner Displays werden als Teilfehler gemeldet. Synchronisierung versendet selbst keine Nachrichten.

## Sicherungen und Prüfung

- HA-Sicherung vor Änderungen: `e47516d6`, 15.11.2026 21:26:22, NASHome, Konfiguration und Datenbank.
- Lokale Sicherung: `backups/pre-bookings-groups-20261115-212555/`.
- Veröffentlichungspaket wird aus vorhandenen Quellen erstellt (`package_m365.py`); alte Generatoren nicht ausführen.
- Tests verwenden synthetische Microsoft-Daten und explizite HA-Grenzstellen-Fakes; keine produktiven Buchungen oder Gruppen-Nachrichten werden erzeugt.
- Integration 0.8.0 installiert; 29 Quelldateien per SHA256 geprüft. Zusätzliche Serversicherung: `/config/desk_booking_backup_080_20261115_214534`.
- HA-Konfigurationsprüfung erfolgreich; Verzeichnis- und Kalender-Sync nach Neustart erfolgreich (10 aktive interne Benutzer, 1 Places-Schreibtisch, 8 Gruppen). Alle 8 vorhandenen Gruppen haben `securityEnabled=false`; daher erwartungsgemäß keine Group-Geräte im Live-System.
- Display-Original gesichert unter `/config/desk_display_backups/before-bookings-20261115-2149/`. ESPHome 2026.10.2: Build erfolgreich, Flash 50,8 %, RAM 38,6 %, OTA-Upload erfolgreich (Exit 0). Konfigurationshash des Builds: `0xe1c92490`.
- Display-Textentität empfängt die echte Buchung am 16.11.2026 um 08:00 mit Alex Beispiel. Physische Darstellung am Bildschirm kann ohne Kamera nicht visuell bestätigt werden.
- Paket-SHA256: `979d15fa03ff4affd14ff1eab24582430dd7de061c3a51c8cacff24c7f4c26a1`.
- Abschließende Prüfung: 100 Tests erfolgreich. Live-Buchung: 16.11.2026 08:00–17:00 Europe/Berlin, Alex Beispiel; `identity_status=resolved`, Mitarbeiter-Geräte- und Entitätsverknüpfung vorhanden. Nach letztem Neustart keine `desk_booking`-Einträge im Systemfehlerprotokoll, Kalenderstatus `ok`, null fehlgeschlagene Schreibtische.
