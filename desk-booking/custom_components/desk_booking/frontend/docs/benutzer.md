# Desk Booking · Benutzerhandbuch

Dieses Handbuch beschreibt die ausgelieferte Version von Desk Booking. Versionsstand und Prüfdatum stehen oben in der HTML-Ausgabe. Eine Reservierung in Microsoft Places und ein Check-in in Home Assistant sind zwei verschiedene Vorgänge.

## 1. Schnellstart

1. Öffne das Home-Assistant-Dashboard mit der Karte „Desk Booking Raumplan“.
2. Prüfe Datum, Uhrzeit und die Anzeige „LIVE“ oder „PLANUNG“.
3. Klicke oder tippe auf einen Arbeitsplatz. Das Feld am Symbol zeigt Status und gegebenenfalls die reservierende oder eingecheckte Person.
4. Für eine neue Buchung wähle „Reservieren“. Der Link öffnet Microsoft Places separat. Dort den gewünschten Arbeitsplatz und Zeitraum auswählen und buchen.
5. Zum Arbeitsbeginn in Home Assistant am Schreibtisch den Mitarbeiter auswählen und „Test-Check-in“ drücken. Der Name der Taste ist historisch; sie führt einen echten lokalen Check-in aus.
6. Bei erfolgreichem Check-in zeigt das zugeordnete Display „EINGECHECKT“ in Blau. Zum Verlassen „Auschecken“ am Schreibtischgerät drücken.

Reservierungen entstehen in Microsoft Places. Der Reservieren-Link bucht selbst nichts und übergibt derzeit weder Schreibtisch noch Datum. Die Integration legt keine persönlichen Home-Assistant-Konten aus Microsoft 365 an.

## 2. Objekte und Zuständigkeiten

| Objekt | Bedeutung |
| --- | --- |
| Mitarbeiter | Aus Microsoft 365 importierte Person mit lokalen Sitz-/Stehhöhen und gegebenenfalls einer NFC-Zuordnung. |
| Schreibtisch | Aus Places importierter Arbeitsplatz; kann mit einem Display, Lichtern, Rollo und Schaltkanal verbunden sein. |
| Raum | Eigenständiger Places-Raum mit aktuellen und folgenden Reservierungen; derzeit ohne Check-in und Zubehörsteuerung. |
| Group | Importierte Microsoft-Gruppe für Nachrichten an die aktuell genutzten Schreibtische ihrer Mitglieder. |
| Desk Booking Zentrale | Gemeinsame Steuerung, Synchronisierung und Statusanzeigen für Administratoren bzw. berechtigte Bediener. |

Neue Mitarbeiter, Schreibtische, Räume und Gruppen werden durch die Synchronisierung angelegt. Eine manuelle Neuanlage in Desk Booking ist nicht vorgesehen. Administratoren pflegen lokale Zuordnungen. Ausgeblendete Objekte erscheinen nicht in den Desk-Booking-Karten.

## 3. Den Raumplan lesen

### Aufbau

Oben stehen die optionalen Überschriften. Im Grundriss liegen die Arbeitsplatzsymbole, oben links die Anzahlen und oben rechts „LIVE“ oder „PLANUNG“. Unten links steht dauerhaft „Reservieren“. Direkt unter dem Bild folgen Legende, Datum, Uhrzeit, Suche mit „Nur frei“ und die Planauswahl. Administratoren sehen zusätzlich die Bearbeitungsfunktionen.

Das Bild passt sich proportional an die Kartenbreite an. Der Bildbereich hat keinen eigenen Scrollbalken. Bei langen Karten kann die Dashboard-Seite normal gescrollt werden.

### Farben und Status

| Farbe | Anzeige | Bedeutung |
| --- | --- | --- |
| Grün | Frei | Am ausgewählten Zeitpunkt keine laufende bzw. in weniger als 60 Minuten beginnende Reservierung und kein angezeigter Live-Check-in. |
| Gelb | Bald reserviert | Nächste Reservierung beginnt in weniger als 60 Minuten. |
| Rot | Reserviert | Reservierung läuft. Mehrere gleichzeitige Reservierungen werden als Buchungskonflikt bezeichnet. |
| Blau | In Benutzung | Schreibtisch ist aktuell in Home Assistant eingecheckt; nur im Live-Modus. |
| Grau | Daten nicht aktuell / nicht verfügbar | Daten fehlen, sind veraltet oder das Objekt ist inaktiv. Daraus darf keine Freigabe abgeleitet werden. |

Die Summen beziehen sich auf sichtbare, im gewählten Plan platzierte Objekte, also gegebenenfalls Schreibtische und Räume gemeinsam. „Reserviert“ zählt gelbe und rote Objekte zusammen. Ein Suchfilter ändert die Summen nicht.

