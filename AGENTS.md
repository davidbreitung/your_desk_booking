# Agent development rules

Applies to all work in this repository, including Codex and any other agent that explicitly reads this file.

1. Read `REQUIREMENTS.md`, `STATUS.md`, `docs/USER_MANUAL.md`, `docs/ADMIN_MANUAL.md`, and this file before making changes.
2. Keep `REQUIREMENTS.md` aligned with functional requirements, acceptance criteria, and scope changes. Record decisions instead of silently changing scope.
3. Update `STATUS.md` for every meaningful development task: implemented changes, tests actually executed and their results, outstanding issues, and next steps.
4. Commit relevant documentation together with code changes. Do not claim tests passed unless executed; record unrun tests as such.
5. Follow Home Assistant's current integration conventions; prefer async-safe APIs, proper config flows, and secure credential handling.
6. Never commit secrets, access tokens, private configuration, or personally identifying data.
7. Use a feature branch and pull request for risky changes; do not deploy or restart production Home Assistant without explicit authorization.
8. Before completing a task, verify that code, requirements, status, README, and both manuals are consistent.
9. If no requirement changed, explicitly record that in `STATUS.md`; do not rewrite `REQUIREMENTS.md` unnecessarily.
10. These instructions do not automatically propagate to other tools or repositories; ensure agents read them at the start of a task.
11. Maintain two separate manuals throughout development: `docs/USER_MANUAL.md` for end users and `docs/ADMIN_MANUAL.md` for administrators. Create both at project start. Update the affected sections whenever functionality, configuration, setup, permissions, troubleshooting, or operational behavior changes; commit manual changes together with code. If a change does not affect a manual, note that explicitly in `STATUS.md` rather than making cosmetic edits. Never describe unimplemented features as available.

## Imported implementation and documentation gate

# Desk Booking: verbindliche Dokumentationspflege

Bei jeder Weiterentwicklung von Desk Booking sind die Handbücher Bestandteil derselben Änderung, nicht eine nachgelagerte Aufgabe.

- Maßgebliche Quellen: `desk-booking/custom_components/desk_booking/frontend/docs/benutzer.md` und `administrator.md`. Aktuellen Code prüfen; ältere Releaseberichte sind keine aktuelle Bedienungsanleitung.
- Geänderte Funktionen, Einstellungen, Standardwerte, Berechtigungen, Grenzen, Fehlermeldungen und Bedienwege in den passenden Handbüchern aktualisieren. Benutzer- und Administratorperspektive getrennt halten. Bei rein internen Änderungen die inhaltliche Prüfung dokumentieren, keine erfundene Funktionsänderung ergänzen.
- Firmwareänderungen ebenfalls gegen die Handbücher prüfen. NFC-Zuordnung nicht als fertig angebundener NFC-Check-in beschreiben. Planungen, SSO und Power BI nicht als implementiert ausgeben.
- Keine produktiven Zugangsdaten, realen Mandanten-/Objekt-IDs, personenbezogenen Screenshots oder privaten Konfigurationen in die ausgelieferten Handbücher übernehmen. Sie werden als allgemeine statische Hilfe bereitgestellt.
- Nach inhaltlicher Prüfung `python desk-booking/documentation.py --review` ausführen. Dies erzeugt HTML, Inhaltsverzeichnisse und die Versions-/Quellenprüfung. `--review` ist eine bestätigte redaktionelle Prüfung, kein Ersatz für die Inhaltsarbeit.
- Vor Paketierung `python desk-booking/documentation.py --check` ausführen. `package_m365.py` verweigert künftig Pakete bei abweichenden Quellen oder veralteten Handbuchdateien. Nie diese Prüfung umgehen, um Änderungen ohne geprüfte Dokumentation zu veröffentlichen.
- HTML-Hilfe und Links unter Konfigurieren → Handbücher bei Änderungen an Hilfe/Navigation live prüfen. Tatsächlichen Installationsstatus und relevante Tests dokumentieren. Die zentralen Optionen und lokale Zusatzdaten erhalten.

- The implemented integration is in `desk-booking/custom_components/desk_booking`, with HA domain `desk_booking`; the repository name does not rename the domain.
- `docs/USER_MANUAL.md` and `docs/ADMIN_MANUAL.md` are generated mirrors of the canonical manuals. Run `python desk-booking/documentation.py --review` after editorial review; do not edit the mirrors independently.
- Preserve future requirements separately from implemented functionality. Do not change production Home Assistant during repository synchronization.
