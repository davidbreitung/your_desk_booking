> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Microsoft Places in Desk Booking 0.7.0

## Verhalten

- Derselbe automatische/manuelle M365-Sync liest Benutzer und Gruppen per Delta sowie alle Seiten der Places-Typen `desk`, `room` und `workspace`.
- Echte Places-`desk`-Objekte werden bei jedem Lauf als Schreibtisch-Subentries importiert. Neu angelegte Schreibtische benötigen keinen weiteren lokalen Anlagevorgang.
- Ressourcen-Konten werden anhand `mailboxDetails.externalDirectoryObjectId` bzw. exakt übereinstimmender E-Mail/UPN erkannt. Anzeigenamen und `mode.assignedUserId` sind keine Ressourcen-Identität.
- Räume und Arbeitsplatz-Pools werden aus den Mitarbeitern ausgeschlossen, aber nicht ungefragt zu einzelnen Schreibtischen umgedeutet.
- `placeId` ist die bevorzugte Identität, mit `id` als Rückfall für ältere Antworten. Löschen oder `unavailablePlaceMode` deaktiviert den lokalen Schreibtisch; Daten und Belegung bleiben erhalten. Ein deaktiviertes Entra-Ressourcenkonto allein deaktiviert keinen Schreibtisch (Ressourcenkonten sind oft absichtlich für Anmeldung gesperrt).
- Lokale Namen/Displaynamen, Display, vier Lichtzuordnungen mit Namen/Symbolen, Rollo/Jalousie, Schaltkanal und Belegungsdaten bleiben lokal. Bearbeitung über den bestehenden Schreibtisch-Rekonfigurationsdialog.
- Ohne Display ist ein importierter Schreibtisch sichtbar und konfigurierbar; Check-in liefert einen verständlichen Hinweis und schreibt keine Gerätewerte.
- Bereits irrtümlich importierte Mitarbeiter-Ressourcen werden über die verwaltete HA-Subentry-API umklassifiziert. Die opaque Subentry-ID, Gerätezuordnung und gespeicherte lokale Felder bleiben erhalten. Die vier alten Mitarbeiterentitäten werden deaktiviert, nicht aus Registry/Recorder gelöscht.
- Umklassifizierung verwendet `async_add_subentry` mit bestehender Subentry-ID und neuer eindeutiger Places-Identität. Der HA-Core-2026.11.1-Code ersetzt so den Datensatz ohne `async_clear_config_subentry`; keine direkte `.storage`-Bearbeitung. Nach Strukturänderungen erfolgt ein zusammengefasster Integrations-Reload.
- Vollständiger Snapshot wird vor Anwendung gespeichert. Ein Fehler auf einer späteren Places-Seite übernimmt keine Teilmenge und deaktiviert keine Schreibtische. 0.6-Caches werden nicht zur Places-Umklassifizierung verwendet.

## Microsoft-Konfiguration

Zusätzlich zu `User.Read.All` und `GroupMember.Read.All`: **`Place.Read.All` als Anwendungsberechtigung** mit Administratorzustimmung. Keine Schreibberechtigung erforderlich. Places muss im Mandanten korrekt eingerichtet sein; Microsoft nennt `EnableBuildings` als Voraussetzung für sichtbare Listenantworten. Eine leere Antwort beweist nicht, dass Places eingerichtet ist.

Places bietet für diese Listen keinen dokumentierten Delta-Endpunkt. Daher vollständiger paginierter Abruf pro Sync, standardmäßig 15 Minuten. Rate Limits, Retry-After, Token-Erneuerung und der vorhandene lokale Cache gelten auch für Places.

Quellen:
- https://learn.microsoft.com/en-us/graph/api/place-list?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/resources/desk?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/resources/mailboxdetails?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/resources/places-api-overview?view=graph-rest-1.0
- https://raw.githubusercontent.com/home-assistant/core/2026.11.1/homeassistant/config_entries.py

## Sicherung und Prüfung

Lokale Ausgangsdateien: `backups/pre-places-20261115-205602/`.
HA-Backup `bdc40b81`, „Vor Desk Booking Microsoft Places“, 15.11.2026 20:56 Uhr Europe/Berlin, NASHome, inklusive Konfiguration und Datenbank.

89 lokale Tests bestanden (simulierte HA-Grenzen, keine echte HA-Testinstallation): Graph-Paginierung/Fehler, Ressourcen-Zuordnung, Umklassifizierung und Datenerhalt, zukünftige Importe, deaktivierte/ungebundene Schreibtische sowie bestehende Profil-, Display- und Transaktionstests.

Installierte Python-Dateien wurden nach Upload gegen lokale Quellen verglichen: 10 geänderte/neue Module identisch. Version 0.7.0 wurde in HA Core 2026.11.1 geladen. „Schreibtisch 1“ wurde im vorhandenen Datensatz als Typ Tisch / Gerätemodell Desk umklassifiziert. Die vier bisherigen Mitarbeiterentitäten sind deaktiviert; ihre Historie ist auf der Geräteseite weiterhin sichtbar. Der Schreibtisch-Konfigurationsdialog wurde ohne Display erfolgreich gespeichert.

Ein weiterer manueller Sync am 15.11.2026 um 21:13:40 Europe/Berlin meldete `ok`, `error: null`, 10 Mitarbeiter, 1 Places-Schreibtisch, 0 Räume, 0 Arbeitsplatz-Pools, 1 erkanntes Ressourcenkonto und 8 Gruppen; Intervall 15 Minuten. Kein doppelter Schreibtisch entstand. Testnachweis für zusätzliche spätere Schreibtische: lokale Projektions-/Paginationstests; es wurde keine künstliche Ressource im produktiven Microsoft-Mandanten angelegt.

Die Protokollprüfung zeigte zusätzlich einen veralteten Registry-Aufruf. Er wurde auf `async_get_device_by_identifier(identifier, config_entry_id)` umgestellt (HA Core 2026.11.1). Die sieben betroffenen Lifecycle-Tests bestanden erneut; `m365.py` wurde nachinstalliert. Nach dem abschließenden Neustart: automatischer Sync am 15.11.2026 um 21:18:25 Europe/Berlin wieder `ok`, Schreibtischgerät und Einstellungen erhalten, Protokollsuche `desk_booking`: „Keine Probleme ... gefunden“. Diese letzte Prüfung erfolgte über die lokale Chrome-Oberfläche, da der Cloud-Connector nach dem Neustart nicht erreichbar war.

Screenshot des installierten Schreibtischgeräts: `places-installation-070.jpg`. „Desk 1“ war bereits bei der letzten Bestandsaufnahme vor Installation nicht mehr im Live-Eintrag vorhanden; es wurde kein lokaler Schreibtisch gelöscht oder mit der neuen Places-Ressource zusammengeführt.

Paket: `dist/desk-booking-0.7.0.zip`, SHA256 `a1fea1e2eb2cc674672e727b605a246169b29798999c50bcc763fc82dca74a5c`.
