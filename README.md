# Your Desk Booking

Arbeitsplatz-Buchungssystem mit Microsoft Places als geplantem führendem System, Home Assistant als Frontend und ESPHome-Displays am Arbeitsplatz.

> **Status:** Konzept und Anforderungsübernahme. Die technische Machbarkeit der Microsoft-Places-/Graph-API-Vorgänge ist noch zu verifizieren. Dieses Repository enthält derzeit ein Home-Assistant-Integrationstemplate, keine fertig implementierte Buchungslösung.

## Ziele
- Arbeitsplatzreservierungen und Check-ins über Microsoft Places verwalten.
- Freie Plätze vor Ort ad hoc reservieren und einchecken.
- Ein rundes ESPHome-Display mit Drehbedienung und NFC am Schreibtisch verwenden.
- Home Assistant als Anzeige- und Integrationsschicht nutzen, nicht als zweite führende Buchungsdatenbank.

## Dokumentation
- [Anforderungen](REQUIREMENTS.md)
- [Projektstand](STATUS.md)
- [Architektur](docs/architecture.md)
- [Integrationen und API-Prüfpunkte](docs/integrations.md)
- [Hardware](docs/hardware.md)
- [Entwicklungsregeln](AGENTS.md)

## Sicherheit
Keine Tokens, Mitarbeiterdaten, NFC-Schlüssel oder produktiven Home-Assistant-Konfigurationen committen. Das Repository ist öffentlich.

## Entwicklung
Die vorhandenen Template-Dateien sind ein Ausgangspunkt und müssen vor einem produktiven Einsatz angepasst werden. Änderungen sollen Anforderungen, Status und betroffene Handbücher konsistent halten.
