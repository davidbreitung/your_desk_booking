import importlib
import asyncio
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch
import unittest
from test_m365 import graph, CONFIG, Session, Response
from test_m365_lifecycle import ha_modules, Store
from test_bookings_groups import NOW, event as raw_event

policy = importlib.import_module('m365_tests.checkin_policy')
booking = importlib.import_module('m365_tests.booking')


def event(start=-10, end=50, owner='one'):
    return {'id':'event','start':(NOW+timedelta(minutes=start)).isoformat(),
            'end':(NOW+timedelta(minutes=end)).isoformat(),'booker_object_id':owner}


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.person=NS(subentry_id='person',data={'object_id':'one'})

    def decision(self, desk=None, events=None, fresh=True):
        return policy.decide(desk or {},self.person,events or [],NOW,fresh)[0]

    def test_free_walkin_and_reservation_owner(self):
        self.assertEqual(self.decision(),'allow')
        self.assertEqual(self.decision(events=[event()]),'allow')
        self.assertEqual(self.decision(events=[event(owner='other')]),'reserved')

    def test_upcoming_boundary_and_unresolved_identity(self):
        for start,expected in [(60,'reserved'),(60.01,'allow')]:
            self.assertEqual(self.decision(events=[event(start,start+30,'other')]),expected)
        self.assertEqual(self.decision(events=[event(owner=None)]),'reserved')

    def test_occupied_walkin_same_person_and_offline(self):
        desk={'status':'checked_in','occupant':'other'}
        self.assertEqual(self.decision(desk),'occupied')
        self.assertEqual(self.decision({'status':'checked_in','occupant':'person'},fresh=False),'already_checked_in')
        self.assertEqual(self.decision(fresh=False),'calendar_unavailable')

    def test_expired_occupation_can_be_replaced_unless_following_booking(self):
        desk={'status':'checked_in','occupant':'other','checkin_reservation':event(-60,0,'other')}
        self.assertEqual(self.decision(desk),'replace')
        self.assertEqual(self.decision(desk,[event(60,90,'third')]),'reserved')
        self.assertEqual(self.decision(desk,[event(-60,20,'other')]),'reserved')
        self.assertEqual(self.decision({**desk,'status':'error'}),'occupied')

    def test_overlap_conflict_fails_closed(self):
        self.assertEqual(self.decision(events=[event(),event(15,40,'other')]),'reserved')

    def test_no_show_strictly_after_30_minutes_not_attended_and_not_ended(self):
        for start,expected in [(-30,False),(-30.01,True),(-45,True)]:
            self.assertEqual(policy.no_show(event(start,60),NOW,False,{}),expected)
        self.assertFalse(policy.no_show(event(-45,0),NOW,False,{}))
        self.assertFalse(policy.no_show(event(-45,60),NOW,True,{}))
        self.assertFalse(policy.no_show(event(-45,60),NOW,False,{'event':'end'}))

    def test_warning_end_change_is_a_new_key_and_end_is_exclusive(self):
        self.assertIsNone(policy.warning_key(event(end=30.01),NOW))
        self.assertIsNotNone(policy.warning_key(event(end=30),NOW))
        self.assertIsNone(policy.warning_key(event(end=0),NOW))
        self.assertNotEqual(policy.warning_key(event(end=20),NOW),policy.warning_key(event(end=30),NOW))


class GraphDeletionTests(unittest.IsolatedAsyncioTestCase):
    async def test_scoped_delete_204_etag_and_escaped_event_id(self):
        session=Session(Response(204))
        client=graph.GraphClient(session,CONFIG)
        client.token,client.expires='token',float('inf')
        await client.delete_resource_event('desk@example.test',{'id':'a/b','type':'occurrence','@odata.etag':'"version"'})
        method,url,args=session.calls[0]
        self.assertEqual(method,'DELETE')
        self.assertTrue(url.endswith('users/desk%40example.test/events/a%2Fb'))
        self.assertEqual(args['headers']['If-Match'],'"version"')

    async def test_never_delete_series_master_or_without_etag(self):
        client=graph.GraphClient(Session(),CONFIG)
        for obj in ({'id':'x','type':'seriesMaster','@odata.etag':'e'},{'id':'x','type':'occurrence'}):
            with self.assertRaises(graph.GraphError): await client.delete_resource_event('desk',obj)
        self.assertFalse(client.session.calls)

    async def test_changed_event_not_deleted_and_no_body_disclosed(self):
        client=graph.GraphClient(Session(Response(412,{'private':'data'})),CONFIG)
        client.token,client.expires='token',float('inf')
        with self.assertRaises(graph.GraphError) as err:
            await client.delete_resource_event('desk',{'id':'x','type':'singleInstance','@odata.etag':'e'})
        self.assertEqual(str(err.exception),'event_changed')


