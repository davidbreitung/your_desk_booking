# Desk Booking · Administratorhandbuch

Desk Booking ist eine Home-Assistant-Custom-Integration mit Microsoft-Graph-App-Anmeldung, Places-Ressourcen, lokalen Arbeitsplatzzuordnungen und zwei Dashboard-Karten. Dieses Handbuch beschreibt den ausgelieferten Code. Es dokumentiert Vorgaben und Verhalten, keine Momentaufnahme individueller Produktivdaten. Aktuelle Version und Prüfdatum stehen oben in der HTML-Ausgabe.

## 1. Architektur und Zuständigkeiten

| Datenbereich | Führendes System | Verhalten |
| --- | --- | --- |
| Mitarbeiteridentität, Name, Mail, Aktivstatus | M365 / Entra ID | Import aktiver interner Benutzer, Änderungen und Deaktivierungen werden übernommen. Keine manuelle Mitarbeiteranlage. |
| Gruppen und direkte Mitgliedschaften | M365 / Entra ID | Alle von Graph gelieferten unterstützten Gruppen; nicht auf Sicherheitsgruppen begrenzt. Verschachtelungen werden beim Nachrichtenrouting ausgewertet. |
| Schreibtische und Räume | Microsoft Places | Ressourcen als getrennte lokale Gerätetypen; neue Ressourcen beim Folgesync importieren. Identität über IDs, nicht Anzeigenamen. |
| Reservierungen | Exchange-Ressourcenkalender | Zeiten und Organisator aus Graph; kein lokaler Buchungseditor. |
| NFC-Zuordnung, Sitz-/Stehhöhen, Zubehör und Display | Home Assistant | Lokal speichern, bei Synchronisierung erhalten. NFC-Zuordnung allein verarbeitet keine Scans. |
| Check-in, Displaywarnungen, Tagesabschluss | Home Assistant | Lokale Steuerung; keine native Places-Check-in-Rückmeldung mit dieser App-Authentifizierung. |
| Grundrisse und Positionen | Home Assistant | Zentral für Karten speichern; Anzeigeoptionen wie Überschriften zusätzlich pro Karte. |

Ein Integrationseintrag pro HA-Instanz. Mitarbeiter benötigen kein automatisch erzeugtes HA-Konto. Geräte werden unter den Kategorien Mitarbeiter, Group, Schreibtische und Räume organisiert; die Zentrale bleibt separat. Die Geräteansicht ist von Sichtbarkeitsfiltern der Desk-Booking-Karten zu unterscheiden.

Bei einer Ressource mit gleichem Namen nach Löschen/Neuanlage entscheidet die neue Places-/Entra-ID, nicht der Name. Das frühere Objekt kann inaktiv erhalten bleiben. Unklare Ressourcen-/Benutzerzuordnungen werden nicht anhand ähnlicher Namen zusammengeführt.

## 2. Voraussetzungen und Installation

Die Implementierung wurde auf Home Assistant Core 2026.11.1 und der projektspezifischen ESPHome-Display-Firmware entwickelt. Eine beliebige ältere HA-Version oder ein beliebiges Display ist damit nicht automatisch kompatibel. Internetzugriff auf Microsoft-Anmeldung und Graph ist erforderlich; bei Ausfällen bleiben lokale Daten erhalten.

1. Vor einem Update die vorhandenen Integrationsdateien und relevante HA-Konfiguration sichern; bei Firmwareänderung zusätzlich die Displaykonfiguration.
2. Das geprüfte Paket nach `/config/custom_components/desk_booking` installieren. Der gesamte Ordner einschließlich `frontend/docs` und `translations` gehört zur Integration.
3. Bei Backendänderungen Home Assistant neu starten und Konfigurations-/Laufzeitprüfung durchführen. Reine Frontendänderungen benötigen in der Regel nur die neue Dashboard-Ressourcen-URL und Neuladen des Browsers.
4. Neue Einrichtung: Einstellungen → Geräte & Dienste → Integration hinzufügen → Desk Booking.
5. Bestehende Einrichtung: Desk Booking → Konfigurieren. Es wird keine zweite M365-Integration angelegt.
6. Verbindung und Sync-Status prüfen, anschließend lokale Display-/Zubehörzuordnungen kontrollieren.

Alte Build-Generatoren können frühere Metadaten überschreiben. Für neue Pakete ausschließlich den aktuellen `package_m365.py` und die Dokumentationsprüfung verwenden. `.storage`-Dateien nicht manuell bearbeiten.

## 3. Entra-App einrichten

### Die drei Zugangswerte

