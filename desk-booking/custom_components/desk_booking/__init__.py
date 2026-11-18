"""Locally managed employee preferences for a future booking integration."""
from .records import ensure_categories, records


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import PLATFORMS, PROFILE, update_signal
from .desk import DeskManager
from .dimmer import DeskDimmer
from .fleet import DisplayFleet
from .m365 import DirectorySync
from .booking_sync import BookingSync
from .checkout_schedule import CheckoutSchedule
from .mail import MailManager
from .mail_model import email, template
from homeassistant.exceptions import ServiceValidationError
from .floorplan import async_setup_floorplan, unload_floorplan
import voluptuous as vol
from homeassistant.helpers import config_validation as cv


def _structure(entry: ConfigEntry) -> tuple:
    return tuple((p.subentry_id, p.title, p.data.get("display_device"), tuple(p.data.get("light_entities", [])),
                  p.data.get("cover_entity"), p.data.get("switch_entity")) for p in records(entry).values() if p.subentry_type != PROFILE)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ensure_categories(hass, entry)
    entry.runtime_data = DeskManager(hass, entry, _structure(entry))
    entry.runtime_data.fleet = DisplayFleet(hass, entry)
    entry.runtime_data.directory = DirectorySync(hass, entry)
    entry.runtime_data.bookings = BookingSync(hass, entry)
    entry.runtime_data.checkout_schedule = CheckoutSchedule(hass, entry)
    entry.runtime_data.mail = MailManager(hass, entry)
    await entry.runtime_data.mail.start()
    await async_setup_floorplan(hass, entry)
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.runtime_data.dimmer = DeskDimmer(hass, entry)
    entry.runtime_data.dimmer.start()
    entry.runtime_data.fleet.start()
    async def notify(call):
        await entry.runtime_data.fleet.notify(call.data["message"], call.data["priority"], call.data["duration"], call.context)
    async def checkout(call):
        await entry.runtime_data.fleet.checkout_all(call.context)
    hass.services.async_register("desk_booking", "notify_all", notify, schema=vol.Schema({
        vol.Required("message"): vol.All(cv.string, vol.Length(min=1, max=255)),
        vol.Optional("priority", default="3"): vol.In(["1", "2", "3"]),
        vol.Optional("duration", default=15): vol.All(vol.Coerce(int), vol.Range(min=1, max=300))}))
    hass.services.async_register("desk_booking", "checkout_all", checkout, schema=vol.Schema({}))
    async def sync(call):
        await entry.runtime_data.directory.sync()
    hass.services.async_register("desk_booking", "sync_m365", sync, schema=vol.Schema({}))
    async def sync_bookings(call):
        await entry.runtime_data.bookings.sync()
    hass.services.async_register("desk_booking", "sync_bookings", sync_bookings, schema=vol.Schema({}))
    async def send_email(call):
        user = await hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
        if call.context.user_id and (not user or not user.is_admin):
            raise ServiceValidationError('Nur Administratoren dürfen E-Mails versenden.')
        try:
            subject = call.data['subject']
            if any(ord(c)<32 for c in subject):
                raise ValueError('Ungültiger Betreff')
            await entry.runtime_data.mail.send(email(call.data['recipient']), subject, call.data['message'])
            await entry.runtime_data.mail.save()
        except (ValueError, OSError) as err:
            raise ServiceValidationError('Adresse, Betreff oder Speicher prüfen.') from err
    hass.services.async_register('desk_booking','send_email',send_email,schema=vol.Schema({
        vol.Required('recipient'):cv.string,vol.Required('subject'):vol.All(cv.string,vol.Length(min=1,max=255)),
        vol.Required('message'):vol.All(cv.string,vol.Length(min=1,max=10000))}))
    await entry.runtime_data.directory.start()
    await entry.runtime_data.bookings.start()
    await entry.runtime_data.checkout_schedule.start()
    return True


async def _async_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    if getattr(entry.runtime_data, "reload_pending", False):
        return
    if (entry.runtime_data.structure != _structure(entry)
            or entry.runtime_data.bookings.interval != entry.options.get("booking_interval", 5)
            or entry.runtime_data.checkout_schedule.time != entry.options.get('daily_checkout_time', '00:00')
            or entry.runtime_data.directory.config != entry.data.get("m365", {})):
        # Add/remove/rename affects platforms and device registry names.
        runtime = entry.runtime_data
        runtime.reload_pending = True
        try:
            await hass.config_entries.async_reload(entry.entry_id)
        finally:
            runtime.reload_pending = False
    else:
        # Value edits must not reload all employee entities.
        async_dispatcher_send(hass, update_signal(entry.entry_id))
        await entry.runtime_data.fleet.settings_updated()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        unload_floorplan(hass, entry)
        await entry.runtime_data.checkout_schedule.stop()
        await entry.runtime_data.bookings.stop()
        await entry.runtime_data.directory.stop()
        await entry.runtime_data.dimmer.stop()
        await entry.runtime_data.fleet.stop()
        hass.services.async_remove("desk_booking", "notify_all")
        hass.services.async_remove("desk_booking", "checkout_all")
        hass.services.async_remove("desk_booking", "sync_m365")
        hass.services.async_remove("desk_booking", "sync_bookings")
        hass.services.async_remove('desk_booking','send_email')
        return True
    return False


async def async_migrate_entry(hass, entry):
    if entry.version > 2:
        return False
    if entry.version == 1:
        ensure_categories(hass, entry)
        hass.config_entries.async_update_entry(entry, version=2)
    return True
