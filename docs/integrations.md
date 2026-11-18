# Vorhandene Schnittstellen (Import 2026-11-18)

M365-Verzeichnis, Places-Ressourcen, Exchange-Ressourcenkalender, Mail.Send und Home Assistant/ESPHome sind im importierten Code vorhanden. Historische Laufzeitprüfungen sind in den Entwicklungsberichten beschrieben; dieser Import führt keinen erneuten Produktivtest aus. Persönliche Kalenderanzeige, Teams/Discord-Präsenz, Channel-Inhalte, Docbee und Pascom bleiben offen. Die folgende Tabelle ist das frühere Zielbild.

---

# Geplante Integrationen und Prüfpunkte

| System | Ziel | Status |
|---|---|---|
| Microsoft Places / Graph | Führende Arbeitsplatz-, Mitarbeiter-, Reservierungs- und Check-in-Daten | API-Fähigkeit ungeprüft |
| Home Assistant | Frontend, Zustände, Aktionen | Integration noch nicht nachgewiesen |
| ESPHome | Arbeitsplatzdisplay und Bedienelemente | Gerätetyp und Firmware prüfen |
| Microsoft 365 Kalender | Persönliche Termine nach Identifikation | Datenschutz/API prüfen |
| Microsoft Teams | Mitarbeiter-Präsenz | API/Berechtigungen prüfen |
| Microsoft Teams Channel | Channel-Inhalte als Karte | API/Berechtigungen prüfen |
| Discord | Mitarbeiter-Online-Status | Bot/API/Einwilligung prüfen |
| Docbee | Externe Integration | Umfang offen |
| Pascom | Telefonie-/Kommunikationsanbindung | Umfang offen |

Keine dieser Schnittstellen gilt allein aufgrund dieser Planung als implementiert.
