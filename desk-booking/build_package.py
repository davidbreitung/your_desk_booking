"""Build reproducible release files from this directory (Python stdlib only)."""

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
COMPONENT = ROOT / "custom_components" / "desk_booking"


def translations(german=False):
    labels = (
        {"name": "Anzeigename", "test_profile": "Testprofil (keine echte Microsoft-Identität)",
         "tenant_id": "Microsoft Entra Mandanten-ID", "object_id": "Microsoft Benutzer-Objekt-ID / Testkennung",
         "nfc_tag_id": "NFC-Tag-ID (optional)", "active": "Profil aktiv"}
        if german else
        {"name": "Display name", "test_profile": "Test profile (not a real Microsoft identity)",
         "tenant_id": "Microsoft Entra tenant ID", "object_id": "Microsoft user object ID / test identifier",
         "nfc_tag_id": "NFC tag ID (optional)", "active": "Profile active"}
    )
    errors = (
        {"invalid_name": "Bitte einen Namen mit 1 bis 100 Zeichen eingeben.",
         "invalid_uuid": "Bitte eine gültige, nicht leere Microsoft-ID im UUID-Format eingeben.",
         "invalid_test_id": "Bitte eine eindeutige Testkennung mit 1 bis 100 Zeichen eingeben.",
         "invalid_tag": "Maximal 255 Zeichen und keine Steuerzeichen verwenden.",
         "duplicate_identity": "Für diese Identität besteht bereits ein Profil.",
         "duplicate_tag": "Dieser NFC-Tag ist bereits einem anderen Profil zugeordnet.",
         "invalid_height": "Die Höhe muss zwischen 50 und 140 cm liegen.",
         "height_order": "Die Sitzhöhe muss kleiner als die Stehhöhe sein."}
        if german else
        {"invalid_name": "Enter a name with 1 to 100 characters.",
         "invalid_uuid": "Enter a valid, nonzero Microsoft ID in UUID format.",
         "invalid_test_id": "Enter a unique test identifier with 1 to 100 characters.",
         "invalid_tag": "Use at most 255 characters and no control characters.",
         "duplicate_identity": "A profile for this identity already exists.",
         "duplicate_tag": "This NFC tag is already assigned to another profile.",
         "invalid_height": "Height must be between 50 and 140 cm.",
         "height_order": "Sitting height must be less than standing height."}
    )
    create_description = (
        "Für echte Mitarbeiter die Mandanten-ID und die unveränderliche Benutzer-Objekt-ID aus Microsoft Entra eingeben (keine E-Mail-Adresse). Die Identität wird hier nur zugeordnet, noch nicht bei Microsoft überprüft. Für einen Test das Testprofil aktivieren und eine frei gewählte Testkennung eintragen; die Mandanten-ID bleibt dann leer. Höhen anschließend am Gerät einstellen. NFC-Tag-ID exakt wie beim Leser eingeben."
        if german else
        "For real employees, enter the tenant ID and immutable user object ID from Microsoft Entra (not an email address). The identity is only mapped locally, not yet verified with Microsoft. For testing, enable test profile and enter a fictitious test identifier; leave tenant ID empty. Set heights on the device afterwards. Enter NFC tag IDs exactly as reported by the reader."
    )
    edit_description = (
        "Name, Freigabe und NFC-Zuordnung ändern. Das NFC-Feld leeren, um die Zuordnung zu entfernen. Die Microsoft-Identität bleibt unverändert; Höhen werden am Gerät bearbeitet. Ein deaktiviertes Profil bleibt bearbeitbar und gespeichert."
        if german else
        "Change name, active status and NFC assignment. Clear the NFC field to remove the assignment. Microsoft identity stays fixed; edit heights on the device. A disabled profile remains editable and stored."
    )
    result = {
        "title": "Desk Booking",
        "config": {"step": {"user": {
            "title": "Desk Booking",
            "description": (
                "Lokale Mitarbeiterprofile in Home Assistant verwalten. Nach dem Anlegen über 'Mitarbeiter hinzufügen' die Profile erfassen. Version 0.1: keine Places-Anbindung, keine Buchungsprüfung, kein NFC-Check-in und keine Tischbewegung."
                if german else
                "Manage local employee profiles in Home Assistant. After setup, use 'Add employee' to create profiles. Version 0.1: no Places connection, booking verification, NFC check-in or desk movement."
            )}}, "abort": {"already_configured": "Desk Booking ist bereits eingerichtet." if german else "Desk Booking is already configured."}},
        "config_subentries": {"employee": {
            "entry_type": "Mitarbeiter" if german else "Employee",
            "initiate_flow": {"user": "Mitarbeiter hinzufügen" if german else "Add employee",
                              "reconfigure": "Profil bearbeiten" if german else "Edit profile"},
            "step": {
                "user": {"title": "Mitarbeiter hinzufügen" if german else "Add employee",
                         "description": create_description, "data": labels},
                "reconfigure": {"title": "Profil bearbeiten" if german else "Edit profile",
                                "description": edit_description,
                                "data": {k: labels[k] for k in ("name", "nfc_tag_id", "active")}},
            },
            "error": errors,
            "abort": {"reconfigure_successful": "Profil aktualisiert." if german else "Profile updated.",
                      "already_configured": errors["duplicate_identity"]},
        }},
        "entity": {
            "number": {"sitting_height": {"name": "Sitzhöhe" if german else "Sitting height"},
                       "standing_height": {"name": "Stehhöhe" if german else "Standing height"}},
            "switch": {"active": {"name": "Profil aktiv" if german else "Profile active"}},
        },
        "exceptions": {k: {"message": errors[k]} for k in ("height_order", "invalid_height")},
    }
    result["config"]["step"]["user"]["description"] = (
        "Mitarbeiter und Tische lokal verwalten. Check-in ohne Reservierung oder Microsoft-Verbindung. Es werden nur Displayfavoriten übertragen; keine Tischbewegung."
        if german else "Manage employees and desks locally. Check in without reservations or a Microsoft connection. Only display favorites are transferred; no desk movement."
    )
    result["options"] = {
        "step": {"init": {"title": "Globale Anzeige" if german else "Global display settings",
                          "description": "Der Firmenname gilt für alle Schreibtische." if german else "The company name applies to every desk.",
                          "data": {"company_name": "Firmenname" if german else "Company name"}}},
        "error": {"invalid_company_name": "Maximal 60 Zeichen, keine Steuerzeichen." if german else "Use at most 60 characters and no control characters."},
    }
    desk_data = {"name": "Tischname" if german else "Desk name", "display_device": "Schreibtisch-Display" if german else "Desk display",
                 "display_name": "Anzeigename auf dem Display (leer = Tischname)" if german else "Display label (empty = desk name)",
                 "light_entities": "Dimmbare Lichter (bis zu vier, Reihenfolge = Displayseiten)" if german else "Dimmable lights (up to four, order = display pages)"}
    description = ("ESPHome-Display mit den Favoriten Sitzen und Stehen auswählen. Jeder Tisch erhält eine Mitarbeiterauswahl sowie Check-in und Auschecken. {detail}"
                   if german else "Select an ESPHome display with the sitting and standing favorites. Each desk gets an employee selector and check-in/out buttons. {detail}")
    result["config_subentries"]["desk"] = {
        "entry_type": "Tisch" if german else "Desk",
        "initiate_flow": {"user": "Tisch hinzufügen" if german else "Add desk", "reconfigure": "Tisch bearbeiten" if german else "Edit desk"},
        "step": {step: {"title": "Tisch einrichten" if german else "Set up desk", "description": description, "data": desk_data} for step in ("user", "reconfigure")},
        "error": {"invalid_desk": "Tischzuordnung prüfen. Details stehen oben." if german else "Check the desk mapping. See details above."},
    }
    result["entity"].update({
        "select": {"selected_employee": {"name": "Mitarbeiter für Check-in" if german else "Employee for check-in"}},
        "button": {"check_in": {"name": "Test-Check-in" if german else "Test check-in"}, "check_out": {"name": "Auschecken" if german else "Check out"}},
        "sensor": {"occupant": {"name": "Angemeldeter Mitarbeiter" if german else "Signed-in employee"},
                   "desk_status": {"name": "Belegung" if german else "Occupancy", "state": ({"free": "Frei", "applying": "Übertragung / Wiederherstellung ausstehend", "checked_in": "Eingecheckt", "error": "Übertragung fehlgeschlagen"} if german else {"free": "Free", "applying": "Transfer / recovery pending", "checked_in": "Checked in", "error": "Transfer failed"})}},
    })
    result["config_subentries"]["desk"]["step"]["lights"] = {
        "title": "Lichtnamen und Symbole" if german else "Light labels and icons",
        "description": ("Reihenfolge wie in der Lichtauswahl. Leerer Name übernimmt den Namen des Lichts. Die sechs Home-Assistant-Lichtsymbole sind offline im Display gespeichert. {detail}" if german else "Same order as the light selection. An empty label uses the light name. Six Home Assistant light icons are stored offline on the display. {detail}"),
        "data": {f"light_{slot}_{key}": (f"Licht {slot}: " + ("Anzeigename" if key == "name" else "Symbol")) if german else f"Light {slot}: {key}" for slot in range(1,5) for key in ("name", "icon")},
    }
    options = result["options"]["step"]["init"]
    result["options"]["error"]["invalid_display_setting"] = "Wert außerhalb des erlaubten Bereichs." if german else "Value outside the permitted range."
    options["description"] = ("Zentrale Vorgaben für alle zugeordneten Displays. Geräte können weiterhin einzeln bedient werden." if german else "Central defaults for all mapped displays. Individual device controls remain available.")
    options["data"].update({key: de if german else en for key, de, en in (
        ("display_brightness", "Display-Helligkeit", "Display brightness"),
        ("standby_brightness", "Standby-Helligkeit", "Standby brightness"),
        ("standby_timeout", "Standby nach Sekunden (0 = deaktiviert)", "Standby delay in seconds (0 = disabled)"),
        ("standby_home", "Bei Standby zur Check-in-Seite wechseln", "Return to check-in page on standby"))})
    steps = result["config_subentries"]["desk"]["step"]
    steps.pop("lights", None)
    desk_data.pop("light_entities", None)
    for slot in range(1, 5):
        for key, de, en in (("entity", "Entität", "Entity"), ("name", "Anzeigename", "Display name"), ("icon", "Symbol", "Icon")):
            desk_data[f"light_{slot}_{key}"] = f"Licht {slot}: {de}" if german else f"Light {slot}: {en}"
    desk_data.update({key: de if german else en for key, de, en in (
        ("cover_entity", "Rollo / Jalousie", "Cover / blind"),
        ("cover_name", "Rollo / Jalousie: Anzeigename", "Cover: display name"),
        ("switch_entity", "Schaltkanal", "Switch channel"),
        ("switch_name", "Schaltkanal: Anzeigename", "Switch: display name"),
        ("switch_icon", "Schaltkanal: Symbol", "Switch: icon"))})
    return result


