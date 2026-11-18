> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Buchungssync und ersetzte Räume – 0.12.2

Ursache live bestätigt: zwei inaktive frühere Stand-Up-Räume erzeugten errors=['inactive'] und damit einen falschen zentralen Fehlerstatus. Die beiden neuen gleichnamigen Schreibtische waren bereits aktiv und hatten erfolgreiche aktuelle Kalenderabrufe (kein Buchungstreffer, kein Abruffehler).

Korrektur: Inaktive Ressourcen werden ohne Kalenderzugriff übersprungen, alte Fehler entfernt und Cache/Historie behalten. Der Ressourcenstatus bleibt inaktiv; echte Fehler aktiver Ressourcen bleiben sichtbar. Zentralstatus zählt inactive_rooms/inactive_desks separat. Gelöschte Räume erhalten den Namenszusatz (inaktiv); Reaktivierung derselben Places-ID stellt den Cloud-Namen wieder her. Keine Zusammenführung anhand des Namens, keine Löschung von Geräte-, Entity- oder Kalenderdaten.

147 Python-Tests erfolgreich, inklusive gelöschtem Raum und neuem gleichnamigen Schreibtisch, Historienerhalt und weiterhin gemeldetem fehlendem Postfach einer aktiven Ressource.

Quellbackup lokal backups/pre-sync-0122, remote /config/desk_booking_backup_0122_20261116_001639. Installationsprüfung gegen 0.12.1-Baseline und SHA256 aller 36 Paketdateien erfolgreich. Paket-SHA256 8dfb783cb78556573fe209287f9f7d4124c6c5520157d1e83ac157bdc1e8e73d.
Live-Abschluss 16.11.2026 ca. 00:18 Europe/Berlin: Version 0.12.2 aktiv. Buchungen-Synchronisierung ok, failed_desks=0, failed_rooms=0, inactive_rooms=2, errors=[]. Beide Stand-Up-Schreibtische data_current=true und error=null. Alte Räume in Geräteansicht als (inaktiv) sichtbar, neue Schreibtische unter Schreibtisch; 162 Entitäten erhalten. Screenshot sync-fix-0122.png.
