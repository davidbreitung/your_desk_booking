> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking 0.10.0 — Check-in und tägliches Auschecken

## Regeln

- Jeder neue Check-in liest den Ressourcenkalender direkt. Fehler/veraltete
  Kalenderdaten sperren neue Check-ins; Auschecken bleibt möglich.
- Laufende und in höchstens 60 Minuten beginnende Reservierungen schützen den
  Tisch für ihre anhand der Entra-ID zugeordnete Person. Unklare Identitäten und
  widersprüchliche Reservierungen sperren den Check-in.
- Ein belegter Tisch bleibt geschützt. Derselbe Mitarbeiter kann folgenlos
  erneut einchecken. Eine Nutzung ohne Reservierung endet erst beim Auschecken.
- Nach Ende einer zum Check-in gehörenden Reservierung darf eine andere Person
  übernehmen, sofern keine geschützte Folgereservierung entgegensteht.
- Ein Wechsel wird erst nach bestätigter Übertragung der neuen Tischhöhen
  abgeschlossen. Bei einem Fehler wird der vorherige Zustand wiederhergestellt;
  bei fehlgeschlagener Wiederherstellung bleibt der Tisch als Fehler gesperrt.
- Ablehnung: `Bereits gebucht...`, Priorität 1, roter animierter Ring, 30 Sekunden.
  Kalenderfehler bekommen eine eigene verständliche Meldung.
- Endwarnung ab 30 Minuten Restzeit, einmal je Ereignis/Endzeit:
  `Achtung, Reservierung endet bald. Bitte nachbuchen, falls benötigt...`,
  ebenfalls roter animierter Ring. Verlängerungen werden berücksichtigt.
- Bei mehr als 30 Minuten laufender, noch nicht beendeter Reservierung ohne
  bisherigen Check-in und bei freiem Tisch wird die konkrete Reservierung im
  Schreibtisch-Ressourcenkalender gelöscht. Ein zwischenzeitlicher Check-in
  verhindert das. Attendance und Warnungen werden über Neustarts gespeichert.
- Vor einer Löschung wird das Ereignis erneut gelesen. Nur unveränderte
  Einzeltermine/Vorkommen/Ausnahmen mit ETag sind erlaubt, keine Serienmaster.
  DELETE enthält If-Match. Anschließend wird der Kalender erneut gelesen.
  Organisator-Kalender und Places-Schreibtischobjekte werden nicht gelöscht.

## Tägliches Auschecken

Standard gemäß Nutzerwunsch: **00:00**, lokale Home-Assistant-Zeitzone.
Konfigurierbar am Zahnrad der Integration unter **Buchungen** als HH:MM.
Ein Statussensor an der Zentrale zeigt Uhrzeit, Zeitzone und offene Versuche.
Die Prüfung läuft alle 30 Sekunden. Fehlgeschlagene Abmeldungen werden mit
derselben ursprünglichen Mitarbeiterzuordnung erneut versucht. Eine inzwischen
andere Person wird nicht abgemeldet. Beim erstmaligen Installieren wird kein
vergangener Tagesabschluss rückwirkend ausgeführt. Nach späteren Ausfällen wird
ein verpasster Abschluss nachgeholt. Datumsbasierte Ausführung verhindert doppelte
Tagesabschlüsse bei der Zeitumstellung.

## Microsoft Places

Calendars.ReadWrite als Anwendungsberechtigung wurde laut Nutzer ergänzt und
mit Administratorzustimmung versehen. Die native Places-Check-in-API unterstützt
derzeit ausschließlich delegierte Benutzeranmeldung, keine App-Anmeldung.
Daher bleibt HA führend für Check-in. Native Places-Autorelease sollte für diese
Schreibtische deaktiviert sein, damit belegte Tische nicht parallel freigegeben
werden. Anleitung wurde dem Nutzer übermittelt; die Abschaltung ist nicht durch
die Integration erfolgt.

https://learn.microsoft.com/en-us/graph/api/place-post-checkins?view=graph-rest-1.0
https://learn.microsoft.com/en-us/graph/api/event-delete?view=graph-rest-1.0
https://learn.microsoft.com/en-us/microsoft-365/places/what-is-places/admin-web-app

## Prüfung und Sicherung

126 lokale Tests bestanden (HA-Grenzen simuliert), inklusive Zeitgrenzen,
Reservierungsschutz, Nichtanreise, Serien-/ETag-Schutz, fehlender Berechtigung,
einmaliger Warnungen, sicherem Nutzerwechsel und Tagesabschluss-Wiederholung.
Es wurden keine echten Kalenderbuchungen zu Testzwecken gelöscht.

HA-Backup: `30b08fd6`, 15.11.2026 22:44 Europe/Berlin, Konfiguration inklusive
Datenbank und SSL. Lokale Quellensicherung: `backups/pre-checkin-20261115-223538`.
Paket SHA256: `526a2acdd73231212d65e2119e2d5fb215f9611a836d83b718a4a3eb0116b40d`.

Quelldateien installiert; Quellensicherung auf HA:
`/config/desk_booking_backup_0100_20261115_224938`.
Alle 32 Paketdateien wurden beim Installieren per SHA256 geprüft.
Der rein lesende Graph-Test bestätigte `Calendars.ReadWrite` als App-Rolle,
Zugriff auf beide Ressourcenkalender und ETag/Typ `singleInstance` beim geprüften
Termin. Dabei wurden keine Termine geändert. HA-Konfigurationsprüfung erfolgreich.
Neustart ausgelöst; laufender Status und UI werden anschließend geprüft.
