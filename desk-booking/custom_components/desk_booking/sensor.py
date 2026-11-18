"""Desk occupancy and signed-in employee."""
from .records import records, records_of_type, category_id

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from .const import DESK, PROFILE, GROUP, ROOM, update_signal
from datetime import datetime
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from .entity import EmployeeEntity, CentralEntity
from .light_options import DEFAULT_LIGHT_ICON

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([DirectoryStatus(entry, "m365_sync", "Microsoft 365 Synchronisierung")])
    async_add_entities([BookingHealth(entry, "booking_sync", "Buchungen Synchronisierung")])
    async_add_entities([DailyCheckoutHealth(entry, 'daily_checkout', 'Tägliches Auschecken')])
    async_add_entities([MailStatus(entry, 'mail_status', 'E-Mail-Versand')])
    known = set()
    @callback
    def add_profiles():
        for record in records(entry).values():
            key = ('email', record.subentry_id)
            if key not in known:
                known.add(key)
                async_add_entities([ObjectEmail(entry, record, 'email')], config_subentry_id=category_id(entry, record))
        for profile in records_of_type(entry, PROFILE):
            if profile.subentry_id not in known:
                known.add(profile.subentry_id)
                async_add_entities([EmployeeStatus(entry, profile, "directory_status")], config_subentry_id=category_id(entry, profile))
    entry.async_on_unload(async_dispatcher_connect(hass, update_signal(entry.entry_id), add_profiles))
    add_profiles()
    for desk in records_of_type(entry, DESK):
        async_add_entities([DeskStatus(entry, desk, "desk_status"), DeskOccupant(entry, desk, "occupant"),
            NextBooking(entry, desk, "next_booking"), BookingEmployee(entry, desk, "booking_employee")], config_subentry_id=category_id(entry, desk))
    for group in records_of_type(entry, GROUP):
        async_add_entities([GroupStatus(entry, group, "group_status")], config_subentry_id=category_id(entry, group))
    for room in records_of_type(entry, ROOM):
        async_add_entities([RoomStatus(entry, room, "room_status"),
            NextBooking(entry, room, "next_booking"), BookingEmployee(entry, room, "booking_employee"),
            CurrentRoomBooking(entry, room, "current_booking"), CurrentRoomEmployee(entry, room, "current_booking_employee")],
            config_subentry_id=category_id(entry, room))


class ObjectEmail(EmployeeEntity, SensorEntity):
    _attr_name = 'E-Mail-Adresse'
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.profile.get('mail') or self.profile.get('places_email') or None


