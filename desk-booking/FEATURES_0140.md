> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Desk Booking 0.14.0

Installiert und live geprüft am 16.11.2026.

- Raumplan zuerst; Überschriften, Planauswahl, Bearbeitung, Datum, Uhrzeit, Suche, Zoom und Legende darunter. Statuszahlen oben links im Bild, Live/Planung oben rechts; Overlays bleiben beim Scrollen/Zoomen am sichtbaren Bildbereich.
- Karteneditor: `eyebrow` und `title` editierbar; `show_eyebrow` und `show_title` unabhängig abschaltbar, bestehende Karten behalten ihre Überschriften.
- Zentral unter Konfigurieren → Raumplan: HTTPS-Reservierungs-URL und optionales Bearbeitungskennwort. Leeres Kennwortfeld behält vorhandenen Schutz; separate Option entfernt ihn. Aktuell kein Kennwort gesetzt.
- Kennwort nur als gesalzener PBKDF2-SHA256-Hash mit 600.000 Iterationen gespeichert. Prüfung im Executor, maximal fünf Versuche pro Minute und Benutzer. Freigabe an Benutzer und aktuellen Kennworthash gebunden, eine Stunde gültig, nach erfolgreichem Speichern verbraucht. Server prüft Freigabe bei jedem Speichern; Administratorrechte weiterhin erforderlich. Weder Hash noch Kennwort werden im Raumplan-Snapshot ausgegeben. Browser hält Freigabe nur im Speicher.
- Freie Plätze zeigen im Detailbereich „Reservieren“, Ziel öffnet separat mit `noopener noreferrer`. Keine Schreibtisch-/Datums-Vorauswahl im Places-Gebäudelink. Bei reservierten, eingecheckten, inaktiven oder unklaren Plätzen kein Reservierungsbutton.
- Vorgegebene Places-Gebäudeadresse zentral über Options Flow gespeichert. Andere Einstellungen bleiben erhalten.

## Prüfung und Deployment

- Lokales Quellbackup: `backups/pre-0140-20261116-135547/desk_booking`.
- Live-Dateien vor Installation gegen lokale 0.13.2-Prüfsummen geprüft. Live-Quellbackup: `/config/desk_booking_backup_0140_20261116_140257`.
- 164 Python-Tests erfolgreich, darunter Kennwortprüfung, Schreibsperre ohne Freigabe, falscher Benutzer, Freigabeverbrauch, Drosselung, Options Flow, URL-Prüfung, Bestandskompatibilität. 13 JavaScript-Tests erfolgreich, darunter Kartenanordnung, Überschriften, Reservierungsbutton und Bearbeitungsabfrage.
- `ha core check` und Import von floorplan/config_flow in der echten HA-Python-Umgebung erfolgreich. Danach Home Assistant neu gestartet.
- Ressource 64797138dc1448d595075d1cede5ca75 auf `/desk_booking_static/desk-booking-floorplan.js?v=0.14.0` aktualisiert und neue Karte im Chrome-Dashboard geprüft.
- Überschriften in Karteneditor-Vorschau ausgeblendet und ohne Speichern abgebrochen. Planbearbeitung ohne Kennwort geöffnet und abgebrochen. Produktives Kennwort nicht testweise gesetzt; geschützter Ablauf mit isolierten Tests geprüft.
- Live-Snapshot: sechs Ressourcen, alle Buchungsdaten aktuell, Büro-Plan Revision 8. Keine Planänderung gespeichert. Kein Desk-Booking-Eintrag im Systemfehlerprotokoll bei Abschlussprüfung.
- Reservierungsziel und `_blank` live geprüft; keine Reservierung ausgelöst.
- Screenshots: `floorplan-live-0140.jpg` und `floorplan-reservieren-0140.jpg`.
- Paket SHA256: `4e313edccee578f45d1dd85b98eb8a6013279bef25abdcdd81b78e2ec2b20fea`.

Die Installation tauscht ausschließlich Integrationsdateien aus. Rücknahme der Codeänderungen durch Wiederherstellung des genannten Quellbackups und Neustart; die Lovelace-Ressource kann wieder auf `?v=0.13.2` gesetzt werden. Kein Vollbackup-Restore erforderlich.
