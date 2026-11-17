# Anforderungen – Your Desk Booking

Stand: 2026-11-17. Diese Datei dokumentiert besprochene Ziele, **nicht** bestätigte Implementierungen.

## Systemführerschaft
- Microsoft Places soll führend für Mitarbeiter, Arbeitsplätze, Reservierungen und Check-in-Informationen sein.
- Home Assistant dient als Frontend/Integrationsschicht; keine konkurrierende Buchungsdatenhaltung.
- Prüfen, welche Objekte und Operationen tatsächlich über unterstützte Microsoft-APIs verfügbar sind; API-Zugriff nicht voraussetzen.

## Arbeitsplatzbuchung
- Reserviert bedeutet für die Anzeige besetzt; ohne aktuelle Reservierung ist ein spontaner Check-in möglich.
- Ein Ad-hoc-Check-in soll im Hintergrund eine Reservierung im führenden System erzeugen.
- Standard-Endzeit: Ende des Werktags.
- Dauer über Drehrad in 15-Minuten-Schritten verkürzbar.
- Besteht später am selben Tag eine Reservierung, darf die neue Buchung höchstens bis zu deren Beginn reichen.
- Kürzere Aufenthalte und vorzeitiges Beenden des Check-ins ermöglichen.
- Konflikte, Race Conditions, Zeitzonen, Ausfälle und fehlende API-Berechtigungen berücksichtigen.

## Displays und Identifikation
- Rundes ESPHome-kompatibles Display am Schreibtisch; Bedienoberfläche nach Markenfarbgebung von your admins.
- NFC/RFID für Identifikation prüfen; PN532/ESP32-S3 als diskutierte Plattform.
- DESFire EV3 mit AES-Authentifizierung über eigene ESPHome External Component evaluieren.
- Schlüsselverwaltung, Offline-Verhalten, Kompatibilität und geschützten Türcontroller sicherheitsorientiert konzipieren.

## Benachrichtigungen und Informationen
- Erinnerung an reservierende Mitarbeiter ohne Check-in; Zeitpunkt und Kanal konfigurierbar.
- Nach Identifikation/Check-in optional persönliche Microsoft-365-Kalendertermine am Display anzeigen, unter Berücksichtigung der Privatsphäre.
- Gast- und Besucherverwaltung: temporäre Zugänge, zeitlich begrenzte Reservierungen, optional QR-/NFC-Zutritt, Benachrichtigung des Gastgebers.

## Externe Integrationen
- Discord-Online-Status von Mitarbeitern.
- Microsoft-Teams-Online-Status von Mitarbeitern.
- Inhalte eines Microsoft-Teams-Channels auf einer Karte darstellen.
- Docbee-Integration.
- Pascom-Anbindung.
- Für alle Integrationen: Authentifizierung, Berechtigungen, Datenschutz und API-Verfügbarkeit prüfen.

## Hardware und Gestaltung
- Gehäuse für rundes Display mit möglichst gleichmäßigem Außendurchmesser und kurzem, gebogenem Träger.
- Tischbefestigung von unten mit Gewindestab, ohne sichtbare Schrauben oben.
- Leuchtring mit überstehendem Milchglas-/Plexiglasdiffusor.
- Arbeitsplatzbeleuchtung für frei stehende Rücken-an-Rücken-Schreibtische: oben weißes Arbeitslicht, vertikal dezente farbige Beleuchtung (z. B. Türkis, WS2812); Blendung vermeiden.

## Qualitäts- und Sicherheitsanforderungen
- Keine Secrets oder personenbezogenen produktiven Daten im Git-Repository.
- Sichere Fehlerbehandlung, aussagekräftige Protokollierung ohne sensible Inhalte, Wiederanlauf nach Offline-Phasen.
- API- und Integrationsfähigkeit vor Implementierung mit reproduzierbaren Tests verifizieren.
- Nutzer- und Administratorhandbuch bei implementierten Änderungen aktualisieren.

## Offene Entscheidungen
- Exakte Microsoft-Graph-/Places-Endpunkte, Lizenzierung und Schreibrechte für Buchung und Check-in.
- Datenmodell und Zuordnung Microsoft Places ↔ Home Assistant ↔ ESPHome.
- Geräte-, NFC- und Türcontroller-Sicherheitsarchitektur.
- Genauer Hardwaretyp, Pinbelegung, Stromversorgung und Displaytreiber.
- Datenschutzfreigaben für Präsenz- und Kalenderanzeige.
