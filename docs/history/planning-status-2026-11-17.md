# Projektstatus

Stand: 2026-11-17

## Aktueller Zustand
Projektanforderungen aus bisherigen Gesprächen in dieses Repository übertragen. Es existiert ein Home-Assistant-Integrationstemplate; eine funktionsfähige Your-Desk-Booking-Integration ist damit **nicht** nachgewiesen. Keine produktive Home-Assistant- oder ESPHome-Konfiguration wurde importiert.

## Historische Aufgabenlage
Die bisherige Gesprächsplanung nennt **17 erledigte Aufgaben** und anschließend **43 offene Aufgaben**; danach kamen weitere neue Aufgaben hinzu (DESFire-EV3-Evaluierung, Check-in-Erinnerung, Kalenderanzeige, Gastverwaltung). Eine vollständige, verifizierte Einzelaufstellung der ursprünglichen 55 Aufgaben liegt hier nicht vor. Deshalb werden keine fehlenden Aufgaben oder Erledigungsnachweise erfunden.

## Dokumentierte nächste Arbeitspakete
1. Microsoft Places/Graph: lesende und schreibende Reservierungs-/Check-in-APIs, Rechte und Lizenzen verifizieren.
2. Home-Assistant-Datenmodell und Zustandsabgleich spezifizieren.
3. ESPHome-Display und Bedienelemente integrieren.
4. Ad-hoc-Reservierung mit 15-Minuten-Schritten und Konfliktprüfung implementieren.
5. NFC-/DESFire-EV3-Sicherheitskonzept evaluieren.
6. Kalender, Erinnerungen, Gastverwaltung und Kommunikationsintegrationen priorisieren.
7. Hardwaregehäuse, Diffusor und blendfreie Beleuchtung prototypisieren.
8. Vollständige historische Aufgabenliste abgleichen und erst danach GitHub-Issues vollständig migrieren.

## Tests
Keine Tests für Your Desk Booking ausgeführt; keine API-Fähigkeiten bestätigt.

## Risiken
- Microsoft Places bietet möglicherweise nicht alle benötigten Schreib-/Check-in-Funktionen über öffentlich unterstützte APIs.
- Öffentliches Repository: keine internen Mitarbeiterinformationen, Zugangsdaten, Schlüsselinhalte oder Betriebsdetails einpflegen.
- Ursprüngliche Aufgabenliste ist nur teilweise rekonstruierbar.
- Template-Code darf nicht als produktionsreife Integration interpretiert werden.

## Änderungsprotokoll
- 2026-11-17: Anforderungen, Architektur und bekannte Aufgaben aus Projektgesprächen übernommen; keine funktionalen Änderungen und keine Tests.
