> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Anzeige und Lichtsteuerung

## Einstellungen

- **Desk Booking → Konfigurieren**: Firmenname für alle Schreibtische.
- **Tisch bearbeiten**: Anzeigename für diesen Schreibtisch sowie bis zu vier dimmbare Lichter in Seitenreihenfolge. Ohne eigenen Anzeigenamen wird der Tischname verwendet.
- Änderungen der Namen und Lichtzuordnung werden an die vorbereitete Firmware übertragen; dafür ist kein erneutes Firmware-Update erforderlich.
- Jedes zugeordnete Licht erhält eine eigene Dimmerseite mit seinem Home-Assistant-Namen. Nicht belegte Seiten werden beim Wischen übersprungen.
- Drehen bzw. Berühren des Dimmerrings stellt die Helligkeit ein; 0 % schaltet aus. Ringdruck schaltet das Licht der aktuellen Seite um.
- Die Integration übernimmt diese Steuerung selbst. Bisherige Automationen für dasselbe Display müssen deaktiviert sein, damit insbesondere Ringdruck nicht doppelt ausgeführt wird.
- Änderungen außerhalb des Displays werden derzeit nicht auf den Dimmerring zurückgespiegelt; dies entspricht der bisherigen Automationsanbindung.

## Nachrichten

Check-in und Check-out verwenden eine eigene Displayaktion mit grünem animiertem Ring. Die Prioritätsfarben normaler Nachrichten bleiben erhalten. Die grüne Frei-Anzeige bleibt ein statischer Ring.

## Verhalten bei Neustart

Gespeicherte Dimmerwerte, wiederhergestellte Ereignisse und das Wiederverbinden lösen keine Lichtaktion aus. Nur neue Bedienänderungen werden weitergegeben. Die Displaybeleuchtung wird als Ziel abgewiesen.

## Validierung

33 lokale Tests bestanden: bestehende Check-in-Transaktionen, Profile, vier unabhängige Lichtziele, Entprellung, Ringdruck, Verbindungsausfälle und Abmelden der Listener.

Am 15.11.2026 erfolgreich mit ESPHome 2026.10.2 gebaut (98,4 % der App-Partition) und per OTA installiert. Integration 0.3.0 mit HA 2026.11.1 importiert, nach Neustart erfolgreich geladen. Sicherungen auf dem HA-System: `/config/desk_display_backups/before-controls-20261115_162135.yaml` und `/config/desk_booking_backup_20261115_162316`.

Live geprüft: Display-Regelwert 40 % schaltet die zugeordnete Deckenleuchte auf Helligkeit 102/255, 0 % schaltet sie aus. Beide früheren Automationen waren dabei aus und bleiben als Rückfallmöglichkeit deaktiviert erhalten. Abschließend wurde der frühere Display-Regelwert 85 % wiederhergestellt und das Licht ausgeschaltet.

Globale Firmen- und lokale Arbeitsplatznamen wurden testweise geändert und zurückgesetzt; der Empfang beider Änderungen ist im Displayprotokoll bestätigt. Ein-/Auschecken löste jeweils die neue Aktion `Check-in Nachricht senden` aus. Tisch abschließend frei, `[TEST] Alex Beispiel` ausgewählt.

Vier Kanäle sind im Gerät vorhanden und ihre getrennte Zuordnung ist automatisiert getestet. Am realen Tisch ist bislang nur die bisherige Deckenleuchte zugeordnet. Die optische Kontrolle der neuen grünen Meldungen sowie das Blättern bei mehreren real zugeordneten Lichtern wurde nicht per Kamera geprüft. Ein einzelner LVGL-Zeitschwellwert von 528 ms trat beim Auschecken auf, ohne Verbindungsabbruch.
