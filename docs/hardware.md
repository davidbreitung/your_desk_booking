# Vorhandene Firmware (Import 2026-11-18)

Die redigierte Referenz für ein ESP32-S3-Display mit 16 MB Flash, Touch und Drehrad liegt in `schreibtisch-display-01.checkedin.redacted.yaml`, ergänzt um Partitionsdatei, Ressourcen-Header und Hintergrundassets. Secret-Referenzen, Beispieladresse und HA-Entitäten vor Verwendung anpassen. Historischer Build/OTA-Erfolg gilt für das ursprüngliche Gerät, nicht für neue Hardware. NFC/DESFire, Türcontroller, Gehäuse, Diffusor und Beleuchtungsentwicklung bleiben die nachstehenden offenen Konzepte.

---

# Hardwarekonzept (Planungsstand)

- Rundes, etwa 2-Zoll-ESPHome-kompatibles Schreibtischdisplay; genaue Herstellerbezeichnung und Firmwarekonfiguration müssen ergänzt werden.
- Bedienung mit Drehrad; Zeitwahl in 15-Minuten-Schritten.
- NFC-Lesegerät (PN532 als diskutierte Option) mit ESP32-S3; DESFire EV3 und sichere AES-Authentifizierung gesondert evaluieren.
- Kompaktes gebogenes Trägerrohr, am Display möglichst ohne knollige Durchmesservergrößerung.
- Befestigung mittels Gewindestab durch die Tischplatte und Kontermutter von unten.
- Leuchtring mit leicht überstehendem milchigem Plexiglasdiffusor.
- Rücken-an-Rücken-Arbeitsplätze: weißes blendarmes Arbeitslicht oben, vertikal dezente farbige Effekte (z. B. Türkis).
- Elektrische Sicherheit, Wärmeabfuhr, mechanische Stabilität und normgerechte Arbeitsplatzbeleuchtung vor Umsetzung prüfen.

CAD-Dateien, Schaltpläne und produktive ESPHome-Konfigurationen wurden noch nicht übernommen.
