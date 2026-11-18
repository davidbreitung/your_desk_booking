"""Update translations and release metadata without regenerating older assets."""
import json
from pathlib import Path

root = Path(__file__).parent / "custom_components/desk_booking"
for path in [root / "strings.json", *sorted((root / "translations").glob("*.json"))]:
    data = json.loads(path.read_text(encoding="utf-8"))
    de = path.stem == "de"
    fields = {"tenant_id": "Tenant-ID", "client_id": "Client-ID", "client_secret": "Client-Secret", "sync_interval": "Sync-Intervall (Minuten)" if de else "Sync interval (minutes)"}
    description = ("M365 führt die Mitarbeiterstammdaten. App-Berechtigungen User.Read.All und GroupMember.Read.All mit Administratorzustimmung erforderlich. Bei Änderungen Secret leer lassen, um es beizubehalten." if de else
                   "M365 owns employee identity data. Application permissions User.Read.All and GroupMember.Read.All with admin consent required. Leave secret blank on edits to retain it.")
    errors = {
        "invalid_config": "Tenant-ID, Client-ID, Secret und Intervall prüfen." if de else "Check tenant ID, client ID, secret and interval.",
        "invalid_auth": "Microsoft-Anmeldung fehlgeschlagen. Secret und App prüfen." if de else "Microsoft authentication failed. Check secret and app.",
        "insufficient_permissions": "Graph-Berechtigungen oder Administratorzustimmung fehlen." if de else "Graph permissions or admin consent are missing.",
        "cannot_connect": "Verbindung fehlgeschlagen. Später erneut versuchen." if de else "Connection failed. Try again later.",
        "rate_limited": "Microsoft begrenzt die Anfragen. Später erneut versuchen." if de else "Microsoft is throttling requests. Try again later.",
        "invalid_response": "Unvollständige Microsoft-Antwort; lokale Daten bleiben erhalten." if de else "Incomplete Microsoft response; local data retained.",
        "graph_error": "Microsoft Graph hat die Anfrage abgewiesen." if de else "Microsoft Graph rejected the request.",
        "delta_expired": "Microsoft-Synchronisierungsstand abgelaufen." if de else "Microsoft synchronization cursor expired.",
        "tenant_change_not_allowed": "Mandantenwechsel wird zum Schutz lokaler Identitäten nicht unterstützt." if de else "Changing tenant is not supported, to protect local identities.",
    }
    data["config"]["step"]["user"] = {"title": "Desk Booking · Microsoft 365", "description": description, "data": fields}
    data["config"].setdefault("error", {}).update(errors)
    options = data.setdefault("options", {})
    steps = options.setdefault("step", {})
    if "display" not in steps:
        steps["display"] = steps.get("init", {})
    steps["init"] = {"title": "Desk Booking", "menu_options": {"display": "Displays", "m365": "Microsoft 365"}}
    steps["m365"] = {"title": "Microsoft 365", "description": description, "data": fields}
    options.setdefault("error", {}).update(errors)
    employee = data["config_subentries"]["employee"]
    employee["abort"]["managed_by_m365"] = "Mitarbeiter werden ausschließlich aus Microsoft 365 importiert." if de else "Employees are imported exclusively from Microsoft 365."
    employee["step"]["reconfigure"]["description"] = "NFC-Zuordnung lokal ändern. Stammdaten und Aktivstatus kommen aus Microsoft 365. Tischhöhen am Mitarbeitergerät bearbeiten." if de else "Edit the local NFC assignment. Identity and active status come from Microsoft 365. Edit heights on the employee device."
    employee["step"]["reconfigure"]["data"] = {"nfc_tag_id": "NFC-Tag-ID"}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
path = root / "manifest.json"
data = json.loads(path.read_text())
data.update(version="0.6.0", iot_class="cloud_polling")
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
