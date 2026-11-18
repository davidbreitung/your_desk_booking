"""Places pagination, mailbox identity and preservation of local desk settings."""
from copy import deepcopy
import importlib
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from test_m365 import graph, directory, CONFIG, TENANT, USER

places = importlib.import_module("m365_tests.places")


class PlacesGraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_types_and_pages_use_stable_identity(self):
        client = graph.GraphClient(None, CONFIG)
        client.get = AsyncMock(side_effect=[
            {"value": [{"id": "mailbox", "placeId": "stable"}], "@odata.nextLink": graph.BASE + "next"},
            {"value": [{"id": "new"}]}, {"value": [{"id": "room"}]}, {"value": []}])
        result = await client.places()
        self.assertEqual(set(result), {"stable", "new", "room"})
        self.assertEqual(result["room"]["kind"], "room")
        self.assertEqual(client.get.await_count, 4)

    async def test_failed_later_page_never_returns_partial_inventory(self):
        client = graph.GraphClient(None, CONFIG)
        client.get = AsyncMock(side_effect=[{"value": [{"id": "p"}], "@odata.nextLink": graph.BASE + "next"}, graph.GraphError("rate_limited")])
        with self.assertRaises(graph.GraphError):
            await client.places()

    async def test_invalid_page_and_external_link_rejected(self):
        for page in ({}, {"value": [{}]}, {"value": [], "@odata.nextLink": "https://evil.example/v1.0/next"}):
            client = graph.GraphClient(None, CONFIG)
            client.get = AsyncMock(return_value=page)
            with self.assertRaises(graph.GraphError):
                await client.places()


class PlacesProjectionTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {"tenant_id": TENANT, "users": {USER: {"id": USER, "accountEnabled": True,
            "userType": "Member", "displayName": "Desk", "mail": "desk@example.test"}}, "groups": {},
            "places": {"p": {"kind": "desk", "displayName": "Places Desk", "mailboxDetails": {"externalDirectoryObjectId": USER}}}}

    def test_resource_account_never_becomes_employee(self):
        self.assertEqual(directory.profile_updates([], self.snapshot), [])
        changes = places.desk_updates([], [], self.snapshot)
        self.assertEqual(len(changes), 1)
        self.assertIsNone(changes[0][1]["display_device"])

    def test_assigned_employee_is_not_resource(self):
        self.snapshot["places"]["p"].pop("mailboxDetails")
        self.snapshot["places"]["p"]["mode"] = {"@odata.type": "#microsoft.graph.assignedPlaceMode", "assignedUserId": USER}
        self.assertEqual(len(directory.profile_updates([], self.snapshot)), 1)

    def test_case_insensitive_email_fallback_for_rooms_excludes_employee(self):
        self.snapshot["places"]["p"] = {"kind": "room", "emailAddress": "DESK@EXAMPLE.TEST"}
        self.assertEqual(places.resource_users(self.snapshot), {USER: "p"})
        self.assertEqual(directory.profile_updates([], self.snapshot), [])
        self.assertEqual(places.desk_updates([], [], self.snapshot), [])

    def test_ambiguous_mailbox_aborts(self):
        self.snapshot["users"]["other"] = {"mail": "desk@example.test"}
        self.snapshot["places"]["p"]["mailboxDetails"]["emailAddress"] = "desk@example.test"
        with self.assertRaises(graph.GraphError):
            places.resource_users(self.snapshot)

    def test_sync_preserves_all_local_controls_and_occupancy(self):
        data = {"source": "places", "tenant_id": TENANT, "place_id": "p", "name": "Local alias", "active": True,
            "display_device": "display", "display_name": "Screen", "light_entities": ["light.one"],
            "light_details": {"light.one": {"name": "Light"}}, "cover_entity": "cover.one", "switch_entity": "switch.one",
            "status": "checked_in", "occupant": "employee", "previous": {"sitting_height": 72}, "nfc_tag_id": "keep"}
        current = SimpleNamespace(data=data, subentry_type="desk")
        _, result = places.desk_updates([current], [], self.snapshot)[0]
        for key, value in data.items():
            self.assertEqual(result[key], value)
        self.snapshot["places"] = {}
        _, retired = places.desk_updates([current], [], self.snapshot)[0]
        self.assertFalse(retired["active"])
        self.assertEqual(retired["previous"], data["previous"])

    def test_future_desks_import_and_unavailable_mode_disables(self):
        self.snapshot["places"]["new"] = {"kind": "desk", "displayName": "New Desk", "mode": {"@odata.type": "#microsoft.graph.unavailablePlaceMode"}}
        changes = places.desk_updates([], [], self.snapshot)
        self.assertEqual(len(changes), 2)
        self.assertFalse(changes[1][1]["active"])

    def test_no_places_in_legacy_cache_cannot_deactivate_desks(self):
        self.snapshot.pop("places")
        current = SimpleNamespace(data={"source": "places", "tenant_id": TENANT, "place_id": "p", "active": True})
        self.assertEqual(places.desk_updates([current], [], self.snapshot), [])
