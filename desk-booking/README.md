> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

> Aktueller Quellstand: **0.15.2**. Maßgeblich sind ab jetzt das [Benutzerhandbuch](custom_components/desk_booking/frontend/docs/benutzer.md) und das [Administratorhandbuch](custom_components/desk_booking/frontend/docs/administrator.md). HTML-Ausgaben derselben Fassung liegen daneben und sind über Konfigurieren → Handbücher abrufbar. Der tatsächliche Installationsstatus steht in [FEATURES_0150.md](FEATURES_0150.md).
>
> Die folgenden Abschnitte sind historische Entwicklungsnotizen, keine aktuelle Bedienungsanleitung. Insbesondere manuelle Mitarbeiter-/Schreibtischanlage, Sicherheitsgruppen-Beschränkung, frühere Displayfarben und alte Aussagen zu fehlender M365-Anbindung gelten nicht mehr. Aktuelle individuelle Mail-Schalterstellungen sind keine Auslieferungsdefaults.
>
> Entwicklung: Projektanweisung [AGENTS.md](../AGENTS.md) beachten, beide Handbücher zusammen mit Änderungen pflegen, nach redaktioneller Prüfung `python documentation.py --review` und danach `python package_m365.py` ausführen. Die Paketierung verweigert nicht geprüfte Quellen-/Handbuchstände.

# Desk Booking 0.7.0 – Microsoft 365 und Places

Version 0.7.0 ergänzt Microsoft Places direkt in Desk Booking. M365 bleibt alleinige Mitarbeiterquelle; Places-Schreibtische werden bei jedem automatischen oder manuellen Sync als Schreibtische importiert. Lokale Display- und Zubehörzuordnungen bleiben in Home Assistant editierbar.
Version 0.7.0 ist auf Home Assistant installiert; der echte Import und der manuelle Folgesync wurden erfolgreich geprüft. Einrichtung, Berechtigungen, Tests und Deployment-Nachweis stehen in [PLACES_070.md](PLACES_070.md). Die ursprüngliche Mitarbeiter-/Gruppenanbindung ist in [M365_060.md](M365_060.md) dokumentiert.
Die frühere manuelle Mitarbeiteranlage ist ab 0.6.0 gesperrt; entsprechende Anleitungen weiter unten beschreiben ältere Versionen.
Für aktuelle Pakete `package_m365.py` verwenden: Das ältere `build_package.py` generiert Metadaten für frühere Versionen neu.

# Frühere Version 0.2.0

## Neu: lokaler Check-in ohne Reservierung

Unter **Desk Booking → Tisch hinzufügen** einen Tischnamen eingeben und das
ESPHome-Schreibtisch-Display auswählen. Unterstützt werden aktuell Displays mit
den bekannten ESPHome-Number-Entitäten **Favorit Sitzen** und **Favorit Stehen**.
Die Zuordnung zu Motor-Sollwerten oder beliebigen Number-Entitäten wird abgewiesen.
Ein Display kann nur einem Tisch zugeordnet werden.

Am virtuellen Tischgerät:

1. **Mitarbeiter für Check-in** auswählen.
2. **Test-Check-in** drücken. Das Profil muss aktiv und der Tisch frei sein.
3. **Belegung** und **Angemeldeter Mitarbeiter** zeigen die Zuordnung.
4. **Auschecken** stellt die vor dem Check-in vorhandenen Displayfavoriten wieder
   her und löst anschließend die Zuordnung.

Der Testbutton simuliert den lokalen Check-in direkt über die Mitarbeiterauswahl;
er benötigt keinen NFC-Tag und löst kein `tag_scanned`-Ereignis aus. Eine echte
NFC-Leser-Anbindung ist weiterhin ein späterer Schritt. Auch echte lokal
angelegte Profile können verwendet werden, jedoch ohne Online-Identitätsprüfung.

Es werden ausschließlich Favoriten gespeichert, keine Motoraktionen ausgelöst.
Das Display unterstützt aktuell ganze cm: 74,5 cm werden zu 75 cm gerundet.
Die im Profil gespeicherte Präferenz bleibt unverändert. Der Belegungssensor
zeigt die tatsächlich übertragenen Werte in seinen Attributen. Werte außerhalb
des Displaybereichs werden abgelehnt, nicht auf eine Grenze gekürzt.
Eine Begrüßung bzw. Auscheckmeldung wird über die bekannten Nachricht-Entitäten
desselben Displays versucht; sie ist nur kurz sichtbar und nicht Teil der
Belegungsbestätigung. Den dauerhaften Belegungsstatus zeigt zunächst HA.

