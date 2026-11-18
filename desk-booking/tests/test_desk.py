"""Transaction tests with a simulated HA state/service boundary, no hardware."""
import asyncio
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "desk_booking"
package = ModuleType("desk_transaction_tests")
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package


class HAError(Exception):
    pass


class ValidationError(HAError):
    pass


registry = SimpleNamespace(async_get=lambda hass: hass.registry,
                           async_entries_for_device=lambda registry, device: [e for e in registry if e.device_id == device])
modules = {
    "homeassistant": ModuleType("homeassistant"),
    "homeassistant.exceptions": SimpleNamespace(HomeAssistantError=HAError, ServiceValidationError=ValidationError),
    "homeassistant.helpers": SimpleNamespace(entity_registry=registry),
    "homeassistant.helpers.dispatcher": SimpleNamespace(async_dispatcher_send=lambda *a: None),
}
with patch.dict(sys.modules, modules):
    spec = importlib.util.spec_from_file_location(f"{package.__name__}.desk", ROOT / "desk.py")
    desk_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(desk_module)


def subentry(pid, kind, data):
    return SimpleNamespace(subentry_id=pid, subentry_type=kind, title=pid, data=data)


class DeskTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.desk = subentry("Desk", "desk", {"display_device": "display", "selected_profile": "Employee"})
        self.employee = subentry("Employee", "employee", {"name": "Profil-Anzeigename", "active": True, "sitting_height": 74.5, "standing_height": 113})
        self.entry = SimpleNamespace(entry_id="entry", subentries={"Desk": self.desk, "Employee": self.employee})
        self.entry.get_subentries_of_type = lambda kind: [s for s in self.entry.subentries.values() if s.subentry_type == kind]
        self.values = {"number.sit": SimpleNamespace(state="74", attributes={"min": 62, "max": 128, "step": 1}),
                       "number.stand": SimpleNamespace(state="110", attributes={"min": 62, "max": 128, "step": 1})}
        self.calls = []
        self.fail_count = 0
        async def call(domain, service, data, **kwargs):
            self.calls.append((domain, service, data))
            if self.fail_count:
                self.fail_count -= 1
                raise HAError("simulated device failure")
            self.values[data["entity_id"]].state = str(data["value"])
            await asyncio.sleep(0)
        self.hass = SimpleNamespace(data={}, registry=[
            SimpleNamespace(entity_id=eid, domain="number", platform="esphome", original_name=name,
                            disabled_by=None, unique_id=f"MAC/0/number/{name}", device_id="display")
            for eid, name in (("number.sit", "Favorit Sitzen"), ("number.stand", "Favorit Stehen"))],
            states=SimpleNamespace(get=self.values.get), services=SimpleNamespace(async_call=call),
            config_entries=SimpleNamespace(async_update_subentry=lambda entry, sub, data: setattr(sub, "data", data)))
        self.manager = desk_module.DeskManager(self.hass, self.entry, ())

    async def test_check_in_rounds_and_check_out_restores(self):
        await self.manager.check_in("Desk", None)
        self.assertEqual(self.desk.data["status"], "checked_in")
        self.assertEqual(self.values["number.sit"].state, "75.0")
        self.assertEqual(self.desk.data["occupant"], "Employee")
        await self.manager.check_out("Desk", None)
        self.assertEqual(self.desk.data["status"], "free")
        self.assertEqual(self.values["number.sit"].state, "74.0")
        self.assertTrue(all(call[:2] == ("number", "set_value") for call in self.calls))

    async def test_grouped_records_keep_transaction_stages_and_restore_heights(self):
        self.entry.data = {"records": {key: {"subentry_type": value.subentry_type,
            "unique_id": key, "title": value.title, "data": dict(value.data)}
            for key, value in self.entry.subentries.items()}}
        self.entry.subentries = {}
        self.hass.config_entries.async_update_entry = lambda entry, data: setattr(entry, "data", data)
        await self.manager.check_in("Desk", None)
        data = self.entry.data["records"]["Desk"]["data"]
        self.assertEqual(data["status"], "checked_in")
        self.assertEqual(data["occupant"], "Employee")
        self.assertEqual(data["previous"]["sitting_height"], 74)
        await self.manager.check_out("Desk", None)
        self.assertEqual(self.entry.data["records"]["Desk"]["data"]["status"], "free")
        self.assertEqual(self.values["number.sit"].state, "74.0")

    async def test_reservation_rejection_uses_red_animated_priority_without_height_writes(self):
        self.manager.bookings = SimpleNamespace(check_in_decision=AsyncMock(return_value=('reserved', None)))
        self.manager.fleet = SimpleNamespace(send_one=AsyncMock())
        with self.assertRaises(ValidationError): await self.manager.check_in('Desk',None)
        self.manager.fleet.send_one.assert_awaited_once_with('display','Bereits gebucht...','1',30,None)
        self.assertFalse(self.calls)

    async def test_replacement_keeps_original_restore_values_and_old_occupant_on_failure(self):
        self.desk.data.update(status='checked_in',occupant='Previous',previous={'sitting_height':70,'standing_height':105},applied={'sitting_height':74,'standing_height':110})
        self.manager.bookings = SimpleNamespace(check_in_decision=AsyncMock(return_value=('replace',None)),mark_attended=AsyncMock())
        self.fail_count=1
        with self.assertRaises(HAError): await self.manager.check_in('Desk',None)
        self.assertEqual(self.desk.data['occupant'],'Previous')
        self.assertEqual(self.desk.data['status'],'checked_in')
        await self.manager.check_in('Desk',None)
        self.assertEqual(self.desk.data['occupant'],'Employee')
        self.assertEqual(self.desk.data['previous']['sitting_height'],70)
        await self.manager.check_out('Desk',None)
        self.assertEqual(float(self.values['number.sit'].state),70.0)

    async def test_scheduled_retry_never_checks_out_a_replacement_occupant(self):
        self.desk.data.update(status='checked_in',occupant='New')
        await self.manager.check_out('Desk',None,expected_occupant='Old')
        self.assertEqual(self.desk.data['occupant'],'New')
        self.assertFalse(self.calls)

    async def test_inactive_profile_has_no_writes(self):
        self.employee.data["active"] = False
        with self.assertRaises(ValidationError):
            await self.manager.check_in("Desk", None)
        self.assertFalse(self.calls)

    async def test_imported_desk_without_display_or_inactive_has_no_writes(self):
        for changes in ({"display_device": None}, {"active": False}):
            self.desk.data = {"display_device": "display", "selected_profile": "Employee", **changes}
            with self.assertRaises(ValidationError):
                await self.manager.check_in("Desk", None)
            self.assertFalse(self.calls)

    async def test_missing_selection_has_no_writes(self):
        self.desk.data["selected_profile"] = "removed"
        with self.assertRaises(ValidationError):
            await self.manager.check_in("Desk", None)
        self.assertFalse(self.calls)

    async def test_range_rejected_without_clamping(self):
        self.employee.data["sitting_height"] = 55
        with self.assertRaises(ValidationError):
            await self.manager.check_in("Desk", None)
        self.assertFalse(self.calls)

    async def test_offline_display_has_no_writes(self):
        self.values["number.sit"].state = "unavailable"
        with self.assertRaises(ValidationError):
            await self.manager.check_in("Desk", None)
        self.assertFalse(self.calls)

    async def test_wrong_entity_rejected(self):
        self.hass.registry[0].unique_id = "MAC/0/number/Motor"
        with self.assertRaises(ValidationError):
            await self.manager.check_in("Desk", None)
        self.assertFalse(self.calls)

    async def test_double_check_in_serialized(self):
        result = await asyncio.gather(self.manager.check_in("Desk", None), self.manager.check_in("Desk", None), return_exceptions=True)
        self.assertEqual(sum(isinstance(r, ValidationError) for r in result), 1)
        self.assertEqual(len(self.calls), 2)

    async def test_employee_cannot_occupy_two_desks(self):
        self.entry.subentries["Other"] = subentry("Other", "desk", {"occupant": "Employee", "status": "checked_in"})
        with self.assertRaises(ValidationError):
            await self.manager.check_in("Desk", None)
        self.assertFalse(self.calls)

    async def test_transfer_failure_restores(self):
        self.fail_count = 1
        with self.assertRaises(HAError):
            await self.manager.check_in("Desk", None)
        self.assertEqual(self.desk.data["status"], "free")
        self.assertEqual(self.values["number.sit"].state, "74.0")

    async def test_rollback_failure_remains_blocked_until_checkout(self):
        self.fail_count = 2
        with self.assertRaises(HAError):
            await self.manager.check_in("Desk", None)
        self.assertEqual(self.desk.data["status"], "error")
        # New manager simulates reload: session and lock remain intact.
        manager = desk_module.DeskManager(self.hass, self.entry, ())
        self.assertIs(manager.lock, self.manager.lock)
        await manager.check_out("Desk", None)
        self.assertEqual(self.desk.data["status"], "free")

    async def test_checkout_failure_does_not_free_desk(self):
        await self.manager.check_in("Desk", None)
        self.fail_count = 1
        with self.assertRaises(HAError):
            await self.manager.check_out("Desk", None)
        self.assertEqual(self.desk.data["status"], "error")
        self.assertEqual(self.desk.data["occupant"], "Employee")

    async def test_interrupted_transfer_recoverable(self):
        self.desk.data.update(status="applying", occupant="Employee", previous={"sitting_height": 74, "standing_height": 110})
        await self.manager.check_out("Desk", None)
        self.assertEqual(self.desk.data["status"], "free")


if __name__ == "__main__":
    unittest.main()
