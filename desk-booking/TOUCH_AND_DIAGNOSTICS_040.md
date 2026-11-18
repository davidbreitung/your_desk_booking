> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Touch-Bedienung und Displaydiagnose

## Bedienung und Konfiguration

Die vier vorbereiteten Dimmerseiten haben jeweils Ein-/Aus-Tasten. Ringdruck weckt nur noch das Display auf; die bisherige Umschaltfunktion ist entfernt. Drehen und Berühren des äußeren Dimmerrings regeln weiterhin die Helligkeit.

Ab zwei zugeordneten Lichtern erscheint oberhalb der allgemeinen Navigation eine zweite Symbolleiste. Sie zeigt nur zugeordnete Lichter, zentriert die Symbole und markiert die aktuelle Lichtseite. Antippen wechselt direkt zur gewünschten Lampe. Bei null oder einem Licht ist die Leiste ausgeblendet.

Unter **Tisch bearbeiten** folgt nach der Lichtauswahl ein Schritt für individuelle Lichtnamen und Symbole. Leerer Name übernimmt den Home-Assistant-Namen. Namen und Symbole werden nach Gerätekennung gespeichert, sodass sie bei einer geänderten Reihenfolge beim richtigen Licht bleiben.

Die vereinbarte kompakte Auswahl besteht aus MDI-Symbolen für Glühbirne, Deckenspot, LED-Band, Deckenleuchte, Stehlampe und Schreibtischlampe. Die Bilder sind offline in der Firmware vorhanden; Änderungen in der Integration benötigen kein neues Firmware-Update. Die Icons verwenden einfarbige Alphamasken mit geglätteten Kanten.

## Diagnose ausschließlich im ESPHome-Gerät

Nachtrag: Die Firmware-Partitionen wurden anschließend auf je 3,5 MiB erweitert.
Die aktuelle Flash-Belegung beträgt etwa 49,8 %. Die unten genannten 99,55 %
beschreiben den Stand vor der Erweiterung. Details: [FLASH_EXPANSION.md](FLASH_EXPANSION.md).

Die folgenden Sensoren gehören zum ESPHome-Display, nicht zu Desk Booking:

| Sensor | Bedeutung |
|---|---|
| CPU Auslastung | Aktive Zeit als Mittel über beide Kerne im letzten Messintervall; aus den FreeRTOS-Leerlaufzählern. Der erste Messpunkt benötigt zwei Stichproben. |
| RAM Belegung | Anteil des belegten internen, byteadressierbaren Heap-Speichers. |
| PSRAM Belegung / PSRAM frei | Belegung und freie Bytes des externen Arbeitsspeichers. |
| Heap frei / Heap groesster Block | Freier Heap und größte zusammenhängende freie Allokation laut ESPHome-Debug-Komponente. |
| Heap Fragmentierung | Fragmentierungskennzahl des Heaps. |
| Schleifenzeit Maximum | Längste Zeit zwischen Hauptschleifen-Durchläufen im Messintervall; hilfreich bei ruckelnder Bedienung. |
| Firmware Flash Belegung | Anteil der laufenden Firmware an ihrer OTA-App-Partition; kein Maß der CPU- oder RAM-Last. |

Messintervall 30 Sekunden; Flash-Belegung wird einmal ermittelt und alle fünf Minuten veröffentlicht. Die CPU-Messung berücksichtigt den Überlauf des Laufzeitzählers. Bei fehlenden Zählern wird kein erfundener Prozentwert geliefert.

Grundlagen: [ESPHome Debug](https://esphome.io/components/debug/) und [ESP-IDF FreeRTOS](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32/api-reference/system/freertos_idf.html).

## Prüfung

39 lokale Tests erfolgreich, darunter getrennte Lichtziele, Ein-/Aus-Befehle, Ignorieren alter Ring-Toggle-Ereignisse, erster Touch nach Neustart, Unterdrückung wiederhergestellter Ereignisse, Abbruch wartender Dimmerbefehle beim Ausschalten sowie Namen/Symbole bei umsortierten Lichtern.

Am 15.11.2026 mit ESPHome 2026.10.2 erfolgreich gebaut und per OTA installiert. Die Alphamasken sparen gegenüber den zunächst verwendeten RGB-Icons 18.308 Bytes. Firmware: 1.826.752 Bytes einschließlich Bildheader, bei 1.835.008 Bytes je OTA-Partition (8.256 Bytes frei). Die vorhandene Partitionierung wurde nicht verändert. Weitere Erweiterungen benötigen zusätzliche Speicheroptimierung.

Integration 0.4.0 wurde mit den echten HA-Bibliotheken erfolgreich importiert. Sicherungen: `/config/desk_display_backups/before-touch-20261115_164522.yaml` und `/config/desk_booking_backup_20261115_165104`.

Nach Neustart erfolgreich geladen, beide bestehenden Deckenleuchten und die vom Nutzer geänderten Namen erhalten. Der Nutzer hat Symbolleiste, Ein-/Aus-Tasten für beide Lampen und den Wegfall des Ring-Schaltbefehls am physischen Display bestätigt.

Gerätemessung nach dem Update: CPU zunächst 3,8 %, später 2,5 %; interner Heap etwa 39 %, PSRAM etwa 11,2 %, freier Heap etwa 184 kB. Die maximale Schleifenzeit lag zunächst bei 430 ms, später im ruhigen Intervall bei 22 ms. Das belegt keine dauerhafte CPU-/RAM-Überlastung; einzelne längere Zeichenoperationen bleiben anhand der Schleifenzeit beobachtbar. Flash-Belegung vom Gerät: 99,55 %.
