"""Graph protocol and directory safety tests; no live Microsoft requests."""
import asyncio
from copy import deepcopy
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".test-deps"))
pkg = ModuleType("m365_tests")
pkg.__path__ = [str(ROOT / "custom_components/desk_booking")]
sys.modules[pkg.__name__] = pkg
graph = importlib.import_module("m365_tests.graph")
directory = importlib.import_module("m365_tests.directory")
profile = importlib.import_module("m365_tests.profile")
TENANT = "a0b1c2d3-1111-4222-8333-123456789012"
USER = "b0b1c2d3-1111-4222-8333-123456789012"
CONFIG = {"tenant_id": TENANT, "client_id": USER, "client_secret": "synthetic-test-secret"}


class Response:
    def __init__(self, status=200, data=None, headers=None):
        self.status, self.data, self.headers = status, data, headers or {}
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass
    async def json(self):
        return self.data


class Session:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []
    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


class GraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_auth_token_cached_and_no_redirects(self):
        session = Session(Response(data={"access_token": "synthetic-token", "expires_in": 3600}), Response(data={}), Response(data={}))
        client = graph.GraphClient(session, CONFIG)
        await client.get(graph.USERS)
        await client.get(graph.GROUPS)
        self.assertEqual([c[0] for c in session.calls], ["POST", "GET", "GET"])
        self.assertTrue(all(c[2]["allow_redirects"] is False for c in session.calls))

    async def test_refresh_unauthorized_once(self):
        session = Session(Response(401), Response(data={"access_token": "new"}), Response(data={"ok": True}))
        client = graph.GraphClient(session, CONFIG)
        client.token, client.expires = "old", float("inf")
        self.assertEqual(await client.get(graph.USERS), {"ok": True})

    async def test_long_retry_after_blocks_manual_retry(self):
        session = Session(Response(429, headers={"Retry-After": "120"}))
        client = graph.GraphClient(session, CONFIG)
        for _ in range(2):
            with self.assertRaises(graph.GraphError) as cm:
                await client._request("GET", graph.USERS)
            self.assertEqual(cm.exception.code, "rate_limited")
        self.assertEqual(len(session.calls), 1)

    async def test_short_retry_after_obeyed(self):
        session = Session(Response(503, headers={"Retry-After": "2"}), Response(data={}))
        with patch.object(graph.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            await graph.GraphClient(session, CONFIG)._request("GET", graph.USERS)
            sleep.assert_awaited_once_with(2)

    async def test_permission_error_sanitized(self):
        client = graph.GraphClient(Session(Response(403, {"error": "private secret"})), CONFIG)
        with self.assertRaises(graph.GraphError) as cm:
            await client._request("GET", graph.USERS)
        self.assertEqual(str(cm.exception), "insufficient_permissions")

    async def test_untrusted_cursor_never_receives_token(self):
        session = Session()
        with self.assertRaises(graph.GraphError):
            await graph.GraphClient(session, CONFIG).get("https://evil.example/v1.0/users")
        self.assertFalse(session.calls)

    async def test_paging_partial_user_changes_and_tombstone(self):
        client = graph.GraphClient(None, CONFIG)
        client.get = AsyncMock(side_effect=[
            {"value": [{"id": USER, "displayName": "New"}], "@odata.nextLink": graph.BASE + "next"},
            {"value": [{"id": "deleted", "@removed": {}}], "@odata.deltaLink": graph.BASE + "delta"}])
        old = {USER: {"id": USER, "accountEnabled": True, "userType": "Member"}, "deleted": {"id": "deleted"}}
        result, cursor = await client.delta(graph.USERS, graph.BASE + "old", old)
        self.assertTrue(result[USER]["accountEnabled"])
        self.assertEqual(result[USER]["displayName"], "New")
        self.assertNotIn("deleted", result)
        self.assertIn("deleted", old)

    async def test_group_members_split_across_pages(self):
        client = graph.GraphClient(None, CONFIG)
        client.get = AsyncMock(side_effect=[
            {"value": [{"id": "g", "displayName": "Team", "members@delta": [{"id": USER}]}], "@odata.nextLink": graph.BASE + "next"},
            {"value": [{"id": "g", "members@delta": [{"id": "nested-group"}]}], "@odata.deltaLink": graph.BASE + "delta"}])
        result, cursor = await client.delta(graph.GROUPS, None, {}, True)
        self.assertEqual(set(result["g"]["members"]), {USER, "nested-group"})
        client.get = AsyncMock(return_value={"value": [{"id": "g", "members@delta": [{"id": USER, "@removed": {}}]}], "@odata.deltaLink": graph.BASE + "delta2"})
        result, _ = await client.delta(graph.GROUPS, cursor, result, True)
        self.assertEqual(result["g"]["members"], ["nested-group"])

    async def test_incomplete_round_never_returns_snapshot(self):
        client = graph.GraphClient(None, CONFIG)
        client.get = AsyncMock(return_value={"value": []})
        with self.assertRaises(graph.GraphError):
            await client.snapshot({})

    async def test_expired_cursor_rebuilds_both_collections(self):
        client = graph.GraphClient(None, CONFIG)
        client.delta = AsyncMock(side_effect=[graph.GraphError("delta_expired"), ({}, graph.BASE + "u"), ({}, graph.BASE + "g")])
        client.places = AsyncMock(return_value={})
        result = await client.snapshot({"user_cursor": graph.BASE + "expired"})
        self.assertEqual(result["users"], {})
        self.assertIsNone(client.delta.call_args_list[1].args[1])


class ProjectionTests(unittest.TestCase):
    def snapshot(self, **user):
        return {"tenant_id": TENANT, "users": {USER: {"id": USER, "displayName": "New", "accountEnabled": True, "userType": "Member", **user}}, "groups": {"g": {"members": [USER]}}}

    def local(self):
        return SimpleNamespace(data=profile.normalize_profile({"name": "Old", "tenant_id": TENANT, "object_id": USER,
            "nfc_tag_id": "opaque-local-tag", "sitting_height": 75, "standing_height": 115, "history": ["keep"]}))

    def test_import_active_members_only(self):
        self.assertEqual(len(directory.profile_updates([], self.snapshot())), 1)
        self.assertEqual(directory.profile_updates([], self.snapshot(accountEnabled=False)), [])
        self.assertEqual(directory.profile_updates([], self.snapshot(userType="Guest")), [])

    def test_local_fields_and_identity_preserved_on_rename(self):
        current = self.local()
        _, data = directory.profile_updates([current], self.snapshot())[0]
        for field in ("nfc_tag_id", "sitting_height", "standing_height", "history", "object_id"):
            self.assertEqual(data[field], current.data[field])
        self.assertEqual(data["name"], "New")
        self.assertEqual(data["group_ids"], ["g"])

    def test_deleted_disabled_guests_retained_inactive(self):
        for snapshot in (self.snapshot(accountEnabled=False), self.snapshot(userType="Guest"), {"tenant_id": TENANT, "users": {}, "groups": {}}):
            current = self.local()
            _, data = directory.profile_updates([current], snapshot)[0]
            self.assertFalse(data["active"])
            self.assertEqual(data["history"], ["keep"])

    def test_test_profiles_deactivated_without_migration(self):
        current = SimpleNamespace(data=profile.normalize_profile({"name": "Demo", "test_profile": True, "object_id": "demo"}))
        updates = directory.profile_updates([current], self.snapshot())
        self.assertEqual(len(updates), 2)
        self.assertFalse(updates[-1][1]["active"])
        self.assertEqual(updates[-1][1]["object_id"], "demo")

    def test_invalid_uuid_secret_and_interval(self):
        for update in ({"tenant_id": "common"}, {"client_secret": ""}, {"sync_interval": 0}, {"sync_interval": 5.5}, {"sync_interval": True}):
            with self.assertRaises(graph.GraphError):
                graph.credentials({**CONFIG, **update})


if __name__ == "__main__":
    unittest.main()