Im [Microsoft Entra Admin Center](https://entra.microsoft.com/) unter App-Registrierungen eine App für den eigenen einzelnen Mandanten registrieren. Für den Client-Credentials-Ablauf ist kein interaktiver Redirect zur Integration vorgesehen.

| Feld in Desk Booking | Herkunft |
| --- | --- |
| Tenant-ID | Verzeichnis-/Mandanten-ID auf der App-Übersichtsseite. |
| Client-ID | Anwendungs-/Client-ID der App, nicht die Objekt-ID der App-Registrierung. |
| Client-Secret | Zertifikate & Geheimnisse → geheimer Clientschlüssel. Den Wert kopieren, nicht die geheime ID. Der Wert ist nach Verlassen der Ansicht nicht erneut sichtbar. |

Zugangsdaten nicht in Handbücher, Screenshots oder Supportmeldungen übernehmen. Ablaufdatum und Verantwortlichkeit für die Erneuerung festhalten. In einer bestehenden Einrichtung erhält ein leeres Secret-Feld den bisherigen Wert; zum Ersetzen einen gültigen neuen Wert eingeben. Ein Mandantenwechsel wird zum Schutz vorhandener Identitäten abgewiesen.

### Anwendungsberechtigungen und Zustimmung

API-Berechtigungen → Berechtigung hinzufügen → Microsoft Graph → **Anwendungsberechtigungen**. Delegierte Berechtigungen sind für die hier verwendete unbeaufsichtigte App-Anmeldung nicht ausreichend. Anschließend ein berechtigter Administrator: „Administratorzustimmung für … erteilen“. Nach jeder Berechtigungserweiterung erneut Zustimmung und tatsächlichen Zugriff prüfen.

| Berechtigung | Verwendung in Desk Booking |
| --- | --- |
| `User.Read.All` | Benutzerstammdaten, stabile Objekt-IDs und Benutzer-Delta; vorhandene App-Berechtigung wird auch für Benutzerfotos genutzt. |
| `GroupMember.Read.All` | Gruppen, direkte Mitgliedschaften und Gruppen-Delta gemäß bestehender App-Konfiguration. |
| `Place.Read.All` | Places-Schreibtische, Räume und Workspaces. Singular „Place“. |
| `Calendars.ReadBasic.All` | In bisherigen Einrichtungen verwendete App-Berechtigung für lesenden Kalenderzugriff. Die aktuelle Graph-Dokumentation führt bei calendarView `Calendars.ReadBasic`; im Tenant verfügbare Bezeichnung und tatsächlich erteilte App-Rolle prüfen. |
| `Calendars.ReadWrite` | Für die implementierte Nichtanreise-Freigabe durch Löschen des konkreten Termins im Ressourcenkalender. Umfasst auch Lesen. |
| `Mail.Send` | Nur erforderlich, wenn Erinnerungen, Testmail oder die Mail-Aktion genutzt werden sollen. |

Verdeckte Gruppenmitgliedschaften können zusätzliche Microsoft-Berechtigungen erfordern; sie sind nicht als uneingeschränkt unterstützt zugesagt. Nicht pauschal zusätzliche Schreibrechte für Benutzer, Gruppen oder Places vergeben.

Die Verbindungskontrolle prüft Benutzer-/Gruppen-Delta und Places-Abfragen. Sie ersetzt keinen erfolgreichen Kalender- oder Mailtest. Insbesondere nach einem 403 die betroffene Funktion und deren App-Rolle getrennt prüfen. [Benutzer-Delta](https://learn.microsoft.com/en-us/graph/api/user-delta?view=graph-rest-1.0), [Gruppen-Delta](https://learn.microsoft.com/en-us/graph/api/group-delta?view=graph-rest-1.0), [Places lesen](https://learn.microsoft.com/en-us/graph/api/place-list?view=graph-rest-1.0).

### Exchange-Zugriff begrenzen

Ein Exchange-Administrator sollte Kalenderzugriff auf die erforderlichen Ressourcen und Mailversand auf das vorgesehene Absenderpostfach begrenzen. Die zentrale Absenderadresse ist keine Berechtigungsgrenze. Exchange Application RBAC und Entra-App-Rechte können unabhängig/additiv wirken; eine eingeschränkte RBAC-Zuweisung beschränkt nicht automatisch eine gleichzeitig uneingeschränkt erteilte Entra-Berechtigung. Die wirksamen Rechte daher testen. Die aktuelle Freigabelogik prüft zusätzlich die `Calendars.ReadWrite`-App-Rolle im Token; reine RBAC-Zuweisungen ohne diese Rolle sind für diese Funktion nicht als unterstützt zugesagt. [Microsoft: Application RBAC](https://learn.microsoft.com/en-us/exchange/permissions-exo/application-rbac).

## 4. Alle zentralen Konfigurationsbereiche

Öffnen: Einstellungen → Geräte & Dienste → Desk Booking → Konfigurieren. Änderungen über die Dialoge speichern; nicht durch direkte Bearbeitung interner HA-Dateien.

### Display

| Einstellung | Standard | Zulässiger Bereich / Wirkung |
| --- | --- | --- |
| Firmenname | your-admins | Bis 60 Zeichen, keine Steuerzeichen; Anzeige auf zugeordneten Displays. |
| Normale Helligkeit | 50 % | 1–100 %. |
| Standby-Helligkeit | 10 % | 0–100 %. |
| Standby-Wartezeit | 120 s | 0–3600 s; 0 deaktiviert Standby. |
| Rückkehr zur Check-in-Seite | Aus | Bei Standby zur Check-in-Seite wechseln. |

Vorgaben werden bei Wiederverbindung erneut angewendet. Helligkeitsänderungen schalten ein ausdrücklich ausgeschaltetes Display nicht wieder ein. Einzelne Geräte bleiben über ihre ESPHome-Entitäten steuerbar.

### Microsoft 365

Tenant-ID, Client-ID und Secret wie oben; Sync-Intervall standardmäßig 15 Minuten, 5–1440 Minuten. Ein leer gelassenes bestehendes Secret bleibt erhalten. Der Dialog prüft die Verbindung vor dem Speichern. Benutzer und Gruppen verwenden Delta-Abfragen; Places wird vollständig mit Seitenverfolgung abgefragt. Abgelaufene Delta-Cursor führen zur erneuten vollständigen Einlesung, nicht zur vorschnellen Löschung lokaler Objekte.

Aktive interne Benutzer werden übernommen; Gäste und erkannte Ressourcenkonten sind keine Mitarbeiter. Deaktivierte/gelöschte Personen werden lokal inaktiv. Stammdaten können nicht lokal gegen Microsoft überschrieben werden. Der noch vorhandene Mitarbeiter-Aktiv-Schalter zeigt den synchronisierten Zustand; manuelles Umschalten wird abgewiesen.

### Buchungen

| Einstellung | Standard | Wirkung |
| --- | --- | --- |
| Abrufintervall | 5 min | 1–1440 Minuten; getrennt vom Verzeichnissync. |
| Tägliches Auschecken | 00:00 | Format HH:MM, lokale HA-Zeitzone. |

Der Abruf liest vom Beginn des heutigen lokalen Tages bis ungefähr 365 Tage voraus. Serienvorkommen und Ausnahmen werden über calendarView gelesen. Stornierte, freie oder abgelehnte Termine zählen nicht als Reservierung. Laufende und zukünftige Buchungen werden unterschieden. Die Karten erlauben bewusst nur heute bis 30 Tage voraus.

Der Organisator wird zuerst über UPN und dann eindeutige Mail-/SMTP-Aliasse einem Entra-Objekt zugeordnet; gespeichert/verknüpft wird die stabile Identität im Mandanten. Mehrdeutige/fehlende Zuordnungen bleiben unbekannt und sperren geschützte Check-ins. Die Mailadresse allein ist kein dauerhafter Primärschlüssel.

Der lokale Cache bleibt bei Fehlern erhalten. Angaben `data_current`, `last_success`, `error` und `search_until` an Buchungsentitäten ermöglichen die Bewertung. Die Aktualitätsgrenze liegt bei mindestens 15 Minuten bzw. abhängig vom Abrufintervall; ein Abruffehler markiert Daten unabhängig davon als nicht aktuell. Ein neuer Check-in führt zusätzlich einen frischen Kalenderabruf aus.

Der Tagesabschluss wird etwa alle 30 Sekunden geprüft. Fehlgeschlagene Abmeldungen werden mit Bezug auf die ursprünglich eingecheckte Person erneut versucht. Eine inzwischen andere Person wird dadurch nicht abgemeldet. Beim ersten Start und nach Änderung der Abschlusszeit wird kein vergangener Abschluss unmittelbar rückwirkend ausgeführt; nach späteren Ausfällen wird ein verpasster Abschluss nachgeholt.

### Schreibtisch bearbeiten

Zuerst einen synchronisierten sichtbaren Schreibtisch wählen. Die Auswahl zeigt bei Bedarf eine kurze lokale Kennung zur Unterscheidung gleicher Namen.

| Feldgruppe | Beschreibung |
| --- | --- |
| Name | Lokaler Tischname, Pflichtfeld, maximal 60 Zeichen; Microsoft-Stammdaten können beim Sync erneut maßgeblich werden. |
| Display-Gerät | ESPHome-Gerät mit den erwarteten Favoritenentitäten. Bei Places-Desks optional; für Check-in erforderlich. Ein Display darf nur einem Tisch zugeordnet sein. |
| Anzeigename | Displaybeschriftung; leer übernimmt den Tischnamen. |
| Licht 1–4 | Je Licht Entität, optionaler Name und Symbol. Nur geeignete dimmbare Lichter, keine doppelte Zuordnung im Tisch und keine ungeeignete Display-eigene Steuerung. |
| Rollo/Jalousie | Cover-Entität mit Positionssteuerung, optionaler Anzeigename. Lamellen nur bei unterstütztem Cover. |
| Schaltkanal | Externe Switch-Entität, optionaler Name und Symbol; nicht die Display-eigene interne Schaltfunktion. |

Lichtsymbole: Glühbirne, Deckenspot, LED-Band, Deckenleuchte, Stehlampe, Schreibtischlampe. Schaltsymbole: Ein/Aus, Steckdose, Ventilator, Monitor, Heizung, Schalter. Nicht zugeordnete Funktionen werden im Displaymenü ausgelassen. Vor Displaywechsel immer auschecken. Namen haben höchstens 60 Zeichen; leere Zubehörnamen verwenden den Entitätsnamen.

Die Integration schreibt beim Check-in nur Sitz-/Steh-Favoriten und löst keine Motorfahrt aus. Favoriten müssen innerhalb der jeweiligen Displaygrenzen liegen. Bei Übertragungsfehlern gibt es Wiederherstellung und einen gesperrten Fehlerzustand; nach Behebung auschecken. Beim Neustart werden Licht-, Cover-, Schalt- und Nachrichtenbefehle nicht pauschal erneut abgespielt.

### Mitarbeiter bearbeiten

Hier wird die optionale lokale NFC-Tag-ID gepflegt. Leeres Feld entfernt die Zuordnung. Maximal 255 Zeichen, keine Steuerzeichen, eindeutige Zuordnung auch gegenüber inaktiven Profilen. Groß-/Kleinschreibung beachten. Die Integration lauscht derzeit nicht auf `tag_scanned` und enthält keinen fertigen NFC-Leser-Ablauf.

Sitz-/Stehhöhen am Mitarbeitergerät: 50–140 cm, Schritt 0,5 cm, Sitzhöhe kleiner als Stehhöhe; Standardwerte 72/110 cm. Bei Übertragung gelten zusätzlich Bereich und Schrittweite des Displays. Anpassungen während einer Sitzung werden erst beim nächsten Check-in wirksam.

### Objekte verwalten

- Sichtbare Objekte auswählen und ausblenden; ausgeblendete Elemente anzeigen und wieder einblenden. Das gilt global für Desk-Booking-Karten und eigene Auswahllisten, einschließlich Räume.
- Die native HA-Geräte-/Integrationsübersicht bleibt sichtbar; sie bietet hier keinen integrierten Filter nach dem lokalen Hidden-Merkmal. Ausblenden ist keine Zugriffssperre und beendet keine laufende Sitzung oder Synchronisierung.
- Dauerhaft löschen ist nur für inaktive, freie Objekte erlaubt, die nicht als aktueller Mitarbeiter einer Sitzung referenziert sind. Es gibt eine separate Bestätigung.
- Lokales Löschen entfernt Datensatz, Entitäten/Gerät, Planpositionen, betroffene Fotos, Kalendercache und Versandhistorie. Recorder-Purge der betroffenen Entitäten wird angefordert. Es löscht keine Microsoft-Objekte und keine Sicherungen. Die tatsächliche Recorder-Verfügbarkeit und vorhandene Backups berücksichtigen.
- Ein noch in Microsoft vorhandenes und später wieder aktives Objekt kann erneut importiert werden. Gleiche Anzeigenamen sind kein Grund, einen aktiven Datensatz zu löschen.

### Raumplan · zentrale Einstellungen

| Feld | Wirkung |
| --- | --- |
| Reservierungs-URL | HTTPS-Adresse, maximal 2048 Zeichen, keine eingebetteten Zugangsdaten. Alle Reservieren-Links verwenden sie und öffnen ein separates Fenster/Tab. |
| Neues Kennwort | Optional, höchstens 256 Zeichen. Geschütztes Öffnen von „Plan bearbeiten“, „+ Plan“ und erster Plananlage. Leeres Feld behält ein vorhandenes Kennwort. |
| Kennwort entfernen | Entfernt den Schutz ausdrücklich. Ohne Kennwort wird keine Abfrage angezeigt. |

Die öffentliche Referenz verwendet eine neutrale Places-Startadresse. Vor der Nutzung den eigenen Gebäude- oder Buchungslink zentral eintragen. Er wählt derzeit keinen einzelnen Schreibtisch, Raum oder Tag vor. Das Benutzerhandbuch enthält absichtlich keine produktiven Gebäude-IDs.

Bearbeitung erfordert weiterhin HA-Administratorrechte. Das Kennwort erweitert keine Benutzerrechte. Server speichert nur einen gesalzenen PBKDF2-SHA256-Hash und prüft auch das Speichern. Freigaben sind an Benutzer und Kennworthash gebunden, eine Stunde gültig und nach erfolgreichem Speichern verbraucht. Nach fünf Versuchen pro Minute warten; neues Kennwort, Reload oder Neustart können eine neue Freigabe erfordern. Keine Freigabe wird dauerhaft im Browser gespeichert.

### E-Mail

| Einstellung | Standard / Grenzen |
| --- | --- |
| Absender | Konfigurierbares Exchange-Postfach; Mail.Send und tatsächliche Postfachfreigabe erforderlich. |
| Dashboard-Link | Optional; HTTP(S), sonst leer. Wird als Text in Vorlagen eingesetzt. |
| Vor Beginn aktiv | Standard Aus, getrennt von Verfall-Erinnerung. |
| Minuten vor Beginn | Standard 15; 1–1440 Minuten. |
| Vor Verfall aktiv | Standard Aus, nur für Schreibtische ohne zugeordnete Teilnahme. |
| Minuten vor Verfall | Standard 5; 1–29 Minuten vor Beginn + 30 Minuten. |
| Betreff je Erinnerung | Pflichttext, maximal 255 Zeichen, keine Zeilenumbrüche. |
| Inhalt je Erinnerung | Pflichttext, maximal 10.000 Zeichen, Klartext. |

Standard bedeutet Auslieferungsvorgabe, nicht aktuelle Schalterstellung einer bestehenden Installation. Gespeicherte Einstellungen bleiben maßgeblich.

Der Menüpunkt Berechtigungen erläutert Mail.Send und Postfachbegrenzung. Platzhalter-Hilfe listet alle Variablen. Vorschau/Test erzeugt Beispielwerte; erst ausdrücklich aktivierter Testversand sendet an die eingegebene Adresse. Die Vorschau ist kein produktiver Reservierungstest.

| Platzhalter | Inhalt |
| --- | --- |
| `{mitarbeiter}` | Eindeutig zugeordneter Mitarbeitername. |
| `{ressource}` | Schreibtisch- oder Raumname. |
| `{beginn}` | Reservierungsbeginn in HA-Zeitzone, TT.MM.JJJJ HH:MM. |
| `{ende}` | Reservierungsende in gleicher Form. |
| `{verfallzeit}` | Beginn plus 30 Minuten; nur für Schreibtische fachlich relevant. |
| `{dashboard_link}` | Zentral hinterlegter Link, sonst leer. |

Literale geschweifte Klammern als `{{` und `}}`. Andere Variablen, Konvertierungen und Formatprogramme sind nicht zulässig. Reservierungsbeginn-Erinnerung gilt für Schreibtische und Räume; Verfall-Erinnerung nicht für Räume. Zugeordnete Teilnahme/Check-in unterdrückt Erinnerungen. Vor Versand wird der Termin erneut geprüft; stornierte oder geänderte alte Cache-Ereignisse lösen keine unpassende Erinnerung aus.

Versandversuche werden vor dem POST gespeichert. Bei unklarem Ergebnis erfolgt keine blinde Wiederholung, damit keine doppelten Nachrichten entstehen. Microsoft 202 heißt angenommen, nicht zugestellt; Zustellung gegebenenfalls im Exchange-Postfach/Nachrichtenablauf prüfen. Der Versand funktioniert nicht während eines HA-Ausfalls; es gibt keinen zugesagten nachträglichen Massenversand verpasster Erinnerungen. [Graph sendMail](https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0).

### Handbücher

Der Menüpunkt verlinkt Benutzer- und Administratorhandbuch sowie die Markdown-Quellen. Die Links öffnen ein separates Browserfenster/Tab, damit Home Assistant die Hilfeseiten nicht als Dashboard-Navigation behandelt. Es wird immer die mit der installierten Version ausgelieferte Fassung geöffnet. Die HTML-Ausgaben sind suchbar und druckbar; über den Browser kann „Als PDF speichern“ genutzt werden. Sie enthalten allgemeine Anleitungen, keine gespeicherten Produktivwerte. Die statische Hilfe besitzt keine zusätzliche Administrator-Anmeldeschranke; die Fähigkeit, Einstellungen zu verändern, bleibt durch Home Assistant geschützt.

## 5. Buchungsschutz und automatische Freigabe

Laufende oder in höchstens 60 Minuten beginnende Buchungen schützen den Schreibtisch für den eindeutig zugeordneten Mitarbeiter. Ein aktiver Mitarbeiter darf nicht gleichzeitig an zwei Schreibtischen eingecheckt sein. Bei Kalenderfehlern werden neue Check-ins gesperrt; Auschecken bleibt als Wiederherstellungsaktion vorhanden.

Ein belegter Arbeitsplatz bleibt grundsätzlich geschützt. Nach Ende der zum Check-in gehörenden Reservierung ist eine Übernahme möglich, sofern keine geschützte Folgereservierung dagegensteht. Die aktuelle HA-Mitarbeiterauswahl sperrt aber einen Wechsel am belegten Tisch; bei Bedienung über diese Auswahl zunächst auschecken. Check-ins ohne zugeordnete Reservierung enden nicht durch einen erfundenen Kalenderzeitpunkt.

Bei mehr als 30 Minuten Nichtanreise löscht die Automatik ausschließlich den geprüften Termin im betreffenden Schreibtisch-Ressourcenkalender, wenn der Tisch frei, das Ereignis noch laufend und niemals als besucht markiert ist. Vor DELETE: frischer Termin, unveränderte Version/ETag, keine Serienmaster. Ein zwischenzeitlicher Check-in verhindert Freigabe. Organisatorkalender und Places-Objekt werden nicht gezielt gelöscht. Räume sind von dieser Automatik ausgenommen. Bei fehlenden Rechten oder Fehlern ist die Freigabe nicht garantiert; Sensoren/Protokoll prüfen.

Endwarnungen erfolgen einmal pro Ereignis/Endzeit in den letzten 30 Minuten bei zugeordnetem Check-in. Eine Verlängerung wird berücksichtigt. Reservierungsschutz bis 60 Minuten und Nichtanreise-Frist von 30 Minuten sind derzeit feste Regeln; sie sind keine frei einstellbaren Optionen.

Native Places-Check-in-Pflicht/Auto-Release muss organisatorisch mit dem HA-Ablauf abgestimmt sein. HA meldet seinen lokalen Check-in nicht an Places zurück. Microsoft unterstützt die hier relevante Check-in-API aktuell nicht mit Application Permissions. Diese Integration schaltet Microsoft-Richtlinien nicht automatisch ab. [Microsoft Check-in-API](https://learn.microsoft.com/en-us/graph/api/place-post-checkins?view=graph-rest-1.0).

## 6. Dashboard-Karten und Grundrissverwaltung

### Ressource und Karten

Die JavaScript-Ressource liegt unter `/desk_booking_static/desk-booking-floorplan.js?v=VERSION` und wird als Modul registriert. Sie lädt auch die Anwesenheitskarte. Bei Updates Versionsparameter aktualisieren und Browser neu laden. Eine fehlende Registrierung kann „Custom element doesn't exist“ verursachen. Bestehende Ressourcen aktualisieren, keine Duplikate anlegen.

| Raumplan-Konfiguration | Vorgabe / Wirkung |
| --- | --- |
| `type` | `custom:desk-booking-floorplan`. |
| `title` | Raumplan; große Überschrift. |
| `eyebrow` | DESK BOOKING; kleine Überschrift. |
| `show_title` / `show_eyebrow` | Standard true, unabhängig ausblendbar. |
| `plan_id` | Optional, sonst erster verfügbarer Plan; Auswahl im Karteneditor. |
| `default_time` | Standard 09:00, Format HH:MM; Startzeit bei Tageswechsel. |

| Anwesenheits-Konfiguration | Vorgabe / Wirkung |
| --- | --- |
| `type` | `custom:desk-booking-attendance`. |
| `title` | Standard Anwesenheit. |
| `plan_id` | Optionaler Filter auf die Ressourcen eines Grundrisses; sonst alle sichtbaren Ressourcen. |

Die beiden Karten führen ihre Datumsauswahl unabhängig. Die Anwesenheitskarte aggregiert je Kalendertag frühesten Beginn/spätestes Ende, nicht die Summe gebuchter Minuten. Sie ist keine Auslastungsstatistik. Bei Räumen nur Buchende, keine Teilnehmerliste.

### Plan anlegen und bearbeiten

„+ Plan“ oder „Plan bearbeiten“ wählen, gegebenenfalls Kennwort eingeben. Planname, Grundrissbild und Symbole bearbeiten und explizit speichern. „Abbrechen“ verwirft den Entwurf. Kartenbearbeitung im HA-Dashboard und die zentrale Grundrissbearbeitung sind getrennte Vorgänge.

| Einstellung / Bedienung | Grenzen |
| --- | --- |
| Pläne | Höchstens 20, Planname maximal 80 Zeichen. |
| Bild | PNG, JPEG oder WebP, Auswahl bis 20 MB; Browser verkleinert auf längste Kante 2400 px und wandelt in WebP. Gespeicherte Bilddaten maximal 4 MB. Seitenverhältnis 1:5 bis 5:1. SVG und externe Bildadressen werden nicht gespeichert. |
| Platzieren | Palette klicken oder Symbol auf das Bild ziehen; maximal 200 Ressourcen je Plan, jede Ressource darin einmal. |
| Position | Prozentwerte im Bild, Anker obere linke Objektecke. Bei älteren Plänen Umrechnung beim Bearbeiten, dauerhaft erst beim Speichern. |
| Raster | 2-Prozent-Schritte beim Ziehen; Pfeiltasten 1 Prozent, mit Umschalt 5 Prozent. |
| Einzelgröße | 16–140 vor zusätzlicher Gesamtskalierung. |
| Drehung | 0–359 Grad. |
| Alle Objekte | 25–150 %, Vorgabe 100 %. |
| Deckkraft | 20–100 %, Vorgabe 100 %. |
| Weiße Hintergründe | An/Aus für Symbol- und Textflächen, verändert nicht die Bilddatei. |
| Vom Plan entfernen | Entfernt nur Position, nicht Microsoft-Ressource oder lokales Gerät. |

Das Bild wird automatisch proportional eingepasst; seit 0.14.1 gibt es keinen eigenen Zoom-/Bildscrollbereich. Veraltete Dokumentationen zum manuellen 25–300-%-Zoom gelten nicht mehr. Statuszahlen beziehen sich auf platzierte sichtbare Ressourcen; Filter ändern die Summen nicht. Bei paralleler Bearbeitung verhindert die Revisionsprüfung ein stilles Überschreiben; abbrechen und neu öffnen.

## 7. Geräte, Entitäten und Aktionen

Die tatsächlichen Entity-IDs vergibt Home Assistant anhand von Namen und bestehenden Registrierungen. In Automationen die vorhandenen IDs auswählen; keine IDs aus einem Beispiel unverändert voraussetzen.

| Gerätetyp | Entitäten / Aufgaben |
| --- | --- |
| Zentrale | Alle Displays, Helligkeit, Nachricht Text/Priorität/Anzeigedauer/Senden, Alle Mitarbeiter abmelden, M365 synchronisieren, Buchungen aktualisieren, Status Verzeichnis/Buchungen/Tagesabschluss/E-Mail. |
| Mitarbeiter | Sitzhöhe, Stehhöhe, M365-Status, synchronisierter Aktivstatus, E-Mail-Adresse. |
| Schreibtisch | Belegung, angemeldeter Mitarbeiter, Mitarbeiterauswahl, Test-Check-in, Auschecken, nächste Buchung, gebucht durch, E-Mail und Nachricht Text/Priorität/Dauer/Senden. |
| Raum | Raumstatus, aktuelle Buchung/aktuell gebucht durch, nächste Buchung/gebucht durch, E-Mail; keine Check-in- oder Zubehörentitäten. |
| Group | Gruppenstatus und direkte Mitgliederanzahl, E-Mail, Nachricht Text/Priorität/Dauer/Senden. |

Belegung verwendet `free`, `applying`, `checked_in`, `error`; Reservierung ist ein zusätzlicher Kalenderzustand, kein weiterer Belegungswert. Buchungsattribute enthalten Ende, aktive Reservierung, Organisatorzuordnung, Mitarbeiter-Geräte-/Entitätslink, Restminuten, Datenaktualität und Fehler. E-Mail-Adressen können fehlen und werden dann nicht erfunden. Display-Diagnose zu CPU/Speicher/Flash stammt aus ESPHome, nicht aus einer zusätzlichen zentralen Messfunktion.

| Aktion | Felder / Wirkung |
| --- | --- |
| `desk_booking.sync_m365` | Verzeichnis, Gruppen, Mitgliedschaften und Places jetzt synchronisieren. |
| `desk_booking.sync_bookings` | Reservierungen der Schreibtische und Räume neu abrufen. |
| `desk_booking.checkout_all` | Alle belegten Tische lokal abmelden; Favoriten wiederherstellen, Teilausfälle melden. |
| `desk_booking.notify_all` | `message`, `priority` 1/2/3, `duration` 1–300 s; Standard Priorität 3, Dauer 15 s. |
| `desk_booking.send_email` | `recipient`, `subject`, `message`; Klartext über zentralen Absender. Administratoren und lokale Automationen, kein allgemeiner anonymer Mail-Endpunkt. |

Nachrichtenpriorität 1 rot animiert, 2 gelb animiert, 3 ohne Ring. Text maximal 255 Zeichen. Gruppe: aktive direkte/verschachtelte Mitglieder mit aktuellem Check-in und zugeordnetem Display; Zyklen abgesichert, Displays dedupliziert. Gruppenimport selbst versendet nichts. Ein Geräteausfall stoppt nicht automatisch den Versand an andere; Teilausfälle beachten.

## 8. Display-Firmware betreiben

Die Integration erwartet die projektspezifischen ESPHome-Entitäten, insbesondere Favorit Sitzen/Stehen, Display Aktiv und die vorgesehenen Nachrichten-/Buchungsschnittstellen. Ein Gerät nur nach Prüfung dieser Endpunkte zuordnen. Wechsel nicht während einer Sitzung durchführen. Benutzerbedienung und Farbzustände beschreibt das Benutzerhandbuch.

Buchungsinformationen werden ungefähr alle 30 Sekunden zum Display übertragen. Nach länger ausbleibendem Empfang, derzeit etwa 90 Sekunden, entfernt die Firmware veraltete Warnhinweise und kennzeichnet die Daten. Ein Warnungs-Overlay hat Vorrang vor normalem Status. EINGECHECKT blau ohne Ring erfordert den passenden Firmwarestand; allein ein Python-Update aktualisiert keine Firmware.

Firmware vor Änderung sichern, Konfiguration validieren, für die tatsächliche Hardware und Partitionierung kompilieren, OTA-Erfolg und erneute Verbindung prüfen. Niemals produktive WLAN-/API-/OTA-Zugangsdaten in veröffentlichte Beispieldateien kopieren. Die vorhandenen redigierten Projektdateien dokumentieren den Stand, sind kein universelles Flash-Abbild für beliebige Displays.

## 9. Fehler suchen und Betrieb überwachen

| Symptom / Code | Vorgehen |
| --- | --- |
| `invalid_auth` | Tenant-/Client-ID, Secret-Wert statt ID, Ablaufdatum und erneute Zustimmung prüfen. Secret nicht in Logs ausgeben. |
| `insufficient_permissions` | Tatsächlich betroffene Graph-Funktion, App-Rolle, Administratorzustimmung und Exchange-Scope prüfen. Verbindungstest allein deckt nicht jede Funktion ab. |
| `cannot_connect` | Internet/DNS/Microsoft-Erreichbarkeit prüfen; lokalen Cache nicht löschen. |
| `rate_limited` | Retry-After beachten; nicht wiederholt manuell synchronisieren. |
| `delta_expired` | Vollabgleich wird erforderlich; Status bis zum erfolgreichen Abschluss prüfen. |
| `ambiguous_place_identity` / unbekannter Buchender | Objekt-/Ressourcen-ID, Mailbox und eindeutige UPN/Aliasse prüfen; nicht nach Namen zusammenführen. |
| Buchungen nicht aktuell | Kalenderstatus, letzte erfolgreiche Abfrage und Mailbox pro Ressource prüfen; manuellen Buchungssync einmal auslösen. |
| Tabelle/Plan speichert nicht | Adminrechte, Kennwortfreigabe, Bild-/Objektgrenzen und Revisionskonflikt prüfen. Keine alten Entwürfe blind wiederholen. |
| Check-in bleibt `error` | Displayverbindung und Favoritenentitäten prüfen; anschließend Auschecken zur Wiederherstellung versuchen. |
| Mail angenommen, aber fehlt | 202 ist keine Zustellgarantie. Absenderpostfach, Exchange-Nachrichtenablauf, Empfänger und Filter prüfen. |
| `mail_delivery_unknown` | Kein bestätigtes Scheitern; nicht blind erneut senden, zunächst Zustellung prüfen. |
| Raum als Mitarbeiter / alter Typ nach Neuanlage | M365-/Places-Sync und stabile IDs prüfen. Alte inaktive Ressource nur nach Prüfung lokal löschen. |
| Karte zeigt alten Stand | Ressourcen-Version und Browsercache prüfen; Dashboard neu laden. |

Read-Requests beachten Rate Limits und versuchen vorübergehende Fehler begrenzt erneut. Nachrichten und Kalenderlöschungen haben andere Nebenwirkungen als Lesen; Wiederholungen nur nach Prüfung. Im HA-Systemprotokoll nach `desk_booking` suchen; keine Zugangsdaten oder komplette interne Speicherdateien in Supportanfragen kopieren.

## 10. Speicherung, Sicherung und Datenschutz

HA-Config-Entry-Daten enthalten lokale Datensätze und Einstellungen, HA-Stores Verzeichnis-/Kalendercache, Tagesabschluss-/Teilnahmezustand, Pläne/Fotos und Versandhistorie. Die Zustands-Historie hängt zusätzlich von HA Recorder und dessen Aufbewahrung ab. Ein Cache ist kein revisionssicheres Archiv und keine garantierte Langzeitstatistik.

Deaktivierung in M365 erhält lokale Zusatzdaten und bisherige Historie; dauerhaftes lokales Löschen bereinigt die genannten Daten ausdrücklich. Ältere Backups können sie weiterhin enthalten. Sicherungskonzept, Aufbewahrung und Zugriff organisatorisch festlegen. Ein Backup des Integrationscodes allein enthält weder die vollständige HA-Konfiguration noch alle Laufzeitdaten.

Handbücher liegen im Integrationsordner unter `frontend/docs`, werden als statische Hilfe mit ausgeliefert und enthalten keine produktiven Konfigurationswerte. Tatsächliche Mitarbeiter-/Buchungsdaten der Karten werden über die authentifizierte HA-WebSocket-Schnittstelle und Entitätsberechtigungen gelesen; Fotoabrufe sind ebenfalls authentifiziert. Ausblenden ersetzt diese Rechte nicht. Das Bearbeitungskennwort ersetzt weder HA-Anmeldung noch Transportverschlüsselung.

Power-BI-Datenmodell, Kennzahlen zu Verspätung/vorzeitigem Ende/Nichtanreise und langfristige Auslastung wurden besprochen, sind aber nicht implementiert. Die Datei POWER_BI_PLAN.md im Entwicklungsprojekt ist ein Planungsdokument. SSO ist zurückgestellt/verworfen und wird nicht durch diese Integration bereitgestellt.

## 11. Handbücher bei Änderungen pflegen

Die Markdown-Dateien sind die redaktionellen Quellen; HTML-Ausgaben werden daraus erzeugt. Jede Änderung an Bedienung, Konfiguration, Standardwerten, Berechtigungen oder Fehlerbehandlung muss im selben Entwicklungsschritt dokumentiert werden. Firmwareänderungen gehören ebenfalls zur Prüfung.

1. Aktuellen Code und betroffene Abschnitte prüfen und beide Zielgruppen berücksichtigen.
2. Handbuchquellen aktualisieren; bei rein interner Änderung die inhaltliche Prüfung bestätigen.
3. `python documentation.py --review` im Projektordner desk-booking ausführen: HTML und geprüften Versions-/Quellenstand erzeugen.
4. `python documentation.py --check` und passende Tests ausführen; danach `python package_m365.py`.
5. Installation, Hilfelinks und tatsächliches Anzeigeverhalten prüfen; Deployment-Status im Releasebericht festhalten.

Die Paketierung verweigert ungeprüfte Änderungen oder veraltete Handbuchausgaben. Dieser technische Schutz erkennt Abweichungen, kann aber die inhaltliche Richtigkeit nicht selbst garantieren. Er ersetzt keine redaktionelle Prüfung. Die Projektanweisung AGENTS.md verpflichtet künftige Arbeiten auf diesem Projekt zur gemeinsamen Pflege.

Die Prüfsummen für Textdateien behandeln Windows- und Linux-Zeilenumbrüche gleich. Inhaltliche Änderungen erfordern weiterhin eine erneute redaktionelle Freigabe; Binärdateien werden unverändert geprüft.


## Öffentliche Repository-Fassung

Übernommen aus dem bisherigen Projektstand 0.15.2. Die öffentliche Fassung enthält neutrale Vorgaben für Absender, Buchungslink und Geräteadresse; bestehende produktive Einstellungen wurden nicht verändert oder übernommen. Der Firmware-Entwurf verwendet Secret-Referenzen und muss vor einem Einsatz an Hardware und Entitätszuordnungen angepasst werden. `docs/USER_MANUAL.md` und `docs/ADMIN_MANUAL.md` werden bei der redaktionellen Freigabe als identische Spiegel erzeugt. Der Import ist kein neuer Hardware- oder Produktivtest.
