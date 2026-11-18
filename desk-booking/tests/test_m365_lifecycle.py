"""HA-boundary tests using explicit fakes (not a real HA runtime)."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from test_m365 import CONFIG, TENANT, USER, graph, profile

ROOT = Path(__file__).resolve().parents[1] / "custom_components/desk_booking"
pkg = ModuleType("m365_lifecycle_tests")
pkg.__path__ = [str(ROOT)]
sys.modules[pkg.__name__] = pkg


class Store:
    def __init__(self, *args):
        self.data = None
        self.fail = False
        self.on_save = None
    async def async_load(self):
        return deepcopy(self.data)
    async def async_save(self, data):
        if self.fail:
            raise OSError("synthetic disk failure")
        if self.on_save:
            self.on_save()
        self.data = deepcopy(data)


class Entry:
    entry_id = "entry"
    def __init__(self):
        self.data = {"m365": CONFIG}
        self.subentries = {}
    def get_subentries_of_type(self, kind):
        return [p for p in self.subentries.values() if p.subentry_type == kind]


class Subentry(SimpleNamespace):
    def __init__(self, **kwargs):
        kwargs.setdefault("subentry_id", "new")
        super().__init__(**kwargs)


registry = SimpleNamespace(async_get_device_by_identifier=lambda identifier, config_entry_id: None)
ha_modules = {
    "homeassistant": ModuleType("homeassistant"),
    "homeassistant.config_entries": SimpleNamespace(ConfigSubentry=Subentry),
    "homeassistant.helpers": SimpleNamespace(device_registry=SimpleNamespace(async_get=lambda hass: registry),
        entity_registry=SimpleNamespace(async_get=lambda hass: None, async_entries_for_config_entry=lambda *a: [])),
    "homeassistant.helpers.aiohttp_client": SimpleNamespace(async_get_clientsession=lambda hass: None),
    "homeassistant.helpers.dispatcher": SimpleNamespace(async_dispatcher_send=lambda *a: None),
    "homeassistant.helpers.event": SimpleNamespace(async_track_time_interval=lambda *a: lambda: None),
    "homeassistant.helpers.storage": SimpleNamespace(Store=Store),
    "homeassistant.util": SimpleNamespace(dt=SimpleNamespace(utcnow=lambda: datetime.now(timezone.utc))),
}
with patch.dict(sys.modules, ha_modules):
    module = importlib.import_module("m365_lifecycle_tests.m365")


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.entry = Entry()
        def update(entry, current, data, title):
            current.data, current.title = data, title
        def add(entry, subentry):
            entry.subentries[subentry.subentry_id] = subentry
        self.hass = SimpleNamespace(config_entries=SimpleNamespace(async_update_subentry=update, async_add_subentry=add),
                                    async_create_task=lambda coro, name: asyncio.create_task(coro))
        self.sync = module.DirectorySync(self.hass, self.entry)
        self.snapshot = {"tenant_id": TENANT, "client_id": USER, "users": {USER: {"id": USER, "displayName": "Employee", "accountEnabled": True, "userType": "Member"}},
                         "groups": {}, "places": {}, "user_cursor": "u", "group_cursor": "g"}
        self.sync.client.snapshot = AsyncMock(return_value=self.snapshot)

    async def run_sync(self):
        await asyncio.create_task(self.sync.sync())

    async def test_success_and_restart_cache_recovery_offline(self):
        await self.run_sync()
        self.assertEqual(self.sync.state, "ok")
        self.assertEqual(len(self.entry.subentries), 1)
        self.entry.subentries = {}  # crash after cache save, before HA config save
        self.sync.client.snapshot = AsyncMock(side_effect=module.GraphError("cannot_connect"))
        await self.sync.start()
        await self.sync.task
        self.assertEqual(len(self.entry.subentries), 1)
        self.assertEqual(self.sync.state, "error")
        self.assertTrue(self.sync.status["last_success"])
        await self.sync.stop()

    async def test_failed_save_changes_neither_profiles_nor_cursors(self):
        self.sync.store.fail = True
        await self.run_sync()
        self.assertEqual(self.entry.subentries, {})
        self.assertEqual(self.sync.cache, {})
        self.assertEqual(self.sync.state, "error")

    async def test_local_edit_during_save_is_preserved(self):
        await self.run_sync()
        current = self.entry.subentries["new"]
        self.sync.store.on_save = lambda: setattr(current, "data", {**current.data, "sitting_height": 80, "nfc_tag_id": "new-local-tag"})
        await self.run_sync()
        self.assertEqual(current.data["sitting_height"], 80)
        self.assertEqual(current.data["nfc_tag_id"], "new-local-tag")

    async def test_group_failure_retains_entire_previous_state(self):
        await self.run_sync()
        old_cache = deepcopy(self.sync.cache)
        old_data = dict(self.entry.subentries["new"].data)
        self.sync.client.snapshot = AsyncMock(side_effect=module.GraphError("insufficient_permissions"))
        await self.run_sync()
        self.assertEqual(self.sync.cache, old_cache)
        self.assertEqual(self.entry.subentries["new"].data, old_data)

    async def test_concurrent_manual_sync_coalesces_and_unload_cancels(self):
        entered = asyncio.Event()
        async def wait(cache):
            entered.set()
            await asyncio.Event().wait()
        self.sync.client.snapshot = AsyncMock(side_effect=wait)
        task = asyncio.create_task(self.sync.sync())
        await entered.wait()
        await self.sync.sync()
        self.sync.client.snapshot.assert_awaited_once()
        await self.sync.stop()
        self.assertTrue(task.cancelled())
        self.assertEqual(self.entry.subentries, {})

    async def test_invalid_record_does_not_advance_cache(self):
        self.snapshot["users"][USER].pop("accountEnabled")
        await self.run_sync()
        self.assertEqual(self.sync.state, "error")
        self.assertIsNone(self.sync.store.data)
        self.assertFalse(self.entry.subentries)

    async def test_reclassification_preserves_subentry_id_and_local_fields(self):
        await self.run_sync()
        current = self.entry.subentries["new"]
        current.data = {**current.data, "nfc_tag_id": "keep", "sitting_height": 79, "history": ["old"]}
        self.snapshot["places"] = {"p": {"kind": "desk", "displayName": "Desk", "mailboxDetails": {"externalDirectoryObjectId": USER}}}
        await self.run_sync()
        desk = self.entry.subentries["new"]
        self.assertEqual(desk.subentry_type, "desk")
        self.assertEqual(desk.data["history"], ["old"])
        self.assertEqual(desk.data["nfc_tag_id"], "keep")
        self.assertEqual(desk.data["sitting_height"], 79)
        self.assertEqual(self.sync.status["users"], 0)
        await self.run_sync()
        self.assertEqual(len(self.entry.subentries), 1)
        self.snapshot["places"] = {}
        await self.run_sync()
        self.assertFalse(desk.data["active"])
        self.assertEqual(len(self.entry.subentries), 1)


if __name__ == "__main__":
    unittest.main()
