> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking 0.9.0 — Geräte nach Typ

Die Integration verwendet drei gemeinsame Home-Assistant-Untereinträge:
Mitarbeiter, Group und Schreibtisch. Die Zentrale bleibt direkt der Integration
zugeordnet. Die Standardoberfläche sortiert die Bereiche alphabetisch.

Cloud-Datensätze liegen getrennt davon unter `ConfigEntry.data.records`.
Ihre bisherigen internen IDs bleiben erhalten; Gerätekennungen und Entity-
Unique-IDs werden daraus weiterhin unverändert gebildet. Neue M365-/Places-
Datensätze nutzen automatisch den passenden vorhandenen Bereich.

Die Migration auf Config-Entry-Version 2 kopiert zunächst sämtliche Datensätze,
legt die Kategorien an, verschiebt Geräte und Entitäten über die öffentlichen
Registry-APIs und entfernt erst danach die leeren alten Untereinträge. Sie ist
wiederholbar und wird vor dem Start der Plattformen und Listener ausgeführt.
Es werden keine HA-Storage-Dateien direkt verändert. Auch deaktivierte
Entitäten werden zugeordnet; Historie, Namen, Labels, Bereiche, NFC, Höhen,
Check-in-Zustand und Displayzuordnungen bleiben erhalten.

Ein-/Auschecken liest vor jedem Schreibschritt den aktuellen Datensatz erneut,
damit vorherige Transaktionsschritte oder zwischenzeitliche Änderungen nicht
durch einen älteren Stand überschrieben werden.

Prüfungen: 106 lokale Tests bestanden, darunter Migration, unterbrochene und
wiederholte Migration, neue Cloud-Datensätze, Ressourcen-Konvertierung,
unveränderte Kennungen und Benutzerattribute sowie Ein-/Auschecken mit
Wiederherstellung der Tischhöhen. Die Tests verwenden simulierte HA-Grenzen.

Sicherungen vor der Installation:
- HA-Backup `a540c41d`, Konfiguration inklusive Datenbank und SSL,
  15.11.2026 22:17 Europe/Berlin.
- Lokale Quellen/Tests: `backups/pre-grouping-20261115-221526`.
- Installierte Quellen: `/config/desk_booking_backup_090_20261115_222050`.
- Private Vergleichsdaten ausschließlich auf HA:
  `/config/desk-booking-090-baseline.json` (keine Zugangsdaten).

Ein einfaches Zurückkopieren von 0.8.1 nach erfolgter Datenmigration ist nicht
ausreichend, da diese Version die neue Datenstruktur nicht kennt. Zur Rückkehr
ist eine passende Rückmigration oder die ausdrücklich beauftragte Wiederherstellung
des HA-Backups erforderlich.

Paket SHA256: `eba9b92db77ce4b994180f6435ca2999ac6e0784474ba3731f0d2d7bbc61e181`.

Live installiert und nach Neustart geprüft: Version 0.9.0, Config-Entry-Version 2,
genau drei Kategorien mit 10 Mitarbeitern, 8 Gruppen und 2 Schreibtischen.
21 Geräte-IDs und 113 Entitäts-IDs einschließlich Unique-IDs, Zuordnungen und
Benutzereinstellungen wurden gegen den Stand vor der Installation verglichen.
Die aktuellen Registry-Daten stammen aus der HA-WebSocket-API, weil gespeicherte
Registry-Dateien nach Änderungen noch einen älteren Stand enthalten können.
Alle 30 installierten Quelldateien entsprechen den Paket-Prüfsummen.
HA-Konfigurationsprüfung erfolgreich; M365- und Buchungssynchronisierung beide
`ok`, keine Desk-Booking-Einträge im Systemfehlerprotokoll.

Beim ersten Vergleich nach Neustart waren sämtliche Datensatzfelder identisch.
Während der weiteren Prüfung änderten sich Check-in-Felder und später
`selected_profile` sowie `display_name`; diese zwischenzeitlichen Änderungen
wurden nicht zurückgesetzt. Alle anderen lokalen Datensatzfelder und die
Integrationsoptionen stimmen mit dem Ausgangsstand überein.

Die Schreibtisch-Zuordnung ist erreichbar über das **Zahnrad neben Desk Booking →
Schreibtisch bearbeiten → Tisch wählen → OK**. Der Dialog wurde live geöffnet:
Display, vier Lichter mit Namen/Symbolen, Rollo und Schaltkanal sind vorhanden.
Bestehendes Display und Licht von Schreibtisch 1 waren korrekt vorbelegt.
Es wurden im Dialog keine Werte verändert oder gespeichert.

Nachweise: `grouping-installation-090.png` und `desk-settings-090.png`.
