> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Prüfung und Installationsstand – 15.11.2026

## Erweiterung 0.2.0: lokaler Tisch-Check-in

- 26 Tests erfolgreich: zusätzlich 12 simulierte Transaktionstests für Check-in,
  Rundung, Checkout, Mehrfachbelegung, unerreichbare/falsche Ziele, Rollback,
  fehlgeschlagene Wiederherstellung und unterbrochene Übertragungen.
- Syntaxprüfung erfolgreich. Alle Integrationsmodule in einem separaten Prozess
  mit den tatsächlich installierten HA-Bibliotheken erfolgreich importiert.
- Version 0.2.0 direkt auf HA installiert; vorheriger Komponentenordner gesichert.
- Nach HA-Neustart Integration geladen, beide bestehenden Mitarbeiterprofile erhalten.
- Tisch `Schreibtisch 01` über den nativen HA-Subentry-Flow erstellt und mit
  `Schreibtisch Display 01` verbunden. Fünf Entitäten automatisch angelegt.
- Demo-Profil ausgewählt; Check-in am tatsächlichen Display erfolgreich:
  Belegung `checked_in`, Demo-Mitarbeiter zugeordnet, Favoriten 75/113 cm.
  Profilpräferenz 74,5 cm blieb unverändert; Displaywert wurde auf 75 cm gerundet.
- Begrüßung in der Nachricht-Text-Entität bestätigt. Die physische Anzeige wurde
  nicht mit einer Kamera verifiziert.
- Erneuter Check-in bei belegtem Tisch abgewiesen.
- Integration während Belegung neu geladen: Belegung und Mitarbeiter erhalten.
- Vollständiger HA-Neustart während eines zweiten Demo-Check-ins: Belegung,
  Mitarbeiter und Displayfavoriten erhalten. Anschließend erfolgreich ausgecheckt.
- Abschließender Reconfigure-Flow des Tisches erfolgreich; Version 0.2.0 geladen.
- Auschecken erfolgreich: Tisch frei, ursprüngliche Displayfavoriten 74/110 cm.
- Profil gesperrt und Check-in versucht: korrekt abgewiesen. Demo-Profil danach
  wieder freigegeben, damit der Nutzer den Ablauf direkt ausprobieren kann.
- Höhen-Sollwert vor und nach dem gesamten Ablauf unverändert 74 cm. Die Integration
  schreibt ausschließlich die zwei validierten Favoriten sowie Nachricht-Entitäten;
  keine Sollwert-/Motor-Aktion und kein Microsoft-Aufruf.
- Endzustand: Tisch frei, Demo-Profil aktiv und ausgewählt, Displayfavoriten
  74/110 cm. Temporäre Übertragungsdateien aus `www` entfernt und deren Abwesenheit
  über den HA-Connector bestätigt. Die vorherige Integration liegt gesichert unter
  `/config/desk_booking_backup_20261115_154516`.
- Nach Abschluss unserer Tests wurde in der HA-Oberfläche ein vom Nutzer
  ausgelöster Check-in mit `[TEST] Alex Beispiel` sichtbar. Dieser aktuelle
  Nutzerzustand wurde nicht zurückgesetzt; der oben genannte freie Zustand ist
  der Abschlusszustand unserer eigenen Testfolge.

Für einen späteren Displaywechsel wurde zusätzlich die Aktualisierung der
Tisch-Identität im Reconfigure-Flow korrigiert. Die Tests für Profile und
Transaktionen ersetzen keine Prüfung mit einem zweiten physischen Display.

### Verbleibende Grenzen

Keine Reservierungsprüfung, kein NFC-Ereignisempfang, keine Microsoft-Verbindung.
Keine automatische Abmeldung bei Profil-Deaktivierung. Vor dem Löschen eines
belegten Profils oder Tisches auschecken. Die dauerhafte Belegungsanzeige liegt in
HA; am Display wird eine temporäre Nachricht angezeigt.

---

## Vorherige Prüfung der Mitarbeiterverwaltung 0.1.0

## Lokal

- 14 unittest-Tests erfolgreich: Identitäten, Testmodus, doppelte NFC-Zuordnung,
  Höhenbereich/-reihenfolge, leere und ungültige Eingaben, Übersetzungsstruktur.
- Python-Syntaxprüfung erfolgreich.
- Paket: `dist/desk-booking-0.1.0.zip`, Prüfsumme in `dist/SHA256SUMS.txt`.

## Verbundenes Home Assistant

Nach manueller Installation durch den Nutzer wurde die Integration über den
HA-Connector mit Status `loaded` bestätigt. Mitarbeiter-Subentries unterstützen
den Reconfigure-Flow. Die Einrichtung wurde nicht nur aus der Nutzerbestätigung abgeleitet.

Ein ausdrücklich fiktives Profil `[TEST] Demo Mitarbeiter` wurde über den nativen
Subentry-Flow angelegt: Testkennung `demo-employee-01`, NFC-Testkennung `TEST-NFC-01`.
Es existieren zwei Number-Entitäten und ein Aktiv-Switch mit deutschen Namen.

Erfolgreich gegen HA geprüft:

- Anlage des Profils und automatische Bereitstellung der drei Entitäten.
- Sitzhöhe auf 74,5 cm und Stehhöhe auf 113 cm geändert.
- Aktiv-Switch ausgeschaltet.
- Profil-Reconfigure-Flow erfolgreich ausgeführt, ohne Höhenverlust.
- Integration gezielt neu geladen: beide Höhen und inaktiver Zustand erhalten.
- Sitzhöhe 120 cm bei Stehhöhe 113 cm abgewiesen; Sitzhöhe bleibt 74,5 cm.
- Zweites Profil mit demselben NFC-Testtag abgewiesen (`duplicate_tag`), auch
  wenn das bestehende Profil inaktiv ist. Der offene Prüf-Flow wurde abgebrochen.
- Öffentliche Entity-Attribute enthalten keine Microsoft- oder NFC-Kennung.

Das Demo-Profil bleibt zur Bedienungsprüfung inaktiv vorhanden. Es gibt keine
echten Mitarbeiterdaten, keine Microsoft-Verbindung und keine Hardwareaktionen.

Zum damaligen Stand nicht live geprüft: kompletter HA-Neustart nach Werteänderung, Profillöschung,
Identitätsprüfung gegen Entra, Places-Buchungen oder NFC-Lesegerät. Der Reload-Test
ist kein Neustarttest. Die persistente Ablage nutzt HA Config-Subentry-Daten.

Beim ersten Installationsversuch wurde ausschließlich die öffentliche Quelldatei
`/config/www/desk-booking-install-0.1.0.json` als Übertragungshilfe abgelegt.
Sie enthält keine Mitarbeiterdaten oder Geheimnisse und wird von der Integration
nicht benötigt. Ihre spätere Entfernung wurde nicht verifiziert.
