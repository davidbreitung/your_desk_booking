"""Single-page desk, light, cover and switch configuration."""
from .records import records_of_type

import voluptuous as vol
from homeassistant.config_entries import ConfigSubentryFlow
from homeassistant.helpers import selector
from homeassistant.exceptions import ServiceValidationError
from .const import DESK, SWITCH_ICONS
from .desk import display_targets
from .dimmer import validate_light
from .light_options import LIGHT_ICONS, DEFAULT_LIGHT_ICON


def text(value):
    value = str(value or "").strip()
    if len(value) > 60 or any(ord(c) < 32 for c in value):
        raise ServiceValidationError("Anzeigenamen: maximal 60 Zeichen, keine Steuerzeichen.")
    return value


def icon_selector(icons):
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=[{"value": k, "label": v} for k, v in icons.items()], mode="dropdown"))


class DeskSubentryFlow(ConfigSubentryFlow):
    async def async_step_user(self, user_input=None):
        return self.async_abort(reason="managed_by_m365")

    async def async_step_reconfigure(self, user_input=None):
        return await self._step("reconfigure", user_input)

    async def _step(self, step, user_input):
        entry = self._get_entry()
        current = self._get_reconfigure_subentry() if step != "user" else None
        previous = dict(current.data) if current else {}
        errors, detail = {}, ""
        if user_input is not None:
            try:
                name = text(user_input["name"])
                if not name:
                    raise ServiceValidationError("Bitte einen Tischnamen eingeben.")
                device = user_input.get("display_device")
                if not device and previous.get("source") != "places":
                    raise ServiceValidationError("Bitte ein Display auswählen.")
                if current and previous.get("status", "free") != "free" and device != previous.get("display_device"):
                    raise ServiceValidationError("Vor einem Displaywechsel zuerst auschecken.")
                if device:
                    display_targets(self.hass, device)
                if device and any(d != current and d.data.get("display_device") == device for d in records_of_type(entry, DESK)):
                    raise ServiceValidationError("Dieses Display ist bereits zugeordnet.")
                lights, details = [], {}
                for slot in range(1, 5):
                    light = user_input.get(f"light_{slot}_entity")
                    if not light:
                        continue
                    if light in lights:
                        raise ServiceValidationError("Ein Licht darf nur einmal zugeordnet werden.")
                    validate_light(self.hass, light, device)
                    icon = user_input.get(f"light_{slot}_icon", DEFAULT_LIGHT_ICON)
                    if icon not in LIGHT_ICONS:
                        raise ServiceValidationError("Ungültiges Lichtsymbol.")
                    lights.append(light)
                    details[light] = {"name": text(user_input.get(f"light_{slot}_name")), "icon": icon}
                cover, switch = user_input.get("cover_entity"), user_input.get("switch_entity")
                if cover:
                    state = self.hass.states.get(cover)
                    if not cover.startswith("cover.") or not state or not int(state.attributes.get("supported_features", 0)) & 4:
                        raise ServiceValidationError("Rollo/Jalousie muss eine Positionssteuerung unterstützen.")
                if switch:
                    from homeassistant.helpers import entity_registry as er
                    registered = er.async_get(self.hass).async_get(switch)
                    if not switch.startswith("switch.") or not self.hass.states.get(switch) or (device and registered and registered.device_id == device):
                        raise ServiceValidationError("Bitte einen externen Schaltkanal auswählen.")
                switch_icon = user_input.get("switch_icon", "mdi:power")
                if switch_icon not in SWITCH_ICONS:
                    raise ServiceValidationError("Ungültiges Schaltsymbol.")
                data = {**(current.data if current else {}), "name": name, "display_device": device,
                        "display_name": text(user_input.get("display_name")) or name,
                        "light_entities": lights, "light_details": details,
                        "cover_entity": cover, "cover_name": text(user_input.get("cover_name")),
                        "switch_entity": switch, "switch_name": text(user_input.get("switch_name")), "switch_icon": switch_icon}
                if current:
                    return self.async_update_and_abort(entry, current, data=data, title=name,
                        unique_id=current.unique_id if previous.get("source") == "places" else f"desk:{device}")
                return self.async_create_entry(title=name, data=data, unique_id=f"desk:{device}")
            except ServiceValidationError as err:
                errors["base"], detail = "invalid_desk", str(err)
        fields = {vol.Required("name"): selector.TextSelector(),
                  (vol.Optional if previous.get("source") == "places" else vol.Required)("display_device"): selector.DeviceSelector(selector.DeviceSelectorConfig(integration="esphome")),
                  vol.Optional("display_name", default=""): selector.TextSelector()}
        suggestions = dict(previous)
        for slot in range(1, 5):
            fields[vol.Optional(f"light_{slot}_entity")] = selector.EntitySelector(selector.EntitySelectorConfig(domain="light"))
            fields[vol.Optional(f"light_{slot}_name", default="")] = selector.TextSelector()
            fields[vol.Required(f"light_{slot}_icon", default=DEFAULT_LIGHT_ICON)] = icon_selector(LIGHT_ICONS)
            lights = previous.get("light_entities", [])
            if slot <= len(lights):
                light = lights[slot-1]
                details = previous.get("light_details", {}).get(light, {})
                suggestions.update({f"light_{slot}_entity": light, f"light_{slot}_name": details.get("name", ""),
                                    f"light_{slot}_icon": details.get("icon", DEFAULT_LIGHT_ICON)})
        fields.update({vol.Optional("cover_entity"): selector.EntitySelector(selector.EntitySelectorConfig(domain="cover")),
                       vol.Optional("cover_name", default=""): selector.TextSelector(),
                       vol.Optional("switch_entity"): selector.EntitySelector(selector.EntitySelectorConfig(domain="switch")),
                       vol.Optional("switch_name", default=""): selector.TextSelector(),
                       vol.Required("switch_icon", default="mdi:power"): icon_selector(SWITCH_ICONS)})
        return self.async_show_form(step_id=step,
            data_schema=self.add_suggested_values_to_schema(vol.Schema(fields), user_input if user_input is not None else suggestions),
            errors=errors, description_placeholders={"detail": detail})