Ein Mitarbeiterfoto erscheint bei einer laufenden/kurz bevorstehenden Reservierung oder einem Live-Check-in. Ohne verfügbares Foto erscheinen Initialen, ohne Person ein Schreibtisch- bzw. Raumsymbol. Ein Foto bei einer Reservierung bestätigt keine tatsächliche Anwesenheit. Räume zeigen den Buchenden, nicht alle Teilnehmenden.

### Informationen und Reservieren

Mit der Maus über dem Symbol erscheinen Informationen. Klick/Touch hält das Feld offen; ein erneuter Klick auf das Symbol, ein Klick außerhalb oder Escape schließt es. Bei einem freien Objekt steht „Reservieren“ direkt in diesem Feld. Der dauerhaft sichtbare Button unten links öffnet Places unabhängig von der ausgewählten Ressource. Beide verwenden denselben zentral konfigurierten Link.

Der Button ist eine Weiterleitung. Freie Anzeige und Button garantieren nicht, dass der Platz in Microsoft Places für den dort gewählten Zeitraum noch frei ist. Microsoft-Anmeldung und Buchungsbestätigung erfolgen dort.

### Datum, Uhrzeit und Suche

- Standard ist heute im Live-Modus. „Jetzt“ kehrt zu aktueller Uhrzeit und Live-Anzeige zurück.
- Pfeile und Datumsfeld wählen heute bis zu 30 Tage im Voraus. Vergangene Tage sind nicht auswählbar.
- Der Uhrzeitregler schaltet auf Planung. Für andere Tage gilt zunächst die in der Karte konfigurierte Startzeit, standardmäßig 09:00.
- Planung zeigt Kalenderreservierungen zum gewählten Zeitpunkt. Sie bildet keine historische tatsächliche Belegung ab. Auch bei Planung für heute wird der aktuelle Check-in nicht als Belegung eingeblendet.
- Suche berücksichtigt Ressourcennamen sowie Namen von Nutzern/Reservierenden. Nicht passende Symbole werden abgeblendet. „Nur frei“ blendet nicht freie Objekte vollständig aus.
- Die Planauswahl wechselt zwischen vorhandenen Grundrissen. Es gelten die Zeitzone und die Datenberechtigungen von Home Assistant.

## 4. Anwesenheitskarte

Die Karte „Desk Booking Anwesenheit“ zeigt je Person ein Foto oder Initialen für den ausgewählten Kalendertag. Ein gelber Rahmen steht für reserviert, ein blauer für aktuell eingecheckt. Ein Administrator kann die Auswahl auf die Ressourcen eines Raumplans begrenzen.

Unter dem Bild steht die Spanne vom frühesten Reservierungsbeginn bis zum spätesten Reservierungsende dieses Tages. Mehrere Buchungen werden zusammengeführt; Pausen sind deshalb in der angezeigten Spanne enthalten. Über Mitternacht reichende Buchungen werden auf den Kalendertag begrenzt. „24:00“ bedeutet Tagesende.

Ohne Reservierung kann heute ein aktueller Check-in als „Seit … eingecheckt“ erscheinen; es wird keine Endzeit erfunden. Bei Räumen zählen nur die Buchenden. Die Karte zeigt geplante Anwesenheit und aktuelle Check-ins, keine garantierte lückenlose Anwesenheitsmessung. Datum und Raumplanfilter gelten für diese Karte selbst; eine Änderung im Raumplan steuert sie nicht automatisch mit.

## 5. Check-in und Check-out

### Bedienung in Home Assistant

Öffne über Geräte & Dienste das virtuelle Schreibtischgerät. Wähle unter „Mitarbeiter für Check-in“ die passende Person und betätige „Test-Check-in“. Die Belegungs- und Mitarbeiterentitäten zeigen den Erfolg. Ein aktives Mitarbeiterprofil, ein aktiver Schreibtisch, aktuelle Kalenderdaten und ein funktionsfähiges zugeordnetes Display sind erforderlich.

Eine hinterlegte NFC-Kennung ist derzeit nur eine lokale Zuordnung. Die Integration enthält keine automatische Verarbeitung von NFC-Scans; ein Scan allein checkt mit diesem Stand niemanden ein. Das Display zeigt den Status, die Check-in-Aktion erfolgt in Home Assistant.

### Welche Check-ins erlaubt sind

