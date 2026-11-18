> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Spätere Auswertung mit Microsoft Power BI

Festgehalten am 15.11.2026 auf Wunsch des Benutzers. Nur Planung für später; keine Implementierung oder Bereitstellung beauftragt. Die technische Architektur ist ein Vorschlag, keine bereits getroffene Infrastrukturentscheidung.

## Gewünschte Auswertungen

- Pro Mitarbeiter: verspätete Annahme einer Reservierung, Anzahl und Verspätung in Minuten.
- Pro Mitarbeiter: vorzeitiger Check-out, Anzahl und verbleibende Minuten.
- Pro Mitarbeiter: Aufgabe einer Reservierung, Anzahl und freigegebene Minuten.
- Pro Mitarbeiter: ungenutzte, verfallene Reservierungen / No-shows.
- Pro Arbeitsplatz: Buchungsfrequenz und Auslastung.
- Flexible Filter nach Zeitraum, Mitarbeiter, Gruppe, Arbeitsplatz und Standort; bevorzugte Auswertung in Power BI.

## Vorgeschlagene Speicherung

Desk Booking erfasst einzelne Ereignisse und Nutzungssitzungen statt ausschließlich kumulierter Zähler. Dauerhafte SQL-Auswertungshistorie, vorzugsweise PostgreSQL; lokale dauerhafte Übertragungswarteschlange für Datenbankausfälle und eindeutige Ereignis-IDs gegen Duplikate. Check-in darf nicht von der Erreichbarkeit der Auswertungsdatenbank abhängen.

Tabellen / Datenbereiche:

- Mitarbeiter: interne ID, Entra-Tenant und Objekt-ID, Anzeigename, Aktivstatus.
- Arbeitsplätze: interne ID, Places-ID, Name, Standort und historisch gültige verfügbare Betriebszeiten.
- Reservierungen: stabile interne Buchungs-ID, Microsoft-Zuordnung, Mitarbeiter, Arbeitsplatz, Beginn, Ende und Status; jede Serieninstanz separat.
- Buchungsänderungen: ursprüngliche und neue Zeiten, Änderungszeitpunkt, Stornierung oder automatische Freigabe; frühere Werte erhalten.
- Nutzungssitzungen: tatsächlicher Check-in und Check-out, Mitarbeiter, Arbeitsplatz, Reservierungszuordnung und Check-out-Grund; mehrere Sitzungen je Buchung möglich.
- Ereignisse: Check-in/out, Aufgabe, No-show festgestellt, Freigabe erfolgreich/fehlgeschlagen; Quelle und eindeutige ID.
- Historische Gruppenzugehörigkeiten mit Gültigkeitszeiträumen, damit spätere Wechsel vergangene Auswertungen nicht verfälschen.

UTC-Zeitpunkte speichern, Auswertungstage nach Europe/Berlin bestimmen. Ereigniszeit und Erkennungszeit unterscheiden. Gelöschte Microsoft-Buchungen sowie deaktivierte Stammdatensätze in der Auswertungshistorie erhalten. Datenlücken und unsichere Zuordnungen kennzeichnen.

## Vorgeschlagene Kennzahlendefinitionen

- Verspätung: erster passender Check-in minus Reservierungsbeginn, soweit positiv. Toleranz erst in der Auswertung anwenden; exakte Zeitpunkte behalten.
- Vorzeitiger Check-out: letzter freiwilliger Check-out vor geplantem Ende. Späteren erneuten Check-in berücksichtigen; endgültige Bewertung nach Buchungsende.
- Automatischer Mitternachts-Check-out und Verdrängung durch einen anderen Mitarbeiter sind eigene Gründe, kein freiwilliger vorzeitiger Check-out.
- Aufgabe: bewusste Stornierung/Freigabe, vor Beginn und während der Buchung getrennt. Freigegebene Minuten und Vorlauf bis zum Beginn separat erfassen.
- No-show: kein passender Check-in bis zur gültigen Frist. Feststellung von erfolgreicher technischer Freigabe trennen. Blockierte Minuten bis zur Freigabe und freigegebene Restminuten unterscheiden.
- Buchungsfrequenz: Buchungen je Arbeitsplatz/Zeitraum; storniert und genutzt separat.
- Buchungsauslastung: reservierte Minuten / verfügbare Minuten.
- Nutzungsauslastung: eingecheckte Minuten / verfügbare Minuten.
- Buchungstreue: innerhalb der Reservierung genutzte Minuten / reservierte Minuten.
- Überlappende Zeitintervalle bei Auslastung nicht doppelt zählen. Check-in ist angemeldete Nutzung, kein Nachweis physischer Anwesenheit.

## Grenzen und noch festzulegende Regeln

Ein fünfminütiger Kalenderabruf liefert nicht zwingend den genauen Zeitpunkt oder Verursacher einer externen Stornierung. Verschwundene Buchungen nicht automatisch als bewusste Aufgabe durch den Mitarbeiter werten. Frühere Check-ins ohne gespeicherte Historie sind nicht rekonstruierbar. Toleranzen, Betriebszeiten, Aufbewahrungsdauer und Zugriffsrechte vor Umsetzung konkretisieren.

## Power BI und weitere Kennzahlen

Sternschema mit Buchungen und Nutzungssitzungen sowie gemeinsamen Dimensionen Mitarbeiter, Arbeitsplatz, Datum und Standort; historische Gruppenbeziehungen ohne Mehrfachzählung modellieren. Zunächst Import mit geplanter Aktualisierung; lokale Datenbank im Power-BI-Dienst über Datengateway anbinden.

Weitere Ideen: No-show- und Verspätungsquote, Median und Verteilung der Verspätung, reservierte ungenutzte Minuten, Spontannutzung, Überziehungsdauer, Wiederbelegung freigegebener Zeit, Auslastungs-Heatmap nach Wochentag/Uhrzeit, Buchungsvorlauf, Stornierungs- und Verlängerungsquote, abgewiesene Check-ins und Datenqualitätsquote.

Vorgeschlagener erster Ausbau: vollständige Ereignis-/Nutzungshistorie und Berichte zu Mitarbeiterverhalten, Arbeitsplatzauslastung und ungenutzten Reservierungen.

Referenzen:
- https://learn.microsoft.com/en-us/power-query/connectors/postgresql
- https://learn.microsoft.com/en-us/power-bi/guidance/star-schema/
