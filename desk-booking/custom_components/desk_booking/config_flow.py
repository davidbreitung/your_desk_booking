"""UI setup, employee creation and employee reconfiguration."""
from .records import records, records_of_type, update_record


import voluptuous as vol
import math
import re

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigSubentryFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, PROFILE, DESK, DISPLAY_DEFAULTS
from .profile import ProfileError, normalize_profile, profile_title, validate_unique
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .graph import GraphClient, GraphError, credentials
from .options_management import ManagementOptions


def m365_schema(current=None):
    current = current or {}
    return vol.Schema({
        vol.Required("tenant_id", default=current.get("tenant_id", "")): selector.TextSelector(),
        vol.Required("client_id", default=current.get("client_id", "")): selector.TextSelector(),
        vol.Optional("client_secret"): selector.TextSelector(selector.TextSelectorConfig(type="password")),
        vol.Required("sync_interval", default=current.get("sync_interval", 15)): selector.NumberSelector(
            selector.NumberSelectorConfig(min=5, max=1440, step=1, mode="box", unit_of_measurement="min")),
    })


async def validate_m365(hass, values, current=None):
    data = {**(current or {}), **values}
    if not values.get("client_secret") and current:
        data["client_secret"] = current.get("client_secret", "")
    data = credentials(data)
    # Changing tenants risks binding local identities to a different directory.
    if current and current.get("tenant_id") != data["tenant_id"]:
        raise GraphError("tenant_change_not_allowed")
    await GraphClient(async_get_clientsession(hass), data).test_connection()
    return data


