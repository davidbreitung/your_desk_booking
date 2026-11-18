> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Handbücher · ausgelieferter Stand 0.15.2

16.11.2026: Benutzerhandbuch und Administratorhandbuch im Integrationsordner `frontend/docs` angelegt, mit aktueller Codebasis und projektspezifischer Display-Firmware abgeglichen. Allgemeine Microsoft-Berechtigungsangaben anhand primärer Microsoft-Dokumentation überprüft und verlinkt. Keine produktiven Zugangsdaten oder realen Objekt-/Gebäude-IDs in die ausgelieferten Handbücher übernommen.

## Inhalt und Nutzung

- Benutzer: Schnellstart, Geräteklassen, Raumplan/Anwesenheit, Reservieren, Check-in/-out, Nichtanreise/Endwarnung/Tagesabschluss, Displayfarben und Bedienung, Höhen, Gruppen-/Displaynachrichten, Mail-Erinnerungen und Fehlerhilfe.
- Administratoren: Installation/Update, Entra/App-Rechte, Exchange-Scopes, sämtliche zentralen Konfigurationsbereiche, lokale Zuordnungen, Objektverwaltung, Buchungsregeln, Kartenparameter/Bildgrenzen, Geräte/Entitäten/Aktionen, Firmware, Diagnose, Speicherung/Backups und Entwicklungsablauf.
- Bekannte Grenzen ausdrücklich festgehalten: keine automatische NFC-Scan-Verarbeitung, keine Places-Check-in-Rückmeldung, keine Raum-Check-ins, kein SSO/Power-BI-Archiv und die noch gesperrte Mitarbeiterauswahl am belegten Schreibtisch.
- Markdown als redaktionelle Quelle, daraus generiertes eigenständiges HTML mit Inhaltsverzeichnis, Abschnittssuche, Querverlinkung und Druckansicht. PDF über Browserdruck möglich; kein separates PDF-Artefakt ausgeliefert.
- Konfigurieren → Handbücher bietet beide HTML- und Markdown-Fassungen. Statische allgemeine Hilfe ohne zusätzliche Administratorschranke; personenbezogene Laufzeitdaten werden nicht eingebettet.

## Verbindliche Pflege

- Projekt-AGENTS.md verpflichtet weitere Arbeiten zur gleichzeitigen Handbuchpflege.
- `documentation.py --review` erzeugt nach redaktioneller Prüfung die HTML-Ausgaben und einen Reviewstand. `--check` prüft Runtime-Quellen, aktive redigierte Display-Firmware, Versionsstand, Markdown und HTML auf Abweichungen.
- `package_m365.py` verweigert nicht geprüfte Quelländerungen oder veraltete Ausgaben. Die Prüfung erkennt Abweichungen, ersetzt aber keine redaktionelle Qualitätskontrolle.
- Historische README-Abschnitte als solche gekennzeichnet und auf die aktuellen Handbücher verwiesen.

## Installation und Verifikation

- Lokales Quellbackup: `backups/pre-0150`, inklusive vorheriger README.
- Live-Quellbackup vor erster Installation: `/config/desk_booking_backup_0150_20261116_152054`.
- Weitere Live-Quellbackups: `/config/desk_booking_backup_0151_20261116_152622` und `/config/desk_booking_backup_0152_20261116_152950`.
- Alle Dateien gegen Ausgangs-/Paketprüfsummen geprüft. Endgültig 48 Paketdateien installiert, Home Assistant neu gestartet, Version 0.15.2 in der Integration aktiv. Konfigurationsprüfung erfolgreich.
- Live-Test korrigierte zwei HA-Besonderheiten: relative Standardlinks wurden vom SPA-Router abgefangen; literales HTML in ICU-Übersetzungen verursachte INVALID_TAG. Endgültig HTML-Anker mit `_blank` als Description-Placeholder, dadurch weder Übersetzungsfehler noch falsche Dashboard-Navigation. Keine festen Hostnamen in der Integration erforderlich.
- Endgültiger Stand: 169 Python-Tests erfolgreich, darunter vier Dokumentations-/Manipulationstests und der Hilfe-Dialogtest. Vor der Linkkorrektur 168 Tests erfolgreich. Karten-JavaScript und Firmware in diesem Release unverändert.
- Tatsächlicher Klick aus Konfigurieren → Handbücher öffnet beide Handbücher in separaten Tabs; Version 0.15.2 bestätigt. Benutzer-Suche nach Standby: 1 von 11 Abschnitten, Administrator-Suche nach Kennwort: vier passende Abschnitte samt vier TOC-Links. Tabellen, Inhaltsverzeichnis und Lesedarstellung visuell geprüft. Keine neue Buchung, E-Mail oder Geräteaktion für diese Tests erzeugt.
- Systemprotokoll nach Abschluss: keine desk_booking-Einträge. Lokaler Vorschau-Server nach Prüfung beendet.
- Screenshots: `benutzerhandbuch-live-0152.jpg`, `administratorhandbuch-live-0152.jpg`.
- Endgültiges Paket: `dist/desk-booking-0.15.2.zip`, SHA256 `ee0b5b4f61ab8d681ac38d217f6d5f32cc1da96bd19074ce25b16773a0b0e1d1`.