Gleichzeitige Check-ins werden serialisiert. Ein Mitarbeiter kann nicht an zwei
Tischen gleichzeitig angemeldet sein, und ein belegter Tisch wird nicht überschrieben.
Änderungen an Mitarbeiterpräferenzen während einer Sitzung werden erst beim nächsten
Check-in übertragen. Das Sperren eines Profils verhindert neue Check-ins, beendet
aber keine bestehende Sitzung. Ein freier Tisch ist Voraussetzung für die Änderung
seiner Displayzuordnung. Vor dem Löschen belegter Tische oder Profile immer auschecken;
das native HA-Löschen ist kein automatischer Check-out.

Bei einem Übertragungsfehler wird die Wiederherstellung versucht. Scheitert auch
diese, bleibt der Tisch gesperrt. Nach Wiederherstellung der Displayverbindung
**Auschecken** erneut drücken. Ein beim Neustart unterbrochener Vorgang bleibt
ebenfalls als ausstehend sichtbar und kann über Auschecken bereinigt werden.
Sitzungen sind in HA gespeichert, aber es gibt keine automatische Rückübertragung
nach Änderungen außerhalb dieser Integration oder nach einem Geräte-Firmwarewechsel.

Microsoft/Places-Synchronisation, Reservierungen und produktive NFC-Authentifizierung
bleiben vollständig ausgesetzt. Die folgenden Angaben beschreiben die weiterhin
vorhandene Mitarbeiterverwaltung aus der ersten Version.

Erster Prototyp für lokale Mitarbeiterpräferenzen in Home Assistant.
Zielsystem: Home Assistant Core 2026.11.1. Keine zusätzlichen Python-Pakete.

## Umfang

- Ein Integrationseintrag mit Mitarbeiter-Unter­einträgen (Config Subentries).
- Ein virtuelles Gerät je Mitarbeiter: Sitzhöhe und Stehhöhe als Number-Entitäten,
  Profil aktiv als Switch. Höhen in cm, Eingabebereich 50–140 cm, Sitzhöhe < Stehhöhe.
  Der Bereich ist eine Plausibilitätsgrenze für Präferenzen, keine Freigabe für einen Tisch.
- HA speichert alle Werte über seine Config-Entry-API dauerhaft. Keine direkten
  Zugriffe auf interne `.storage`-Dateien. Änderungen bleiben bei Reload/Neustart erhalten.
- Microsoft-Zuordnung aus Mandanten-ID + unveränderlicher Entra-Benutzer-Objekt-ID.
  Keine E-Mail-Adresse als Schlüssel; Identität nach Erstellung unveränderlich.
- Optional eine NFC-Tag-ID pro Profil, exakt und unter Beachtung der Groß-/Kleinschreibung.
  Mehrfachzuordnung wird auch bei inaktiven Profilen verhindert. Leeres Feld löst die Zuordnung.
- Identitäts- und Tag-Daten bleiben in der Profilkonfiguration. Keine öffentlichen
  NFC-/Identitäts-Zustandsentitäten oder entsprechenden Entity-Attribute.
- Deutsch und Englisch. Testprofile mit eigener Kennung und sichtbarem `[TEST]`-Präfix.
- Kein HA-Benutzerkonto für Mitarbeiter erforderlich.

## Installation

1. ZIP entpacken. Den Ordner `custom_components/desk_booking` einschließlich
   `translations` nach `/config/custom_components/desk_booking` auf HA kopieren.
   Eine bestehende Installation vor dem Überschreiben sichern.
2. Home Assistant neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Desk Booking**.
4. Im Desk-Booking-Eintrag **Mitarbeiter hinzufügen** wählen.
5. Für echte Profile Namen, Entra-Mandanten-ID und Benutzer-Objekt-ID eingeben.
   Ohne echte IDs ausdrücklich **Testprofil** aktivieren und z. B. `demo-employee-01`
   als fiktive Testkennung verwenden. Es werden keine Mitarbeiter automatisch angelegt.
6. Sitz-/Stehhöhe und Aktivstatus am virtuellen Gerät unter **Konfiguration** bearbeiten.
   Anfangswerte sind 72 cm und 110 cm; sie lösen keine Aktion aus.