class DeskBookingConfigFlow(ConfigFlow, domain=DOMAIN):
    """One local profile collection per HA instance."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            try:
                data = await validate_m365(self.hass, user_input)
            except GraphError as err:
                errors["base"] = err.code
            else:
                return self.async_create_entry(title="Desk Booking", data={"m365": data})
        return self.async_show_form(step_id="user", data_schema=m365_schema(), errors=errors)

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry):
        # HA 2026.11 exposes an Add button for every registered subentry flow.
        # Cloud-only records use the options flow for edits; no creation flows.
        return {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DeskBookingOptionsFlow()


class DeskBookingOptionsFlow(ManagementOptions, OptionsFlow):
    async def async_step_init(self, user_input=None):
        return self.async_show_menu(step_id="init", menu_options=["display", "m365", "bookings", "desk", "employee", "objects", "mail", "floorplan", "manuals"])

    async def async_step_bookings(self, user_input=None):
        errors = {}
        if user_input is not None:
            value = user_input.get("booking_interval", 5)
            checkout_time = user_input.get('daily_checkout_time', self.config_entry.options.get('daily_checkout_time', '00:00'))
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or int(value) != value or not 1 <= value <= 1440:
                errors["base"] = "invalid_booking_interval"
            elif not isinstance(checkout_time, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', checkout_time):
                errors['base'] = 'invalid_checkout_time'
            else:
                return self.async_create_entry(title="", data={**self.config_entry.options, "booking_interval": int(value), 'daily_checkout_time':checkout_time})
        return self.async_show_form(step_id="bookings", errors=errors, data_schema=vol.Schema({
            vol.Required("booking_interval", default=self.config_entry.options.get("booking_interval", 5)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=1440, step=1, mode="box", unit_of_measurement="min")),
            vol.Required('daily_checkout_time', default=self.config_entry.options.get('daily_checkout_time', '00:00')): selector.TextSelector()}))

    async def _choose_record(self, kind, step, user_input):
        records = [r for r in records_of_type(self.config_entry, kind) if not r.data.get('hidden')]
        if not records:
            return self.async_abort(reason="no_synced_records")
        if user_input is not None:
            chosen = next((p for p in records if p.subentry_id == user_input.get("record")), None)
            if chosen:
                self._selected_id = chosen.subentry_id
                return await getattr(self, f"async_step_{step}_edit")()
        return self.async_show_form(step_id=step, data_schema=vol.Schema({
            vol.Required("record"): selector.SelectSelector(selector.SelectSelectorConfig(
                options=[{"value": p.subentry_id, "label": f"{p.title} ({p.subentry_id[-6:]})"} for p in records], mode="dropdown"))}))

    async def async_step_desk(self, user_input=None):
        return await self._choose_record(DESK, "desk", user_input)

    async def async_step_employee(self, user_input=None):
        return await self._choose_record(PROFILE, "employee", user_input)

    def _get_entry(self):
        return self.config_entry

    def _get_reconfigure_subentry(self):
        return records(self.config_entry)[self._selected_id]

    def async_update_and_abort(self, entry, current, **updates):
        update_record(self.hass, entry, current, **updates)
        return self.async_create_entry(title="", data=dict(entry.options))

    async def async_step_desk_edit(self, user_input=None):
        return await DeskSubentryFlow._step(self, "desk_edit", user_input)

    async def async_step_employee_edit(self, user_input=None):
        return await EmployeeSubentryFlow._async_profile_step(self, "employee_edit", user_input)

    async def async_step_m365(self, user_input=None):
        current = self.config_entry.data.get("m365", {})
        errors = {}
        if user_input is not None:
            try:
                data = await validate_m365(self.hass, user_input, current)
            except GraphError as err:
                errors["base"] = err.code
            else:
                self.hass.config_entries.async_update_entry(self.config_entry,
                    data={**self.config_entry.data, "m365": data})
                return self.async_create_entry(title="", data=dict(self.config_entry.options))
        return self.async_show_form(step_id="m365", data_schema=m365_schema(current), errors=errors)

    async def async_step_display(self, user_input=None):
        errors = {}
        if user_input is not None:
            company = user_input["company_name"].strip()
            if len(company) > 60 or any(ord(c) < 32 for c in company):
                errors["company_name"] = "invalid_company_name"
            for key, minimum, maximum in (("display_brightness", 1, 100), ("standby_brightness", 0, 100), ("standby_timeout", 0, 3600)):
                value = user_input.get(key, DISPLAY_DEFAULTS[key])
                if not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
                    errors[key] = "invalid_display_setting"
            if not errors:
                return self.async_create_entry(title="", data={**self.config_entry.options, **user_input, "company_name": company})
        fields = {
            vol.Required("company_name", default=self.config_entry.options.get("company_name", "your-admins")): selector.TextSelector(),
        }
        for key, maximum, minimum in (("display_brightness", 100, 1), ("standby_brightness", 100, 0), ("standby_timeout", 3600, 0)):
            fields[vol.Required(key, default=self.config_entry.options.get(key, DISPLAY_DEFAULTS[key]))] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=minimum, max=maximum, step=1, mode="box", unit_of_measurement="s" if key == "standby_timeout" else "%"))
        fields[vol.Required("standby_home", default=self.config_entry.options.get("standby_home", False))] = selector.BooleanSelector()
        return self.async_show_form(step_id="display", data_schema=vol.Schema(fields), errors=errors)


from .config_desk import DeskSubentryFlow


class EmployeeSubentryFlow(ConfigSubentryFlow):
    """Identity is fixed at creation; name, NFC assignment and status are editable."""

    async def async_step_user(self, user_input=None):
        return self.async_abort(reason="managed_by_m365")

    async def async_step_reconfigure(self, user_input=None):
        return await self._async_profile_step("reconfigure", user_input)

    async def _async_profile_step(self, step, user_input):
        entry = self._get_entry()
        current = self._get_reconfigure_subentry() if step != "user" else None
        errors = {}
        if user_input is not None:
            try:
                # Read current stored heights on submission, not on form opening.
                # A number edit made while this form is open is preserved.
                merged = dict(current.data) if current else {}
                merged.update({"nfc_tag_id": user_input.get("nfc_tag_id", "")})
                if current:
                    for key in ("test_profile", "tenant_id", "object_id"):
                        merged[key] = current.data[key]
                data = normalize_profile(merged)
                validate_unique(data, records_of_type(entry, PROFILE),
                                current.subentry_id if current else None)
            except ProfileError as err:
                errors[err.field] = err.code
            else:
                if current:
                    # Our update listener handles changes, so never request a
                    # second reload through async_update_reload_and_abort.
                    return self.async_update_and_abort(
                        entry, current, data=data, title=profile_title(data)
                    )
        suggestions = dict(current.data) if current else {}
        if user_input:
            suggestions.update(user_input)
        return self.async_show_form(
            step_id=step,
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({vol.Optional("nfc_tag_id", default=""): selector.TextSelector()}), suggestions
            ),
            errors=errors,
        )
