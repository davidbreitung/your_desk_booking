"""Room import and read-only calendar boundaries, using explicit HA fakes."""
import asyncio
from copy import deepcopy
from datetime import timezone
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, patch

from test_places import places
import test_m365_lifecycle as lifecycle
from test_m365_lifecycle import Entry
from test_checkin_rules import sync_module
from test_bookings_groups import NOW, event


class RoomProjectionTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'tenant_id':'tenant','users':{},'places':{
            'p':{'kind':'room','displayName':'Meeting Room','emailAddress':'room@example.test'},
            'd':{'kind':'desk','displayName':'Desk'},
            'w':{'kind':'workspace','displayName':'Workspace'}}}

    def test_only_rooms_and_email_without_entra_user_are_supported(self):
        changes = places.room_updates([], self.snapshot)
        self.assertEqual(len(changes), 1)
        current, data = changes[0]
        self.assertIsNone(current)
        self.assertEqual(data['calendar_mailbox'], 'room@example.test')
        self.assertEqual(data['places_kind'], 'room')
        self.assertTrue(data['active'])
        for key in ('status','display_device','light_entities','occupant','cover_entity'):
            self.assertNotIn(key, data)

    def test_rename_retire_reactivate_keep_identity_and_local_metadata(self):
        data = places.room_updates([], self.snapshot)[0][1]
        old = NS(data={**data,'future_local_setting':'keep'}, subentry_id='stable')
        self.snapshot['places']['p']['displayName'] = 'Renamed'
        current, changed = places.room_updates([old], self.snapshot)[0]
        self.assertIs(current, old)
        self.assertEqual(changed['name'], 'Renamed')
        self.assertEqual(changed['future_local_setting'], 'keep')
        retired = places.room_updates([old], {**self.snapshot,'places':{}})[0][1]
        self.assertFalse(retired['active'])
        old.data = retired
        self.assertTrue(places.room_updates([old],self.snapshot)[0][1]['active'])
        self.assertEqual(places.room_updates([old],{'tenant_id':'tenant','users':{}}), [])

    def test_mailbox_object_id_is_preferred_and_invalid_name_rejected(self):
        self.snapshot['users'] = {'oid':{'mail':'room@example.test'}}
        self.assertEqual(places.room_updates([],self.snapshot)[0][1]['calendar_mailbox'],'oid')
        self.snapshot['places']['p']['displayName']='Bad\nName'
        with self.assertRaises(places.GraphError): places.room_updates([],self.snapshot)

    def test_deleted_room_and_new_same_name_desk_remain_distinct(self):
        data=places.room_updates([],self.snapshot)[0][1]
        old=NS(data=data,subentry_id='old-room',subentry_type='room')
        snapshot={**self.snapshot,'places':{'new-desk':{'kind':'desk','displayName':'Meeting Room'}}}
        retired=places.room_updates([old],snapshot)[0][1]
        self.assertFalse(retired['active'])
        self.assertEqual(retired['name'],'Meeting Room (inaktiv)')
        self.assertEqual(retired['place_id'],'p')
        current,new=places.desk_updates([],[],snapshot)[0]
        self.assertIsNone(current)
        self.assertEqual(new['place_id'],'new-desk')
        self.assertEqual(new['name'],'Meeting Room')
        old.data=retired
        self.assertEqual(places.room_updates([old],snapshot),[])
        self.assertEqual(places.room_updates([old],self.snapshot)[0][1]['name'],'Meeting Room')


class RoomLifecycleTests(unittest.IsolatedAsyncioTestCase):
    setUp = lifecycle.LifecycleTests.setUp
    run_sync = lifecycle.LifecycleTests.run_sync
    async def test_room_import_is_idempotent_and_retired_resource_stays_excluded(self):
        from test_m365 import USER
        self.snapshot['places']={'room':{'kind':'room','displayName':'Room',
            'mailboxDetails':{'externalDirectoryObjectId':USER}}}
        await self.run_sync()
        room=self.entry.subentries['new']
        self.assertEqual(room.subentry_type,'room')
        self.assertEqual(room.data['calendar_mailbox'],USER)
        await self.run_sync()
        self.assertEqual(len(self.entry.subentries),1)
        self.snapshot['places']={}
        await self.run_sync()
        self.assertFalse(room.data['active'])
        self.assertEqual(len(self.entry.subentries),1)


class RoomCalendarTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.entry=Entry()
        self.entry.options={}
        self.room=NS(subentry_id='room',subentry_type='room',data={
            'active':True,'calendar_mailbox':'room@example.test'})
        self.entry.subentries={'room':self.room}
        self.client=NS(calendar_view=AsyncMock(return_value=[event(-10),event(60)]),
            delete_resource_event=AsyncMock(),has_calendar_write=AsyncMock())
        self.entry.runtime_data=NS(lock=asyncio.Lock(),directory=NS(client=self.client,cache={'users':{}}))
        self.sync=sync_module.BookingSync(NS(),self.entry)
        self.clock=patch.object(sync_module.dt_util,'utcnow',return_value=NOW)
        self.clock.start(); self.addCleanup(self.clock.stop)

    async def test_room_poll_cache_and_refresh_never_run_desk_automation(self):
        self.sync._automation=AsyncMock()
        await self.sync.sync()
        self.assertEqual(self.sync.state,'ok')
        self.client.calendar_view.assert_awaited_once()
        self.assertEqual(len(self.sync.cache['room']['events']),2)
        self.assertIn('room',self.sync.store.data['desks']) # backwards-compatible storage key
        self.sync._automation.assert_not_awaited()

    async def test_automation_guard_excludes_room_even_if_called_directly(self):
        await self.sync._automation(self.room)
        self.client.has_calendar_write.assert_not_awaited()
        self.client.delete_resource_event.assert_not_awaited()

    async def test_retired_room_is_not_sync_failure_and_preserves_history(self):
        self.room.data['active']=False
        self.sync.errors['room']='not_found'
        self.sync.cache['room']={'events':[], 'attended':{'old':'end'}}
        await self.sync.sync()
        self.client.calendar_view.assert_not_awaited()
        self.assertEqual(self.sync.state,'ok')
        self.assertEqual(self.sync.errors,{})
        self.assertEqual(self.sync.cache['room']['attended'],{'old':'end'})

    async def test_active_room_without_mailbox_still_reports_real_error(self):
        self.room.data.pop('calendar_mailbox')
        await self.sync.sync()
        self.assertEqual(self.sync.state,'error')
        self.assertEqual(self.sync.errors['room'],'no_resource_mailbox')

    async def test_read_error_retains_cache_and_records_failure(self):
        await self.sync._read_desk(self.room,NOW)
        old=deepcopy(self.sync.cache)
        self.client.calendar_view.side_effect=sync_module.GraphError('insufficient_permissions')
        self.assertFalse(await self.sync._read_desk(self.room,NOW))
        self.assertEqual(self.sync.cache,old)
        self.assertEqual(self.sync.errors['room'],'insufficient_permissions')

    async def test_current_and_next_remain_separate_and_identity_links_match(self):
        from test_m365 import TENANT
        person=NS(subentry_id='person',subentry_type='employee',data={
            'tenant_id':TENANT,'object_id':'oid','name':'Employee'})
        self.entry.subentries['person']=person
        self.entry.runtime_data.directory.cache={'users':{'oid':{'userPrincipalName':'alias@example.test'}}}
        await self.sync._read_desk(self.room,NOW)
        with patch.object(sync_module.dt_util,'DEFAULT_TIME_ZONE',timezone.utc,create=True), \
             patch.object(sync_module.dr,'async_get',return_value=NS(async_get_device_by_identifier=lambda *a:NS(id='device'))), \
             patch.object(sync_module.er,'async_get',return_value=NS(async_get_entity_id=lambda *a:'sensor.employee')):
            upcoming=self.sync.info('room')
            current=self.sync.info('room',current=True)
        self.assertEqual(upcoming['event']['id'],'60')
        self.assertEqual(current['event']['id'],'-10')
        for info in (upcoming,current):
            self.assertTrue(info['fresh'])
            self.assertEqual(info['name'],'Employee')
            self.assertEqual(info['employee_device_id'],'device')
            self.assertEqual(info['employee_entity_id'],'sensor.employee')
