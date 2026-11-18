> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking 0.13.2

Stand: 16.11.2026. Erweiterung derselben Custom-Integration.

## Funktionen

- Raumplan: kreisförmige Marker, 9 statt 3 px Statusrahmen vor Skalierung, M365-Fotos und Initialen als Ersatz. Details beim Überfahren; Klick/Touch schaltet die angehefteten Details um. Escape/außerhalb schließt. Zoom 25–300 % plus Einpassen; Bild und Marker skalieren zusammen. Bestehende Planpositionen bleiben im bisherigen Koordinatenmodus; beim Bearbeiten werden sie anhand der sichtbaren Marker in obere linke Ankerpunkte umgerechnet. Erst Speichern schreibt diese Migration.
- Neue Karte `custom:desk-booking-attendance`: Datumsnavigation, optional `plan_id`, eine Person pro Kalendertag, frühester Beginn/spätestes Ende auf Tagesgrenzen begrenzt. Raumreservierungen nur über Organisatoren. Aktuelle Check-ins nur heute; Walk-ins ohne erfundene Endzeit. Keine historische Anwesenheitsdatenbank.
- Konfigurieren → Objekte verwalten: globales Ein-/Ausblenden in Desk-Booking-Karten und Auswahllisten. Die native Home-Assistant-Geräteliste selbst bleibt bestehen; diese hat keinen von der Integration genutzten Sichtbarkeitsfilter. Ausblenden ist keine Zugriffsberechtigung und ändert weder Synchronisierung noch aktive Zuordnungen.
- Nur inaktive, nicht eingecheckte und nicht als aktueller Mitarbeiter referenzierte Objekte können mit separater Bestätigung lokal gelöscht werden. Bereinigt Entitäten, Geräte, Planpositionen, Fotos, Kalendercache und Versandhistorie; fordert Recorder-Purge für die Entitäten an. Keine Microsoft-Löschung, keine Backup-Löschung. Produktive Löschung nicht ausgeführt.
- E-Mail-Sensor pro M365-Objekt; bestehende deaktivierte HA-Geräte bleiben deaktiviert. Gruppen-Delta-Schema wird auf 3 erneuert, damit das zusätzliche mail-Feld auch für bestehende Gruppen eingelesen wird. Fehlende Microsoft-Adresse bleibt unbekannt.
- Zentraler Absender, zwei getrennte Erinnerungsarten mit Schalter/Betreff/Klartext/Vorlauf. Standard 15 Minuten vor Beginn und 5 Minuten vor No-show-Verfall (Beginn + 30 Minuten). Beide standardmäßig AUS. Start gilt für Schreibtische und Räume; Verfall nur Schreibtische. Zugeordneter Check-in bzw. gespeicherte Teilnahme unterdrückt Erinnerungen.
- Persistente Versandversuche vor dem POST. Keine Wiederholung potenziell angenommener POSTs, auch bei Timeout/5xx. Microsoft 202 heißt angenommen, nicht zugestellt. Bekannte Ablehnungen und 429 mit Mindestpause bzw. Retry-After. Frischer Eventabruf vor Versand verhindert Erinnerungen aus stornierten/geänderten Cache-Daten.
- Platzhalter: {mitarbeiter}, {ressource}, {beginn}, {ende}, {verfallzeit}, {dashboard_link}. Info-Dialoge für alle Platzhalter und Microsoft-Berechtigungen; Vorschau und expliziter Testversand.
- Aktion `desk_booking.send_email` für Administratoren und lokale Automationen, konfigurierter Absender. Felder recipient/subject/message, Klartext.

## Installation und Prüfungen

- Vollbackup vor Änderungen: 41adf2c7, 16.11.2026 07:39:51 Europe/Berlin, HA-Konfiguration inklusive Datenbank und SSL.
- Quellbackup vor erster Installation: /config/desk_booking_backup_0130_20261116_075648; vor letzten Dialogkorrekturen: /config/desk_booking_backup_0132_20261116_080827.
- 159 Python-Tests und 9 JavaScript-Tests erfolgreich; anschließend zwei zusätzliche Dialogtests zusammen mit den neun bestehenden Flow-Tests erfolgreich. Reale HA-Import-/WebSocket-Prüfung erfolgreich, Konfigurationsprüfung erfolgreich.
- Live-Test fand und korrigierte die Kategorie der E-Mail-Sensoren (diagnostic statt config), optionalen Dashboard-Link und die ICU-Escapierung der Platzhalterhilfe.
- Abschließend Version 0.13.2 geladen: M365- und Buchungssync ok, keine Desk-Booking-Fehler im Systemprotokoll. Platzhalterhilfe und optionales Linkfeld live geprüft. Native Geräteliste: 27 Geräte, 189 Entitäten. 26 E-Mail-Entitäten, davon zwei durch bereits deaktivierte Geräte ebenfalls deaktiviert.
- Temporäres Aus-/Einblenden von inaktivem Stand Up 1 via Options Flow geprüft und vollständig zurückgesetzt; Snapshot zählte 7 statt 8 Ressourcen während des Tests.
- Dashboard desk-booking enthält Raumplan und Anwesenheit. Bestehender Büro-Grundriss und sechs Positionen erhalten (Revision 7 bei Prüfung). Neue Anwesenheitskarte nutzt diesen Plan als Filter.
- Mail.Send vom Administrator ergänzt. Eine Testmail an booking@example.invalid wurde von Graph mit 202 angenommen. Beide automatischen Erinnerungen bleiben deaktiviert. Dashboard-Link auf https://ha.example.invalid/desk-booking gesetzt.
- Paket SHA256: f06408b65d8cfd0b078d26e869da9f891510b733f0a585416498f83acbe38b9f.

## Display

Schreibtisch Display 01: nach Check-in EINGECHECKT blau (#3399FF), kein Statusring; laufende Reservierung überschreibt den Check-in nicht mehr. Doppelter Name oben nur auf Check-in-Seite ausgeblendet, unten während Check-in leer. Vorhandene Warnungs-Overlays bleiben unverändert.

Firmware mit ESPHome 2026.10.2 gebaut und OTA erfolgreich installiert (Exit 0). Build 16.11.2026 07:59:12 +0100, Konfigurationshash 0x9bbf85be, Flash 50,8 %, RAM 38,6 %. Anschließende API-Verbindung zum Gerät und die neue Buildzeit bestätigt. Ohne Kamera keine direkte optische Prüfung des physischen Displays; keine produktiven Check-ins oder Kalenderbuchungen zum Testen verändert.

Power BI und SSO wurden nicht umgesetzt (zurückgestellt/verworfen).