| Situation | Verhalten |
| --- | --- |
| Frei, keine geschützte Reservierung | Jede aktive Person darf einchecken, sofern sie nicht bereits an einem anderen Tisch eingecheckt ist. |
| Reservierung läuft oder beginnt in höchstens 60 Minuten | Nur die eindeutig zugeordnete reservierende Person darf einchecken. Unklare Zuordnungen und widersprüchliche Reservierungen sperren den Vorgang. |
| Andere Person bereits eingecheckt | Ein weiterer Check-in wird abgewiesen, solange keine zulässige Übernahme nach Reservierungsende vorliegt. |
| Dieselbe Person erneut | Bestehender Check-in bleibt bestehen. |
| Zum Check-in gehörende Reservierung beendet | Eine andere Person darf grundsätzlich übernehmen, wenn keine geschützte Folgereservierung entgegensteht. |
| Check-in ohne zugeordnete Reservierung | Bleibt bis zum Auschecken oder täglichen Abschluss bestehen; kein automatisches Nutzungsende wird erfunden. |
| Kalender oder Display nicht erreichbar | Neue Check-ins können gesperrt werden. Fehlermeldung lesen und Administrator informieren. Auschecken bleibt als Wiederherstellungsweg verfügbar. |

Die technische Übernahmeregel bedeutet nicht, dass jede Bedienoberfläche bereits einen freien Mitarbeiterwechsel anbietet: Die aktuelle Mitarbeiterauswahl am belegten Schreibtisch ist gesperrt. Für einen Wechsel über diese Oberfläche zuerst auschecken und die nächste Person auswählen.

### Höhen und Auschecken

Beim Check-in werden die persönlichen Sitz-/Steh-Favoriten an das Display übertragen. Der Check-in bewegt den Tisch nicht. Zum tatsächlichen Verstellen die Höhenbedienung am Display verwenden. Beim Auschecken werden die vor der Sitzung vorhandenen Displayfavoriten wiederhergestellt und anschließend die Zuordnung gelöst.

Bei einem Übertragungsfehler versucht die Integration, den vorherigen Zustand wiederherzustellen. Bleibt ein Fehler bestehen, kann der Tisch gesperrt bleiben. Nach Wiederherstellung der Displayverbindung „Auschecken“ erneut versuchen; nicht wahllos Profile oder Geräte löschen.

### Nichtanreise, Endwarnung und Tagesabschluss

- Läuft eine Schreibtischreservierung seit mehr als 30 Minuten, wurde sie noch nie eingecheckt und ist der Tisch frei, kann die Integration diese Reservierung im Ressourcenkalender freigeben. Voraussetzung sind erfolgreiche Prüfung und Schreibberechtigung. Sie greift nicht für Räume.
- Bei eingecheckter Person erscheint in den letzten 30 Minuten der Reservierung eine Warnung: „Achtung, Reservierung endet bald. Bitte nachbuchen, falls benötigt...“. Bei Bedarf in Places verlängern.
- Täglich werden alle eingecheckten Personen zur zentral konfigurierten Zeit abgemeldet, standardmäßig 00:00 in der Home-Assistant-Zeitzone. Das ist ein lokaler Check-out und löscht nicht pauschal Kalenderbuchungen.

## 6. Das Schreibtisch-Display

### Check-in-Dashboard

| Situation | Text und Ring |
| --- | --- |
| Frei, keine nahe Reservierung | „FREI“ grün, statischer grüner Ring. |
| Reservierung in weniger als 60 Minuten | „RESERVIERT“ gelb, statischer gelber Ring. |
| Reservierung hat begonnen, noch kein Check-in | „RESERVIERT“ rot, roter Statusring. |
| Erfolgreich eingecheckt | „EINGECHECKT“ blau, kein farbiger Statusring; gilt auch während laufender Reservierung. |
| Unzulässiger Check-in | „Bereits gebucht...“ mit rotem animiertem Nachrichtenring. |
| Reservierung endet bald | Warnmeldung mit rotem animiertem Nachrichtenring. |
| Übertragung läuft / Fehler | „BITTE WARTEN“ bzw. „BITTE PRUEFEN“. Bei fehlender Verbindung „STATUS OFFEN“. |

Unter zwei Stunden bis zum Beginn wird die aufgerundete Restzeit in Minuten angezeigt, sonst Datum und Uhrzeit. Auf der Check-in-Seite wird der Mitarbeitername nicht zusätzlich oben und unten wiederholt. Nachrichten können die normale Anzeige vorübergehend überdecken. Veraltete Buchungsinformationen werden kenntlich gemacht; ein fehlender Warnring bei Datenfehlern bedeutet keine bestätigte Verfügbarkeit.

### Menü und Gerätebedienung

Wischen oder Tippen auf Menü-Symbole wechselt die Seiten. Im Menü-Auswahlmodus bewegt das Drehrad die Markierung; Drücken öffnet die Seite und aktiviert die Wertsteuerung. Erneutes Drücken kehrt zur Menüauswahl zurück. Nur konfigurierte Zubehörseiten werden angeboten.