def main():
    (COMPONENT / "translations").mkdir(exist_ok=True)
    for path, content in ((COMPONENT / "strings.json", translations()),
                          (COMPONENT / "translations/en.json", translations()),
                          (COMPONENT / "translations/de.json", translations(True))):
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    release = ROOT / "dist"
    release.mkdir(exist_ok=True)
    files = sorted(p for p in COMPONENT.rglob("*") if p.suffix in (".py", ".json", ".yaml"))
    version = json.loads((COMPONENT / "manifest.json").read_text())["version"]
    archive = release / f"desk-booking-{version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        for path in files:
            zipped.write(path, path.relative_to(ROOT).as_posix())
        zipped.write(ROOT / "README.md", "README.md")
        if (ROOT / "VERIFICATION.md").exists():
            zipped.write(ROOT / "VERIFICATION.md", "VERIFICATION.md")
        zipped.write(ROOT / "CONTROLS_030.md", "CONTROLS_030.md")
        zipped.write(ROOT / "TOUCH_AND_DIAGNOSTICS_040.md", "TOUCH_AND_DIAGNOSTICS_040.md")
        zipped.write(ROOT / "CENTRAL_CONTROLS_050.md", "CENTRAL_CONTROLS_050.md")
    bundle = {str(p.relative_to(COMPONENT).as_posix()): p.read_text(encoding="utf-8") for p in files}
    (release / "component-files.json").write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (release / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Built {archive.name}: {len(files)} component files, SHA256 {digest}")


if __name__ == "__main__":
    main()
