> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Raumplan-Darstellung 0.12.1

- Gemeinsame Skalierung aller Objekte samt Text: 25–150 Prozent pro Plan.
- Deckkraft aller Objekte: 20–100 Prozent.
- Weiße Hintergründe der Symbole und Beschriftungen abschaltbar; Grundrissbild unverändert.
- Einzelgröße 16–140 statt 32–140; Foto, Statusabzeichen und Beschriftung skalieren mit.
- Bestehende Pläne ohne neue Felder behalten 100 Prozent Skalierung/Deckkraft und weißen Hintergrund.
- Validierung und Speicherung zentral über bestehenden Administrator- und Revisionsschutz.
- 144 Python-Tests, 6 JavaScript-Tests und Syntaxprüfung erfolgreich.
- Quellen vor Update lokal backups/pre-floorplan-0121 und remote /config/desk_booking_backup_0121_20261116_000458 gesichert. Unveränderte 0.12.0-Basis und alle Paketdateien anhand SHA256 geprüft.
- HA-Konfigurationsprüfung erfolgreich, Neustart zur Aktivierung ausgelöst.
Live-Abschluss: 0.12.1 aktiv, keine Desk-Booking-Systemlogfehler. Plan Büro Revision 4 mit sechs unveränderten Ressourcen gespeichert: 70 Prozent Skalierung, 80 Prozent Deckkraft, weiße Hintergründe aus. Speicherung über API und nach Browser-Neuladen verifiziert. Screenshot floorplan-live-0121.png.
