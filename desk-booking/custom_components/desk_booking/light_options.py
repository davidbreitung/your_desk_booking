"""Small offline MDI set shared with the desk firmware."""
LIGHT_ICONS = {
    "mdi:lightbulb-outline": "Glühbirne",
    "mdi:spotlight-beam": "Deckenspot",
    "mdi:led-strip-variant": "LED-Band",
    "mdi:ceiling-light": "Deckenleuchte",
    "mdi:floor-lamp": "Stehlampe",
    "mdi:desk-lamp": "Schreibtischlampe",
}
DEFAULT_LIGHT_ICON = "mdi:lightbulb-outline"


def normalize_light_details(lights, values, existing):
    result = dict(existing)
    for slot, entity in enumerate(lights, 1):
        previous = existing.get(entity, {})
        name = values.get(f"light_{slot}_name", previous.get("name", "")).strip()
        icon = values.get(f"light_{slot}_icon", previous.get("icon", DEFAULT_LIGHT_ICON))
        if len(name) > 60 or any(ord(c) < 32 for c in name):
            raise ValueError("Lichtnamen: maximal 60 Zeichen, keine Steuerzeichen.")
        if icon not in LIGHT_ICONS:
            raise ValueError("Bitte eines der unterstützten Licht-Symbole auswählen.")
        result[entity] = {"name": name, "icon": icon}
    return result
