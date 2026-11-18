> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking 0.14.1 · Raumplan-Korrektur

16.11.2026: installiert und im Chrome-Dashboard geprüft.

- Überschriften wieder über dem Bild, weiterhin einzeln editierbar/ausblendbar.
- Vollständiger Grundriss mit proportionaler Höhe und 100 % Kartenbreite. Keine eigene Höhenbegrenzung, kein eigener Scrollbereich und keine manuelle Bildvergrößerung. Die Dashboard-Seite selbst kann normal scrollen.
- Reihenfolge: Überschriften → Bild mit Statuszahlen/Live-Anzeige → Legende → Datum → Uhrzeit → Suche/Nur frei → Planauswahl/Bearbeitung.
- Reservieren direkt im per Klick/Touch geöffneten Feld am Symbol eines freien Arbeitsplatzes. Link und Symbol sind getrennte native Bedienelemente, keine verschachtelten Schaltflächen. Link öffnet mit `_blank` und `noopener noreferrer`. Erklärender Satz zu Reservierungen/Anwesenheit entfernt.
- Symbol-Menüs bleiben lesbar unabhängig von der Symbolskalierung. Rechts bzw. unten liegende Menüs werden nach links bzw. oben versetzt, soweit erforderlich.
- Bestehende Planpositionen, zentrale Reservierungs-URL und Kennwortschutz unverändert.

Prüfung: 13 JavaScript-Tests erfolgreich, einschließlich Reihenfolge, Linkposition, Frei-Prüfung und Überschriften. Python-Backend gegenüber 0.14.0 unverändert; dessen 164 Tests wurden für diese reine Frontendkorrektur nicht erneut ausgeführt.

Live-Dateien vor Installation gegen 0.14.0-Prüfsummen geprüft. Lokales Backup `backups/pre-0141`, Live-Quellbackup `/config/desk_booking_backup_0141_20261116_144341`. `ha core check` erfolgreich. Frontend-Ressource auf `?v=0.14.1` aktualisiert und geladen; kein Core-Neustart notwendig. Die bereits geladene Integrations-Metadatenversion kann bis zum nächsten Neustart noch 0.14.0 anzeigen.

Live-DOM: Bild und Canvas 1652 × 780 px; Scroll- und Clientmaße des Bildbereichs identisch. Reservierungslink in `.caption` mit `_blank` bestätigt. Keine Planänderung gespeichert und keine Reservierung ausgelöst. Screenshot `floorplan-corrected-0141.jpg`.

Paket SHA256: `d7d054ec3cac20fd7312c23889a168c0ec2c2e835fd06bde4a00ba791bfd37fe`.