class MailStatus(CentralEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.entry.runtime_data.mail.state
    @property
    def extra_state_attributes(self):
        mail = self.entry.runtime_data.mail
        return {'last_accepted':mail.last_accepted,'error':mail.error,
                'accepted_count':sum(v.get('state') == 'accepted' for v in mail.history.values()),
                'uncertain_count':sum(v.get('state') in ('pending','mail_delivery_unknown') for v in mail.history.values()),
                'note':'accepted bedeutet von Microsoft angenommen, nicht bestätigt zugestellt'}


class DailyCheckoutHealth(CentralEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.entry.runtime_data.checkout_schedule.state

    @property
    def extra_state_attributes(self):
        schedule = self.entry.runtime_data.checkout_schedule
        return {'time':schedule.time,'timezone':str(self.hass.config.time_zone),
                'pending_desks':len(schedule.data.get('pending', {})),
                'last_due_day':schedule.data.get('last_due_day')}


class GroupStatus(EmployeeEntity, SensorEntity):
    _attr_name = "Gruppenstatus"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return "active" if self.profile.get("active") else "inactive"

    @property
    def extra_state_attributes(self):
        return {"entra_object_id": self.profile.get("object_id"), "direct_members": len(self.profile.get("member_ids", []))}


class BookingHealth(CentralEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.entry.runtime_data.bookings.state

    @property
    def extra_state_attributes(self):
        sync = self.entry.runtime_data.bookings
        return {"interval_minutes": sync.interval,
                "failed_desks": sum(d.subentry_id in sync.errors for d in records_of_type(self.entry, DESK)),
                "failed_rooms": sum(r.subentry_id in sync.errors for r in records_of_type(self.entry, ROOM)),
                "inactive_desks": sum(not d.data.get("active", True) for d in records_of_type(self.entry, DESK)),
                "inactive_rooms": sum(not r.data.get("active", True) for r in records_of_type(self.entry, ROOM)),
                "lookahead_days": 365,
                'errors':sorted(set(sync.errors.values())),
                'no_show_releases':sum(v.get('no_show_releases', 0) for v in sync.cache.values())}


class NextBooking(EmployeeEntity, SensorEntity):
    _attr_name = "Nächste Buchung"
    _attr_entity_category = None
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def booking(self):
        return self.entry.runtime_data.bookings.info(self.subentry_id)

    @property
    def native_value(self):
        event = self.booking["event"]
        return datetime.fromisoformat(event["start"]) if event else None

    @property
    def extra_state_attributes(self):
        info = self.booking
        event = info["event"] or {}
        return {"end": event.get("end"), "booked_by": info["name"],
                "reservation_active": bool(info["active_event"] and info["fresh"]),
                "active_reservation_end": (info["active_event"] or {}).get("end"),
                "active_reservation_booked_by": info["active_name"],
                "entra_object_id": event.get("booker_object_id"), "identity_status": event.get("identity_status"),
                "employee_subentry_id": info["employee_subentry_id"], "employee_device_id": info["employee_device_id"],
                "employee_entity_id": info["employee_entity_id"],
                "employee_url": f"/config/devices/device/{info['employee_device_id']}" if info["employee_device_id"] else None,
                "minutes_until_start": info["minutes"], "display_time": info["label"],
                "warning": info["warning"] and info["fresh"], "data_current": info["fresh"],
                "last_success": info["last_success"], "error": info["error"], "search_until": info["window_end"]}


class BookingEmployee(NextBooking):
    _attr_name = "Gebucht durch"
    _attr_device_class = None

    @property
    def native_value(self):
        return self.booking["name"] or "—"


class CurrentRoomBooking(NextBooking):
    _attr_name = "Aktuelle Buchung"

    @property
    def booking(self):
        return self.entry.runtime_data.bookings.info(self.subentry_id, current=True)


class CurrentRoomEmployee(CurrentRoomBooking):
    _attr_name = "Aktuell gebucht durch"
    _attr_device_class = None

    @property
    def native_value(self):
        return self.booking["name"] or "—"


class RoomStatus(EmployeeEntity, SensorEntity):
    _attr_name = "Raumstatus"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return "active" if self.profile.get("active") else "inactive"

    @property
    def extra_state_attributes(self):
        info = self.entry.runtime_data.bookings.info(self.subentry_id)
        return {"data_current": info["fresh"], "last_success": info["last_success"], "error": info["error"]}


class DeskStatus(EmployeeEntity, SensorEntity):
    _attr_entity_category = None
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["free", "applying", "checked_in", "error"]

    @property
    def native_value(self):
        return self.profile.get("status", "free")

    @property
    def extra_state_attributes(self):
        lights = self.profile.get("light_entities", [])
        labels = {}
        for slot in range(1, 5):
            entity_id = lights[slot - 1] if slot <= len(lights) else None
            state = self.hass.states.get(entity_id) if entity_id else None
            details = self.profile.get("light_details", {}).get(entity_id, {})
            labels[f"light_{slot}_name"] = (details.get("name") or (state.name if state else entity_id)) if entity_id else ""
            labels[f"light_{slot}_icon"] = details.get("icon", DEFAULT_LIGHT_ICON) if entity_id else ""
        cover_id = self.profile.get("cover_entity")
        cover = self.hass.states.get(cover_id) if cover_id else None
        switch_id = self.profile.get("switch_entity")
        switch = self.hass.states.get(switch_id) if switch_id else None
        return {"company_name": self.entry.options.get("company_name", "your-admins"),
                "source": self.profile.get("source", "local"),
                "active": self.profile.get("active", True),
                "display_configured": bool(self.profile.get("display_device")),
                "places_name": self.profile.get("places_name"),
                "places_type": self.profile.get("places_kind"),
                "places_mode": self.profile.get("places_mode"),
                "standby_home": self.entry.options.get("standby_home", False),
                "cover_name": (self.profile.get("cover_name") or (cover.name if cover else cover_id)) if cover_id else "",
                "cover_tilt": bool(cover and int(cover.attributes.get("supported_features", 0)) & 128),
                "cover_position": cover.attributes.get("current_position", -1) if cover else -1,
                "cover_tilt_position": cover.attributes.get("current_tilt_position", -1) if cover else -1,
                "cover_available": bool(cover and cover.state not in ("unknown", "unavailable")),
                "switch_name": (self.profile.get("switch_name") or (switch.name if switch else switch_id)) if switch_id else "",
                "switch_icon": self.profile.get("switch_icon", "mdi:power"),
                "switch_state": switch.state if switch else "unavailable",
                "display_name": self.profile.get("display_name", self.profile.get("name", "Arbeitsplatz")),
                **labels,
                "applied_sitting_height": self.profile.get("applied", {}).get("sitting_height"),
                "applied_standing_height": self.profile.get("applied", {}).get("standing_height")}


class DeskOccupant(EmployeeEntity, SensorEntity):
    _attr_entity_category = None

    @property
    def native_value(self):
        occupant = self.profile.get("occupant")
        profile = records(self.entry).get(occupant)
        return profile.data["name"] if profile else ("Profil entfernt" if occupant else "—")


class DirectoryStatus(CentralEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.entry.runtime_data.directory.state

    @property
    def extra_state_attributes(self):
        return self.entry.runtime_data.directory.status


class EmployeeStatus(EmployeeEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "M365-Status"
    @property
    def native_value(self):
        return "active" if self.profile.get("active") else "inactive"
