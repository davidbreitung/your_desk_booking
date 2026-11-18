> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking Raumplan – 0.12.0

## Bedienung

Eigene Dashboard-Karte `custom:desk-booking-floorplan`, im Kartenpicker als „Desk Booking Raumplan“ registriert. Kartenoptionen: `title`, optional `plan_id`, `default_time` (Standard 09:00). Modulressource: `/desk_booking_static/desk-booking-floorplan.js?v=0.12.0`.

Administratoren legen über „＋ Plan“ einen zentralen Plan an, laden PNG/JPEG/WebP hoch, ziehen Ressourcen aus der Palette auf den Plan oder fügen sie per Klick hinzu. Bestehende Symbole per Maus/Touch verschieben oder mit Pfeiltasten feinjustieren. Optionales Raster, Größe 32–140 px, Drehung und Beschriftung. Speichern übernimmt den gesamten Entwurf, Abbrechen verwirft ihn. Parallele Änderungen werden über Revisionen erkannt. Bis zu 20 Pläne mit je 200 Objekten. Keine Möglichkeit zur manuellen Mitarbeiter-/Ressourcenanlage.

Beim Öffnen zeigt die Karte heute und die aktuelle Uhrzeit. Pfeile/Datumsauswahl navigieren bis 30 Tage voraus. Andere Tage starten standardmäßig um 09:00 Uhr. Zeitleiste erlaubt Planung zu einer Uhrzeit; „Jetzt“ kehrt zum Live-Zustand zurück. Datum und Uhrzeit richten sich nach der HA-Zeitzone, unabhängig von der Browserzeitzone. Planungsansicht zeigt Buchungen, keine historische Anwesenheit. Räume haben weiterhin keinen Check-in.

Status: grün frei, gelb Reservierung in weniger als 60 Minuten, rot laufende Reservierung, blau tatsächlich eingecheckt (nur Live-Schreibtische), grau veraltet/inaktiv. Überschneidungen werden in den Details als Konflikt bezeichnet. Eine nächste Reservierung jenseits Mitternacht wird berücksichtigt. Klick auf ein Symbol zeigt die Tagesbuchungen und Mitarbeiterlinks. Mitarbeitersuche, Filter „Nur frei“, Zoom und Übersichtszähler.

## Daten und Zugriff

- Bestehende Integration wird erweitert, keine separate Integration.
- WebSocket-Befehl `desk_booking/floorplan`, Aktionen snapshot/get/save/photo. Ausschließlich über authentifizierte HA-Verbindung. Save prüft Administratorrolle serverseitig. Ressourcen und Mitarbeiter werden anhand der Leseberechtigung ihrer Sensoren gefiltert.
- Öffentlicher statischer Pfad enthält nur JavaScript. Grundrisse und Mitarbeiterbilder liegen in privaten HA-Store-Dateien, nicht in `/local`. Microsoft-Token bleiben im Backend.
- Zentraler Plan-Store, atomare Speicherung vor Übernahme in den Arbeitsspeicher. Positionswerte relativ zum Bild (0–100 %).
- Bild-Upload wird browserseitig auf maximal 2400 px verkleinert; nur PNG/JPEG/WebP, serverseitige MIME-/Signaturprüfung und 4-MB-Limit. Keine beliebigen Bild-URLs oder SVG-Dateien.
- Fotos anhand Tenant + Entra-Objekt-ID; 96×96 über Graph, maximal 256 KiB, JPEG/PNG. Positiver Cache und fehlendes Foto 24 Stunden, temporäre Fehler/Berechtigungen mindestens 5 Minuten. Initialen als Ersatz. Graph-Retry-After und Token-Erneuerung gelten auch für Fotos.
- Die Karte lädt alle 30 Sekunden aus dem vorhandenen Buchungscache; kein zusätzlicher Kalenderpoll pro Browser. Kalender-Sync liest ab lokalem Tagesbeginn, damit frühere Termine des heutigen Tages sichtbar bleiben. Bestehendes konfigurierbares Buchungsintervall bleibt bestehen.
- Drittanbieter-/mehrdeutige Organisatoren ohne eindeutige Mitarbeiterverknüpfung erscheinen als „Nicht zugeordnet“.

## Prüfung und Deployment

- 143 Python-Tests und 6 JavaScript-Tests erfolgreich.
- Neue Tests für Tagesgrenzen/Sommerzeit, über Mitternacht laufende Buchungen, Raum-/Schreibtischstatus, Zukunft ohne echte Belegung, XSS-Escaping, Bildvalidierung, Planrevisionen, fehlgeschlagene Speicherung, Rollen-/Leserechte, Fotocache, Bildgrößenlimit und Token-Erneuerung.
- Lokale Browserprüfung mit ausschließlich synthetischen Daten: Tageswechsel, Drag-and-drop, Abbrechen, Tastaturpositionierung, Speichern und responsive Breite 390 px.
- HA-Backup 51c4dd24 vom 15.11.2026 23:43 Europe/Berlin: Konfiguration, Datenbank und ssl, NASHome, keine Apps.
- Lokale Quellen vor Änderung: backups/pre-floorplan-0120.
- Vorprüfung im echten HA-Container: Modulimport und WebSocket-Schema erfolgreich; lesender Graph-Fototest bei zehn Mitarbeitern: zwei Fotos verfügbar, acht ohne Foto. Keine zusätzlichen Berechtigungen erforderlich.
- Paket mit 36 Dateien installiert, alle Hashes sowie unveränderte 0.11.0-Basis verifiziert. Quellbackup /config/desk_booking_backup_0120_20261115_234719. HA-Konfigurationsprüfung erfolgreich; Neustart ausgeführt. Dashboard und laufende API werden noch geprüft.
- Paket-SHA256: 03b086280d70f4a674b8c48c08d68189cd5b0edc17c64a7a6ba2f9a6656dc1a6.

Der konkrete Gebäudegrundriss wurde noch nicht geliefert. Die Vorschau unter dev/ ist ausdrücklich synthetisch und wird nicht mit der Integration ausgeliefert.

## Abschluss der Live-Prüfung

0.12.0 läuft nach Neustart erfolgreich. Die authentifizierte Raumplan-API liefert echte Ressourcen und Tagesbuchungen einschließlich Mitarbeiterzuordnung; keine Desk-Booking-Systemlogfehler. Alle 162 zuvor registrierten Entitäten mit unveränderten Entity-/Unique-IDs erhalten.

Dashboard: https://ha.example.invalid/desk-booking/raumplan. Modulressource 64797138dc1448d595075d1cede5ca75. Zentraler leerer Plan Büro: ID-ENTFERNT, Revision 1. Erstellung und Speicherung im echten Browser sowie Persistenz nach Neuladen bestätigt. Live-Belegung und tatsächliches Mitarbeiterfoto im temporären Entwurf geprüft; Testposition anschließend verworfen. Es sind keine erfundenen Gebäudepläne oder Arbeitsplatzpositionen gespeichert. Editor zum Hochladen und Platzieren geöffnet. Screenshot: floorplan-live-0120.png.