## Bearbeiten und Entfernen

- Über das Menü des Mitarbeiter-Unter­eintrags **Profil bearbeiten** öffnen:
  Anzeigename, NFC-Tag und Aktivstatus ändern. Höhen bleiben dabei erhalten.
- **Profil aktiv = aus** speichert eine lokale Sperre. Profil und Werte bleiben editierbar.
  Da noch kein Check-in implementiert ist, wird damit kein externes Konto gesperrt.
- Über das Menü des Mitarbeiter-Unter­eintrags **Löschen** wählen. HA entfernt
  zugehörige Entitäten und das virtuelle Gerät. Dies löscht die lokalen Präferenzen
  und NFC-Zuordnung; keine Microsoft-Daten. Vor echtem Datenverlust HA-Backup erstellen.
- Zum Wechsel einer echten Microsoft-Identität bewusst ein neues Profil erstellen.
  Zum Entfernen der ganzen Integration deren HA-Menü verwenden; danach kann der
  Komponentenordner entfernt und HA neu gestartet werden.

## Grenzen und nächster Schritt

Die Microsoft-IDs werden syntaktisch geprüft, **nicht online verifiziert**. Entra
bleibt die vorgesehene Identitätsquelle, Microsoft Places die Buchungsquelle.
Es bestehen noch keine OAuth-, Graph- oder Places-Verbindung, keine Synchronisierung,
keine Buchungs-/Zeitraumprüfung, keine automatische Profillöschung aus Entra und kein
produktiver Check-in. Auch vorhandene Places-Ressourcen werden nicht verändert.

Diese Version hört nicht auf NFC-Scans und bewegt keine Tische. Der lokale
Test-Check-in ist oben beschrieben. Später folgen Buchungsprüfung und der Zustand
reserviert. Eine zentrale Anmeldung
für fremde Places-Buchungen ist nicht als funktionsfähig angenommen.

HA-Administratoren können die Profilkonfiguration einschließlich NFC-Zuordnung lesen.
HA-Backups enthalten sie ebenfalls. Die Konfiguration ist keine Verschlüsselung.
Entity-Berechtigungen richten sich nach HA; `EntityCategory.CONFIG` ist keine
zusätzliche Zugriffssperre. NFC-Kennungen allein sind kein sicherer Identitätsnachweis.

## Entwicklung und Prüfung

`python build_package.py` erzeugt Übersetzungen, ZIP und SHA256-Prüfsumme unter `dist`.
`python -m unittest discover -s tests -v` prüft die reine Validierungslogik.
`python -m compileall -q custom_components` prüft Python-Syntax.
Diese lokalen Tests ersetzen keinen HA-Laufzeittest. Die bei Auslieferung tatsächlich
durchgeführten Prüfungen und der Installationsstand stehen in `VERIFICATION.md`.

Architekturgrundlage: [HA Config Subentries](https://contributors.home-assistant.io/core/integrations/subentries/).
# Version 0.4: Touch-Bedienung und Ressourcenmonitor

Ein-/Aus-Tasten ersetzen das Schalten per Ringdruck. Ab zwei Lichtern zeigt eine zusätzliche Symbolleiste alle belegten Lichtseiten. Nach der Lichtauswahl unter **Tisch bearbeiten** lassen sich je Licht ein Anzeigename und eines von sechs üblichen MDI-Lichtsymbolen pflegen.

CPU-, Heap-, RAM-, PSRAM- und Flash-Diagnose werden ausschließlich vom ESPHome-Gerät bereitgestellt. Details: [TOUCH_AND_DIAGNOSTICS_040.md](TOUCH_AND_DIAGNOSTICS_040.md).

# Version 0.3: Anzeige und bis zu vier Lichter

Der Firmenname wird zentral unter **Desk Booking → Konfigurieren** gepflegt. Unter **Tisch bearbeiten** lassen sich der Anzeigename und bis zu vier dimmbare Lichter in Displayreihenfolge zuordnen. Die vorbereitete Display-Firmware übernimmt diese Einstellungen ohne erneutes Aufspielen. Die Integration verarbeitet Dimmer und Ringdruck direkt; separate Lichtautomationen sind nicht mehr erforderlich. Check-in-/Check-out-Meldungen erhalten einen grünen animierten Ring.

Details und Prüfstand: [CONTROLS_030.md](CONTROLS_030.md).

