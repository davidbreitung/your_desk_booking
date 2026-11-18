> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Zentrale Steuerung und zusätzliche Arbeitsplatzgeräte

## Bedienung

Die Integrationsoptionen enthalten Firmenname, normale Helligkeit, Standby-Helligkeit,
Standby-Wartezeit (0 deaktiviert Standby) und Rückkehr zur Check-in-Seite bei Standby.
Die Vorgaben werden an zugeordnete Displays übertragen und nach Wiederverbindung
erneut angewendet. Einzelne Geräte bleiben über ihre eigenen Entitäten bedienbar.

Das Gerät **Desk Booking Zentrale** bietet:

- Alle Displays ein-/ausschalten (mindestens ein Display an = zentraler Schalter an).
- Helligkeit aller Displays; dieser Wert wird auch als zentrale Vorgabe gespeichert.
- Nachrichtentext, Priorität, Anzeigedauer und Senden-Schaltfläche.
- Alle Mitarbeiter abmelden; ein fehlgeschlagenes Auschecken blockiert nicht die anderen Tische.

Die Aktion `desk_booking.notify_all` nimmt `message`, `priority` ("1", "2", "3")
und `duration` (1–300 Sekunden) entgegen. Priorität 1: roter animierter Ring;
2: gelber animierter Ring; 3: kein Ring. Check-in/-out behalten ihren grünen Meldungsring.
`desk_booking.checkout_all` meldet alle Tische unter Wiederherstellung ihrer vorherigen
Favoriten ab. Beide Aktionen melden Teilausfälle ausdrücklich.

## Drehrad und Touch

Wischen und Antippen von Menü-Symbolen bleiben verfügbar.
Im Auswahlmodus verschiebt Drehen die graue Markierung zwischen den belegten
Dashboard-Symbolen. Drücken öffnet das gewählte Dashboard und aktiviert dessen
Wertsteuerung. Erneutes Drücken führt zurück zur Menüauswahl.

Lichter behalten ihre eigene Symbolleiste ab zwei zugeordneten Lichtern.
Die Höhenseite regelt weiterhin die Tischhöhe. Die Rolloseite regelt die Position;
bei einer Jalousie mit Lamellenfunktion kann per Touch zwischen Höhe und Lamellen
als Drehradfunktion gewählt werden. Der Schaltkanal bietet Ein-/Aus-Tasten;
im Bedienmodus schaltet Drehen rechts ein und links aus.

## Tischkonfiguration

Ein Dialog enthält Display, Anzeigename, vier Lichtzuordnungen samt Namen/Symbolen,
eine Rollo-/Jalousiezuordnung samt Namen und einen Schaltkanal samt Namen/Symbol.
Leere Gerätenamen übernehmen den Entitätsnamen. Nicht zugeordnete Funktionen werden
im Menü ausgeblendet. Die Mitarbeiteranzeige verwendet den Namen im Profil.

## Übertragung und Wiederherstellung

Keine Licht-, Rollo-, Schalt- oder Nachrichtenbefehle werden beim Start wiederholt.
Rollorückmeldungen aktualisieren nur die Oberfläche; separate, frische Bedienereignisse
lösen Positionsbefehle aus. Nachrichten werden pro Display serialisiert.
Ausgeschaltete Displays werden durch normale Aktivität oder Helligkeitsänderungen
nicht wieder aufgeweckt; die eigene oder zentrale Display-Aktiv-Entität schaltet sie ein.

Die Firmware-Erweiterung wird mit `update_display_central.py` aus dem vorherigen
Firmwarestand erzeugt und behält vorhandene Zugangsdaten und die 16-MB-Partitionierung.
Die Diagnose bleibt vollständig im ESPHome-Gerät.

## Prüfstand

- 50 lokale Tests bestanden, darunter Teilausfälle, parallele Nachrichten,
  Wiederverbindung, Rollorückmeldungen, wiederholte Positionsbefehle und fehlende Lamellenfähigkeit.
- Import sämtlicher Plattformen mit Home Assistant 2026.11.1 bestanden.
- Dialog- und Profilnamenprüfung mit echten HA-Klassen isoliert bestanden.
- ESPHome 2026.10.2: Firmware-Build 1.855.207 Byte, 50,6 % des 3,5-MiB-Slots.
- Installation und OTA-Übertragung bestätigt.
- Zentrales Ausschalten und Helligkeitsänderung geprüft; ein ausgeschaltetes Display
  bleibt dabei aus. Einschalten über die Geräte-Entität geprüft, zentrale Anzeige folgt.
- Check-in, Lichtnamen und Favoriten nach Neustart erhalten; Mitarbeiter-Profilname live bestätigt.
- Zentraler Nachrichtenversand mit Prioritäten 1, 2 und 3 sowie Dauer 5 Sekunden live
  geprüft (Aktion und zentrale Senden-Schaltfläche); Parameter am Display bestätigt.
- Zentrale Standby-Wartezeit live von 120 auf 10 Sekunden geändert: Display dimmte auf
  10 %. Rückkehr-Option wurde im Belegungssensor übertragen. Ursprüngliche Einstellungen
  anschließend wiederhergestellt: 120 Sekunden, 50 % normal, 10 % Standby, Rückkehr aus.
- Physische Kontrolle von Drehrad, Menümarkierung und Rückkehr zur Check-in-Seite steht
  noch aus. Rollo/Jalousie und Schaltkanal sind aktuell nicht zugeordnet und wurden
  isoliert geprüft; kein fremdes Gerät wurde zum Test zugeordnet oder bewegt.
- Alle-abmelden wurde isoliert geprüft, der bestehende Live-Check-in blieb erhalten.

Sicherungen dieser Installation auf Home Assistant:
`/config/desk_booking_backup_20261115_175309` und
`/config/desk_display_backups/before-central-20261115_175309`.