| Seite | Bedienung |
| --- | --- |
| Licht | Ein/Aus über die entsprechenden Tasten, Helligkeit über die Wertsteuerung; bei mehreren Lichtern zusätzliche Auswahlleiste. Bis zu vier Lichter. |
| Tischhöhe | Höhe über die vorhandene Steuerung verändern; Sitz-/Steh-Favorit gezielt aufrufen. Der Tisch bewegt sich nur über seine angebundene Steuerung. |
| Rollo/Jalousie | Position steuern; bei unterstützten Jalousien per Touch zwischen Position und Lamellen wechseln. |
| Schaltkanal | Ein/Aus-Tasten; im Bedienmodus Drehen nach rechts ein, nach links aus. |
| Nachrichten | Temporärer Text mit Priorität und Dauer; danach normale Anzeige. |

Standby dimmt nach der eingestellten Wartezeit und kann zur Check-in-Seite zurückkehren. Ein ausdrücklich ausgeschaltetes Display wird durch normale Aktivität nicht automatisch wieder eingeschaltet. Funktionen hängen von der installierten Display-Firmware und den tatsächlichen Gerätezuordnungen ab.

## 7. Persönliche Einstellungen und E-Mails

Sitz- und Stehhöhe liegen am virtuellen Mitarbeitergerät als Zahlenwerte. Bereich 50–140 cm, Schritte 0,5 cm; Sitzhöhe muss kleiner als Stehhöhe sein. Ein Display kann gröbere Schritte und engere Grenzen haben. Außerhalb des zulässigen Displaybereichs wird der Check-in abgewiesen. Änderungen während einer Sitzung werden beim nächsten Check-in übernommen.

Name, E-Mail und Aktivstatus kommen aus Microsoft 365. Sie werden in Home Assistant nicht unabhängig manuell gepflegt. Eine lokale NFC-Zuordnung ändert der Administrator. Zum Bedienen sind die jeweils vergebenen Home-Assistant-Rechte erforderlich.

Wenn vom Administrator aktiviert, erhält die reservierende Person eine E-Mail vor Beginn und eine Erinnerung vor Nichtanreise-Verfall. Nach einem zugeordneten Check-in entfällt die entsprechende Erinnerung. Eine erhaltene E-Mail ersetzt den Check-in nicht. Zeitpunkt und Texte können zentral abweichen. Bei Räumen gibt es keine Nichtanreise-Erinnerung.

## 8. Nachrichten an Arbeitsplätze

Berechtigte Bediener können Nachrichtentext, Priorität und Dauer am Schreibtisch, an einer Gruppe oder an der Zentrale setzen und anschließend senden. Text allein löst keinen Versand aus.

| Priorität | Darstellung |
| --- | --- |
| 1 | Roter animierter Ring. |
| 2 | Gelber animierter Ring. |
| 3 | Kein Nachrichtenring. |

Gruppennachrichten erreichen nur Schreibtische mit aktuell eingecheckten aktiven Gruppenmitgliedern und zugeordnetem Display. Sie gehen nicht automatisch an jedes Display im Gebäude oder an alle Gruppenmitglieder per E-Mail. Die Anzeigedauer beträgt 1–300 Sekunden, Standard 15 Sekunden.

## 9. Häufige Fragen

**Foto fehlt:** Es können Initialen erscheinen, wenn kein M365-Foto existiert oder die Berechtigung/Verbindung fehlt.

**Platz fehlt im Plan:** Er ist möglicherweise nicht platziert, ausgeblendet, inaktiv oder für deinen HA-Zugriff nicht sichtbar. Planauswahl und Filter prüfen.

**Places-Buchung erscheint noch nicht:** Der Kalenderabruf läuft standardmäßig alle fünf Minuten. Ein Administrator kann „Buchungen aktualisieren“ auslösen. Eine lokale Kartenaktualisierung allein liest nicht sofort alle Microsoft-Kalender neu.

**Reserviert, obwohl ich eingecheckt habe:** Erst einen bestätigten lokalen Check-in prüfen. Danach muss das Display „EINGECHECKT“ zeigen; bei Abweichung den Administrator um Prüfung von Displayzuordnung, Firmware und Verbindung bitten.

**Nachts automatisch ausgecheckt:** Das ist der zentrale Tagesabschluss. Am nächsten Arbeitstag erneut einchecken.

**Auschecken schlägt fehl:** Displayverbindung wiederherstellen und erneut versuchen. Belegung nicht durch Löschen des Geräts bereinigen.

## 10. Grenzen dieses Standes

Räume haben keine Check-in- oder Zubehörfunktionen. Es gibt keine M365-SSO-Benutzerverwaltung für Home Assistant, keinen fertigen NFC-Scan-Ablauf und noch keine Power-BI-Auswertung oder umfassende historische Anwesenheitsdatenbank. Die Handbücher beschreiben vorhandene Funktionen; frühere Entwürfe sind keine Funktionszusage.
