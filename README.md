# Your Desk Booking

Dieses Repository führt den vorhandenen Desk-Booking-Stand **0.15.2** und das weitere Zielbild zusammen. Der HA-Domainname bleibt `desk_booking`; es wird keine zweite Integration angelegt.

## Vorhandene Funktionen

- Microsoft-365-/Entra-Benutzer, Gruppen und Places-Schreibtische/Räume synchronisieren.
- Ressourcenreservierungen mit Personenzuordnung, lokalem Cache und konfigurierbaren Intervallen lesen.
- Lokaler Check-in mit Reservierungsschutz, Nichtanreise-Freigabe, Endwarnung und Tagesabschluss.
- Projektspezifische ESPHome-Displaysteuerung, Höhen/Favoriten, Zubehör, Gruppen-/Displaynachrichten und E-Mail-Erinnerungen.
- Raumplan- und Anwesenheitskarte mit M365-Fotos, Tagesplanung und Reservierungslink.
- Zwei aktuelle Handbücher, zentral in der Integration verlinkt und bei Änderungen geprüft.

Native Places-Check-ins, Ad-hoc-Buchungserstellung, fertige NFC-/DESFire-Identifikation, SSO, Power BI und weitere Kommunikationsintegrationen sind **nicht** als implementiert auszugeben. Siehe [Anforderungsabgleich](REQUIREMENTS.md) und [aktueller Status](STATUS.md).

## Einstieg

- [Benutzerhandbuch](docs/USER_MANUAL.md)
- [Administratorhandbuch](docs/ADMIN_MANUAL.md)
- [Architektur und Zielbild](docs/architecture.md)
- [Hardware](docs/hardware.md)
- [Schnittstellen](docs/integrations.md)
- [Power-BI-Planung](desk-booking/POWER_BI_PLAN.md)
- [Importumfang und Neutralisierung](docs/SOURCE_IMPORT.md)
- [Entwicklungsregeln](AGENTS.md)

Der Integrationscode liegt unter `desk-booking/custom_components/desk_booking`. Diesen Ordner vollständig nach `/config/custom_components/desk_booking` kopieren; vorherige Version sichern. Die enthaltenen HTML-Handbücher sind über **Desk Booking → Konfigurieren → Handbücher** erreichbar. Geräte- und Zugangsdaten werden nicht aus GitHub übernommen.

## Entwicklung und Prüfung

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s desk-booking/tests -q
node --test desk-booking/tests/*.test.mjs
python desk-booking/documentation.py --check
```

Nach redaktioneller Handbuchprüfung `python desk-booking/documentation.py --review` ausführen. Dies erzeugt HTML und die Spiegel unter `docs/`; `package_m365.py` blockiert ungeprüfte Quellenstände.

```sh
python desk-booking/package_m365.py
```

Historische Einmalskripte und Releaseberichte unter `desk-booking/` sind keine universellen Installationsanweisungen. Keine produktiven Zugangsdaten, Mitarbeiterdaten, Backups, Registry-Dumps oder Laufzeitaufnahmen committen. Der öffentliche Import wird getrennt von der ursprünglichen Produktivinstallation geprüft und nicht automatisch dort bereitgestellt.
