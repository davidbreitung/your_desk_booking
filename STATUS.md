# Projektstatus

Stand: 18.11.2026. Bestehenden Stand 0.15.2 aus dem früheren Projekt übernommen; neue Planungswünsche bleiben separat erhalten.

## Implementiert im übernommenen Code

M365/Entra- und Places-Synchronisierung, Benutzer/Gruppen/Mitgliedschaften, Schreibtische und Räume, Kalendercache, lokaler Check-in/-out mit Buchungsschutz und Nichtanreise-Freigabe, tägliches Auschecken, Display-/Zubehörsteuerung, Push- und Mail-Erinnerungen, Raumplan-/Anwesenheitskarte und zwei Handbücher mit Pflegeprüfung.

Die frühere Aussage „nur Integrationstemplate“ beschreibt nicht mehr den übernommenen Quellstand. Die bisherige Statusdatei bleibt unter docs/history/planning-status-2026-11-17.md erhalten. Der unverbundene Beispiel-Integrationstemplate wird im Importzweig entfernt.

## Anforderungen und offene Arbeit

REQUIREMENTS.md um einen Ist-/Ziel-Abgleich ergänzt. Keine neueren Ziele verworfen und keine unbekannten Aufgaben nachträglich als erledigt markiert. Weiterhin offen: Microsoft-seitige Ad-hoc-Reservierungen/Check-ins, Werktagsende/15-Minuten-Dauerwahl, NFC/DESFire/Türcontroller, persönliche Kalenderanzeige, Gäste, Teams/Discord/Docbee/Pascom, Power-BI-Historie sowie Gehäuse-/Lichtkonzepte. Vorhandene lokale Check-ins sind kein nativer Places-Check-in.

## Veröffentlichung und Sicherheit

Nur eine bereinigte Referenzfassung wird veröffentlicht. Originaldateien und Produktivsystem unverändert. Neutrale Absender-/Buchungs-/Gerätevorgaben, keine produktiven Schlüssel, Mitarbeiterdaten oder Screenshots. Siehe docs/SOURCE_IMPORT.md. Die API-/Berechtigungsdetails wurden beim Import nicht erneut gegen Microsoft oder produktive Kalender getestet.

## Tests dieses Imports

- 170 Python-Tests im neuen Arbeitsordner erfolgreich, einschließlich einer zusätzlichen Prüfung zur Zeilenumbruch-Kompatibilität. Ein erster Lauf scheiterte an fehlenden Testbibliotheken; nach lokaler Installation von requirements-dev.txt war der vollständige Lauf erfolgreich. Der erste GitHub-Lauf fand eine Windows-/Linux-Abweichung in den Handbuch-Prüfsummen; Textprüfsummen wurden daraufhin unabhängig vom Zeilenumbruch gemacht.
- 13 JavaScript-Tests erfolgreich (Raumplan, Kartenbedienung und Anwesenheit).
- Dokumentationsprüfung erfolgreich; HTML-Ausgaben und Handbuchspiegel unter docs/ entsprechen den redaktionellen Quellen.
- Paketierung erfolgreich: 48 Integrationsdateien; öffentliches Referenzpaket mit neutralen Vorgaben. Kein erneuter HA-/Graph-/Hardwaretest.
- Ausgewählte Quelldateien auf bekannte private Identifikatoren, interne Adressen, private Schlüssel, Tokens und lange fest eingetragene YAML-Schlüssel geprüft. Keine Treffer im freizugebenden Dateisatz.
- Benutzerhandbuch aus dem aktuellen Stand übernommen; Administratorhandbuch um die neutrale öffentliche Referenz und den Spiegel-/Pflegeablauf ergänzt. Keine neue Benutzerfunktion eingeführt.
- GitHub-CI wird separat im Pull Request ausgeführt; deren Ergebnis ist nicht mit den lokalen Tests gleichzusetzen.

## Historische Bereitstellung

Der frühere Chat dokumentiert eine installierte Version 0.15.2 und 169 erfolgreiche Python-Tests am 16.11.2026. Das ist ein historischer Nachweis der vorherigen Umgebung, keine erneute Bereitstellung oder Hardwareprüfung dieses Imports. Während des GitHub-Abgleichs wurden weder Home Assistant neu gestartet noch Kalender, Nachrichten oder Geräte verändert.
