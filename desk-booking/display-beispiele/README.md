# Display-Beispiele

Diese Bildschirmbeispiele wurden anhand der lokalen Firmware schreibtisch-display-01.reserved.redacted.yaml und der Integrationsdokumentation nachgebildet. Sie sind keine Screenshots des Geräts und keine pixelgenaue LVGL-Emulation. Schrift, Icons, Umbruch und Leuchteffekte können abweichen. Namen, Uhrzeiten, Werte und Gerätezuordnungen sind Beispiele. Animationen sind als Standbild dargestellt. Es wurden keine Geräte bedient, Nachrichten gesendet oder Firmwareänderungen vorgenommen.

01. **Frei** — Keine aktuelle oder in weniger als 60 Minuten beginnende Reservierung. Statischer grüner Ring.

02. **Spätere Reservierung** — Beispiel einer Reservierung in weniger als zwei Stunden, aber mindestens 60 Minuten: Tisch bleibt frei.

03. **Reservierung beginnt bald** — Weniger als 60 Minuten bis zum Beginn: gelber Text und statischer gelber Ring.

04. **Reservierung läuft** — Laufende Reservierung ohne Check-in: roter Text und statischer roter Ring.

05. **Eingecheckt ohne Reservierung** — Aktueller Stand: weißer Check-in-Text, kein Ring und zusätzlicher Name am oberen Rand.

06. **Check-in + laufende Buchung** — Aktueller, von dir beanstandeter Zustand: Reservierung überschreibt den Check-in-Text; Namen erscheinen mehrfach.

07. **Check-in wird übernommen** — Zwischenzustand während der Übertragung und Zuordnung.

08. **Verbindung / Daten fehlen** — Kein bestätigter Belegungsstatus; keine grüne Freigabe. Auch veraltete Buchungsdaten werden kenntlich gemacht.

09. **Statusfehler** — Fehlerzustand der Arbeitsplatzzuordnung. Details werden in Home Assistant geprüft.

10. **Licht dimmen** — Drehen im Bedienmodus oder den Ring berühren. Ein-/Aus-Tasten; untere Leiste wechselt die Funktion, obere Symbolleiste die Lampe.

11. **Weitere Lichtseite** — Bis zu vier zugeordnete Lichter mit eigenen Namen und Symbolen. Beispielnamen, nicht die tatsächliche Gerätezuordnung.

12. **Tischhöhe / Favoriten** — Höhenregler 62–128 cm und Sitz-/Steh-Favoriten. Beispiele: 74 und 110 cm.

13. **Menüauswahl per Drehrad** — Grauer Rahmen = Menüauswahl. Drehen wählt die Funktion; Drücken öffnet den Bedienmodus. Erneutes Drücken kehrt zurück.

14. **Rollo / Position** — Positionssteuerung. Die Seite erscheint nur bei zugeordnetem Rollo; ohne Lamellenfähigkeit fehlt deren Steuerung.

15. **Jalousie / Lamellen** — Position und Lamellen getrennt. Per Touch Höhe oder Lamellen als Drehradfunktion auswählen.

16. **Schaltkanal** — Ein und Aus per Touch. Im Bedienmodus: rechts drehen = ein, links drehen = aus. Name und Symbol konfigurierbar.

17. **Check-in-Bestätigung** — Willkommensnachricht mit grünem animiertem Ring; Check-out verwendet dieselbe Meldungsart. Standbild einer Animation.

18. **Check-in abgewiesen** — Belegter oder für eine andere Person reservierter Arbeitsplatz. Roter animierter Ring. Standbild einer Animation.

19. **Reservierung endet bald** — Warnung ab 30 Minuten Restzeit bei eingecheckter Person; roter animierter Ring. Langer Text ist scrollbar.

20. **Push · hohe Priorität** — Priorität 1: rot animiert. Einzel-, Gruppen- und zentrale Nachrichten nutzen dieselbe Oberfläche.

21. **Push · mittlere Priorität** — Priorität 2: gelb animiert; Anzeigedauer konfigurierbar. OK schließt die Nachricht.

22. **Push · normale Priorität** — Priorität 3: ohne Ring. Nach Ablauf oder Bestätigung kehrt die vorige Ansicht zurück.

23. **Standby** — Beispiel einer gedimmten Ansicht. Wartezeit, Helligkeit und Rückkehr zum Check-in-Dashboard sind konfigurierbar.

24. **Display ausgeschaltet** — Display-Aktiv aus: schwarzes Panel. Gewöhnliche Bedienung soll es nicht wieder einschalten.

25. **Geplant: eingecheckt** — Vorgesehene Änderung: GEBUCHT blau, ohne Ring; Mitarbeitername nur einmal, keine Wiederholung oben/unten. Noch nicht aufgespielt.