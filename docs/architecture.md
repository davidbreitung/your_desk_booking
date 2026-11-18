# Implementierte Architektur (Import 2026-11-18)

M365 führt Stammdaten und Gruppen, Places die Ressourcen, Exchange die Reservierungen. Home Assistant speichert geschützte lokale Zusatzdaten und Check-ins; Graph-App-Authentifizierung, Delta-/Kalendercache und ESPHome-Anbindung sind implementiert. Native Places-Check-ins und Ad-hoc-Microsoft-Buchungen sind nicht implementiert. Die folgende Zielarchitektur bleibt ein weiterer Planungsstand und beschreibt nicht den aktuellen Code.

---

# Zielarchitektur

## Datenfluss (geplant)
1. Microsoft Places / Microsoft 365 ist die führende Datenquelle für Mitarbeiter, Arbeitsplätze, Reservierungen und Check-ins.
2. Eine Home-Assistant-Custom-Integration stellt diese Informationen als Zustände und Aktionen bereit.
3. ESPHome-Displays zeigen den Belegungsstatus und erlauben Identifikation sowie Buchungsbedienung.
4. Bei spontaner Nutzung wird **zuerst** eine konfliktgeprüfte Reservierung im führenden System angelegt; erst nach bestätigter Rückmeldung wird ein erfolgreicher Check-in angezeigt.

## Zustandsmodell
- Frei: aktuell keine aktive Reservierung.
- Reserviert: aktuell reserviert bzw. belegt gemäß vereinbarter UI-Semantik.
- Unbekannt/Offline: keine zuverlässige Aussage; nicht fälschlich als frei darstellen.
- Konflikt: gleichzeitige Reservierung oder API-Ablehnung; Buchung nicht als erfolgreich anzeigen.

## Buchungslogik
Standard bis Werktagsende, Verkürzung in 15-Minuten-Schritten. Nächste bestehende Reservierung begrenzt die Endzeit. Zeitangaben in einer eindeutigen Zeitzone verwalten. Vorzeitiges Auschecken ist vorgesehen.

## Offene technische Prüfung
Die tatsächlichen Microsoft-API-Endpunkte, Berechtigungen, Verfügbarkeit und Lizenzbedingungen sind noch nicht validiert. Architektur und Buchungsablauf sind Anforderungen, keine bestätigte technische Implementierung.
