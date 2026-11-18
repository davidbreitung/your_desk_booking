import importlib
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock
from test_m365 import graph, CONFIG

booking = importlib.import_module('m365_tests.booking')
groups = importlib.import_module('m365_tests.groups')
NOW = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)

def event(minutes=30, **extra):
    return {'id': str(minutes), 'start': {'dateTime': (NOW+timedelta(minutes=minutes)).isoformat(), 'timeZone':'UTC'},
            'end': {'dateTime': (NOW+timedelta(minutes=minutes+30)).isoformat(), 'timeZone':'UTC'},
            'organizer': {'emailAddress': {'address':'ALIAS@example.test'}}, **extra}

class BookingTests(unittest.TestCase):
    def test_identity_alias_and_ambiguity(self):
        users = {'oid': {'proxyAddresses':['smtp:alias@example.test']}}
        self.assertEqual(booking.project_events([event()], users)[0]['booker_object_id'], 'oid')
        users['other'] = {'mail':'alias@example.test'}
        record = booking.project_events([event()], users)[0]
        self.assertIsNone(record['booker_object_id'])
        self.assertEqual(record['identity_status'], 'ambiguous')

    def test_cancel_free_declined_and_current_are_not_next(self):
        events = [event(-10), event(70), event(20,isCancelled=True), event(30,showAs='free'),
                  event(40,responseStatus={'response':'declined'}), event(50)]
        records = booking.project_events(events,{})
        self.assertEqual(booking.next_event(records,NOW)['id'],'50')

    def test_unique_principal_wins_over_shared_contact_address(self):
        users = {'real':{'userPrincipalName':'alias@example.test','mail':'alias@example.test'},
                 'other':{'userPrincipalName':'other@example.test','mail':'alias@example.test'}}
        self.assertEqual(booking.project_events([event()],users)[0]['booker_object_id'],'real')

    def test_strict_boundaries(self):
        for minutes, warning, relative in [(59,True,True),(60,False,True),(119,False,True),(120,False,False)]:
            record = booking.project_events([event(minutes)],{})[0]
            value = booking.booking_presentation(record,NOW,timezone.utc)
            self.assertEqual(value['warning'],warning)
            self.assertEqual(value['label'].startswith('In '),relative)

    def test_timezone_and_malformed_time(self):
        self.assertEqual(booking.graph_time({'dateTime':'2026-11-15T13:00:00+01:00'}),NOW)
        with self.assertRaises(graph.GraphError):
            booking.graph_time({'dateTime':'2026-11-15T13:00:00','timeZone':'Unknown'})

class CalendarPaging(unittest.IsolatedAsyncioTestCase):
    async def test_all_pages_and_no_external_nextlink(self):
        client = graph.GraphClient(None,CONFIG)
        client.get = AsyncMock(side_effect=[{'value':[event()], '@odata.nextLink':graph.BASE+'next'}, {'value':[event(90)]}])
        self.assertEqual(len(await client.calendar_view('mail@example.test',NOW,NOW+timedelta(days=365))),2)
        self.assertIn('mail%40example.test',client.get.call_args_list[0].args[0])
        client.get = AsyncMock(return_value={'value':[], '@odata.nextLink':'https://evil.test'})
        with self.assertRaises(graph.GraphError):
            await client.calendar_view('mail',NOW,NOW+timedelta(days=365))

class GroupTests(unittest.TestCase):
    def test_all_groups_local_fields_preserved_and_deleted_disabled(self):
        old = NS(data={'tenant_id':'t','object_id':'g','active':True,'message_text':'Keep'})
        snap = {'tenant_id':'t','groups':{'g':{'securityEnabled':True,'displayName':'New'}, 'distribution':{'securityEnabled':False}}}
        result = groups.group_updates([old],snap)
        self.assertEqual(len(result),2)
        self.assertEqual(result[0][1]['message_text'],'Keep')
        self.assertFalse(groups.group_updates([old],{'tenant_id':'t','groups':{}})[0][1]['active'])

    def test_active_reservation_start_end_and_following_booking(self):
        records = booking.project_events([event(0),event(60)],{})
        self.assertEqual(booking.active_event(records,NOW)['id'],'0')
        self.assertIsNone(booking.active_event(records,NOW-timedelta(seconds=1)))
        self.assertIsNone(booking.active_event(records,NOW+timedelta(minutes=30)))
        self.assertEqual(booking.next_event(records,NOW)['id'],'60')

    def test_nested_cycle_and_checked_in_tenant_filter(self):
        snap = {'tenant_id':'t','groups':{'g':{'members':['nested']},'nested':{'members':['g','oid']}}}
        entries = {'group':NS(data={'active':True,'tenant_id':'t','object_id':'g'}),
                   'person':NS(subentry_type='employee',data={'active':True,'tenant_id':'t','object_id':'oid'})}
        desks = [NS(data={'status':'checked_in','occupant':'person','display_device':'d'}),
                 NS(data={'status':'free','occupant':'person','display_device':'other'})]
        entry = NS(subentries=entries,get_subentries_of_type=lambda kind:desks)
        self.assertEqual(groups.recipient_devices(entry,'group',snap),['d'])
        entries['person'].data['tenant_id']='wrong'
        self.assertEqual(groups.recipient_devices(entry,'group',snap),[])