runtime_modules={**ha_modules,'homeassistant.exceptions':NS(HomeAssistantError=Exception)}
with patch.dict('sys.modules',runtime_modules):
    sync_module=importlib.import_module('m365_lifecycle_tests.booking_sync')
    schedule_module=importlib.import_module('m365_lifecycle_tests.checkout_schedule')


class AutomationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.desk=NS(subentry_id='desk',data={'status':'free','active':True,'calendar_mailbox':'desk@example.test'})
        self.client=NS(has_calendar_write=AsyncMock(return_value=True),resource_event=AsyncMock(),delete_resource_event=AsyncMock())
        self.manager=NS(directory=NS(client=self.client,cache={'users':{}}),alert=AsyncMock(return_value=True),lock=asyncio.Lock())
        self.entry=NS(entry_id='entry',options={},data={'m365':{'tenant_id':'tenant'}},runtime_data=self.manager,subentries={'desk':self.desk})
        self.sync=sync_module.BookingSync(NS(),self.entry)
        self.sync.cache={'desk':{'events':[event(-45,60)],'mailbox':'desk@example.test'}}
        self.sync.info=lambda _: {'fresh':True}
        self.sync._read_desk=AsyncMock(return_value=True)
        self.client.resource_event.return_value=raw_event(-45,id='event',end={'dateTime':(NOW+timedelta(minutes=60)).isoformat(),'timeZone':'UTC'})
        # unresolved booker in this synthetic raw event matches candidate
        self.sync.cache['desk']['events'][0]['booker_object_id']=None
        self.clock=patch.object(sync_module.dt_util,'utcnow',return_value=NOW)
        self.clock.start();self.addCleanup(self.clock.stop)

    async def test_no_show_rechecks_event_and_confirms_calendar(self):
        await self.sync._automation(self.desk)
        self.client.resource_event.assert_awaited_once()
        self.client.delete_resource_event.assert_awaited_once()
        self.sync._read_desk.assert_awaited_once()

    async def test_changed_start_or_attendance_or_occupied_prevents_deletion(self):
        self.client.resource_event.return_value['start']['dateTime']=NOW.isoformat()
        await self.sync._automation(self.desk)
        self.client.delete_resource_event.assert_not_awaited()
        self.sync.cache['desk']['attended']={'event':'end'}
        await self.sync._automation(self.desk)
        self.client.delete_resource_event.assert_not_awaited()
        self.desk.data['status']='error'
        await self.sync._automation(self.desk)
        self.client.delete_resource_event.assert_not_awaited()

    async def test_cache_failure_or_permission_failure_prevents_deletion(self):
        self.sync.store.fail=True
        await self.sync._automation(self.desk)
        self.client.delete_resource_event.assert_not_awaited()
        self.sync.store.fail=False
        self.client.has_calendar_write.return_value=False
        await self.sync._automation(self.desk)
        self.assertEqual(self.sync.errors['desk'],'calendar_write_permission_missing')
        self.client.delete_resource_event.assert_not_awaited()

    async def test_warning_once_and_again_after_changed_end(self):
        self.desk.data['status']='checked_in'
        self.sync._observe_occupant=lambda *args:event(end=30)
        await self.sync._automation(self.desk);await self.sync._automation(self.desk)
        self.manager.alert.assert_awaited_once()
        self.sync._observe_occupant=lambda *args:event(end=25)
        await self.sync._automation(self.desk)
        self.assertEqual(self.manager.alert.await_count,2)


class ScheduleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager=NS(check_out=AsyncMock(),lock=asyncio.Lock())
        self.entry=NS(entry_id='entry',options={'daily_checkout_time':'00:00'},data={'records':{}},runtime_data=self.manager)
        self.schedule=schedule_module.CheckoutSchedule(NS(),self.entry)
        self.schedule.data={'last_due_day':'2026-11-14','pending':{'desk':'person'}}

    async def test_failed_checkout_retried_without_affecting_new_occupants(self):
        with patch.object(schedule_module.dt_util,'utcnow',return_value=NOW), patch.object(schedule_module.dt_util,'as_local',side_effect=lambda x:x,create=True):
            self.manager.check_out.side_effect=Exception('offline')
            await self.schedule.run()
            self.assertEqual(self.schedule.state,'retrying')
            self.manager.check_out.side_effect=None
            await self.schedule.run()
            self.assertFalse(self.schedule.data['pending'])
            self.manager.check_out.assert_awaited_with('desk',None,expected_occupant='person')

    async def test_local_date_boundary(self):
        with patch.object(schedule_module.dt_util,'as_local',side_effect=lambda x:x,create=True):
            self.schedule.time='23:00'
            self.assertEqual(self.schedule.due_day(NOW),'2026-11-14')
            self.assertEqual(self.schedule.due_day(NOW.replace(hour=23)),'2026-11-15')
