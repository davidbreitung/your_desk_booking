"""Update only release metadata and translations; never regenerate sources."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent / "custom_components/desk_booking"
path = root / "manifest.json"
data = json.loads(path.read_text(encoding="utf-8"))
data["version"] = "0.7.0"
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for path in (root / "strings.json", root / "translations/en.json", root / "translations/de.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    de = path.name == "de.json"
    permission = ("Microsoft Graph benötigt User.Read.All, GroupMember.Read.All und Place.Read.All als Anwendungsberechtigungen mit Administratorzustimmung."
                  if de else "Microsoft Graph requires User.Read.All, GroupMember.Read.All and Place.Read.All application permissions with administrator consent.")
    for section in ("config", "options"):
        data[section].setdefault("error", {})["insufficient_permissions"] = permission
        data[section]["error"]["ambiguous_place_identity"] = "Die Zuordnung einer Places-Ressource zu einem Konto ist nicht eindeutig." if de else "A Places resource has an ambiguous account mapping."
        for step, fields in data[section].get("step", {}).items():
            if step in ("user", "m365"):
                fields["description"] = permission + (" Secret leer lassen, um den bestehenden Wert zu behalten." if de else "Leave the secret blank to keep its current value.")
    data["config_subentries"]["desk"]["step"]["reconfigure"]["description"] = (
        "Lokale Einstellungen bearbeiten. Bei Places-Schreibtischen ist das Display optional; für den Check-in wird es benötigt. Places-Synchronisierung erhält diese Einstellungen. {detail}"
        if de else "Edit local settings. A display is optional for Places desks and required for check-in. Places sync preserves these settings. {detail}")
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
