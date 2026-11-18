"""Reminder boundaries, safe templates and non-replayed Graph sends."""
from datetime import datetime, timezone, timedelta
import importlib
import unittest
from test_m365 import graph, CONFIG, Session, Response
import asyncio
import sys
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch
from test_m365_lifecycle import ha_modules

model = importlib.import_module('m365_tests.mail_model')
NOW = datetime(2026,11,16,10,tzinfo=timezone.utc)


class MailTests(unittest.TestCase):
    def test_template_whitelist(self):
        for value in ('{mitarbeiter.__class__}', '{foo}', '{beginn!r}', '{beginn:>100}', '{'):
            with self.assertRaises(ValueError): model.template(value)
        self.assertEqual(model.template('{{Hallo}} {mitarbeiter}'), '{{Hallo}} {mitarbeiter}')
        with self.assertRaises(ValueError): model.template('Hi\nBcc: other',True)

    def test_defaults_disabled_and_valid_ranges(self):
        self.assertFalse(model.settings({})['start_enabled'])
        for val in (0,30,float('nan'),True):
            with self.assertRaises(ValueError):model.settings({'expiry_minutes':val})
        with self.assertRaises(ValueError):model.email('bad\n@example.org')

    def test_start_window_and_checkin(self):
        options=model.settings({'start_enabled':True})
        event={'start':NOW.isoformat(),'end':(NOW+timedelta(hours=2)).isoformat()}
        self.assertTrue(model.due(event,'start',options,NOW-timedelta(minutes=15)))
        self.assertFalse(model.due(event,'start',options,NOW-timedelta(minutes=16)))
        self.assertFalse(model.due(event,'start',options,NOW))
        self.assertFalse(model.due(event,'start',options,NOW-timedelta(minutes=5),checked=True))
        self.assertFalse(model.due(event,'start',options,NOW-timedelta(minutes=5),attended=True))

    def test_expiry_only_unattended_desks_before_deadline(self):
        options=model.settings({'expiry_enabled':True})
        event={'start':NOW.isoformat(),'end':(NOW+timedelta(hours=2)).isoformat()}
        self.assertTrue(model.due(event,'expiry',options,NOW+timedelta(minutes=25)))
        self.assertFalse(model.due(event,'expiry',options,NOW+timedelta(minutes=30)))
        self.assertFalse(model.due(event,'expiry',options,NOW+timedelta(minutes=25),room=True))
        event['end']=(NOW+timedelta(minutes=20)).isoformat()
        self.assertFalse(model.due(event,'expiry',options,NOW+timedelta(minutes=25)))


class MailGraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_202_empty_body_is_accepted(self):
        session=Session(Response(202))
        client=graph.GraphClient(session,CONFIG);client.token='fake';client.expires=float('inf')
        self.assertEqual(await client.send_mail('sender@example.org','test@example.org','Test','Hi'),'accepted')
        self.assertTrue(session.calls[0][2]['json']['saveToSentItems'])
        self.assertEqual(len(session.calls),1)

    async def test_post_never_replayed_even_on_5xx(self):
        for status,code in ((503,'mail_delivery_unknown'),(403,'insufficient_permissions'),(429,'rate_limited')):
            session=Session(Response(status,headers={'Retry-After':'180'}))
            client=graph.GraphClient(session,CONFIG);client.token='fake';client.expires=float('inf')
            with self.assertRaises(graph.GraphError) as ctx:
                await client.send_mail('sender@example.org','test@example.org','Test','Hi')
            self.assertEqual(ctx.exception.code,code)
            self.assertEqual(len(session.calls),1)


class ReminderPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with patch.dict(sys.modules,ha_modules):
            self.module=importlib.import_module('m365_tests.mail')
        self.module.dt_util.DEFAULT_TIME_ZONE=timezone.utc
        self.entry=NS(entry_id='test',data={'m365':CONFIG},options={'mail':{'start_enabled':True}},subentries={})
        self.person=NS(subentry_id='p',subentry_type='employee',title='Person',data={'object_id':'oid','tenant_id':CONFIG['tenant_id'],'active':True,'mail':'p@example.org'})
        self.desk=NS(subentry_id='d',subentry_type='desk',title='Desk',data={'active':True,'status':'free'})
        self.entry.subentries={'p':self.person,'d':self.desk}
        self.entry.get_subentries_of_type=lambda kind:[r for r in self.entry.subentries.values() if r.subentry_type==kind]
        self.event={'id':'e','start':(NOW+timedelta(minutes=10)).isoformat(),'end':(NOW+timedelta(hours=1)).isoformat(),'booker_object_id':'oid'}
        self.client=NS(resource_event=AsyncMock(return_value={'id':'e'}),send_mail=AsyncMock(return_value='accepted'))
        self.entry.runtime_data=NS(lock=asyncio.Lock(),directory=NS(client=self.client,cache={'users':{}}),bookings=NS(info=lambda rid:{'fresh':True},cache={'d':{'mailbox':'d@example.org','events':[self.event]}}))
        with patch.object(self.module,'Store',lambda *a,**k:NS(async_save=AsyncMock(),async_load=AsyncMock(return_value=None))):
            self.mail=self.module.MailManager(NS(),self.entry)

    async def tick(self):
        with patch.object(self.module.dt_util,'utcnow',lambda:NOW),patch.object(self.module,'project_events',return_value=[self.event]):
            await self.mail.tick()

    async def test_restart_deduplicates(self):
        await self.tick()
        saved=self.mail.store.async_save.call_args.args[0]
        self.mail.history={}
        self.mail.store.async_load.return_value=saved
        await self.mail.start()
        await self.tick()
        self.client.send_mail.assert_awaited_once()

    async def test_storage_failure_prevents_send(self):
        self.mail.store.async_save.side_effect=OSError()
        await self.tick()
        self.client.send_mail.assert_not_awaited()

    async def test_uncertain_post_not_retried(self):
        self.client.send_mail.side_effect=graph.GraphError('mail_delivery_unknown')
        await self.tick();self.mail.retry_at=0;await self.tick()
        self.client.send_mail.assert_awaited_once()

    async def test_cancelled_event_not_sent(self):
        with patch.object(self.module.dt_util,'utcnow',lambda:NOW),patch.object(self.module,'project_events',return_value=[]):
            await self.mail.tick()
        self.client.send_mail.assert_not_awaited()
