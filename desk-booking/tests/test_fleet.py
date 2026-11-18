"""Central commands: scope, partial failures, message ordering and reconnect safety."""
import asyncio
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'desk_booking'
package = ModuleType('fleet_tests')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package

class Error(Exception):
    pass

registry = NS(async_get=lambda h: h.registry,
              async_entries_for_device=lambda r, d: [e for e in r if e.device_id == d])
with patch.dict(sys.modules, {
    'homeassistant': ModuleType('homeassistant'),
    'homeassistant.core': NS(callback=lambda f: f),
    'homeassistant.exceptions': NS(HomeAssistantError=Error, ServiceValidationError=Error),
    'homeassistant.helpers': NS(entity_registry=registry),
    'homeassistant.helpers.event': NS(async_track_state_change_event=lambda *a: lambda: None),
    'homeassistant.helpers.dispatcher': NS(async_dispatcher_send=lambda *a: None),
}):
    spec = importlib.util.spec_from_file_location('fleet_tests.fleet', ROOT / 'fleet.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

class FleetTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.calls, self.states, entries = [], {}, []
        self.desks = [NS(subentry_id=d, title=d, data={'display_device':d}) for d in ['a','b']]
        targets = [('number',n) for n in module.SETTING_TARGETS.values()] + [
            ('switch','Display Aktiv'), ('text','Nachricht Text'), ('select','Nachricht Prioritaet'),
            ('number','Nachrichten Anzeigedauer'), ('button','Nachricht senden'), ('button','Check-in Nachricht senden')]
        for device in ['a','b','unmapped']:
            for i,(domain,name) in enumerate(targets):
                eid = f'{domain}.{device}_{i}'
                entries.append(NS(entity_id=eid, platform='esphome', domain=domain, original_name=name, disabled_by=None, device_id=device))
                self.states[eid] = NS(state='0', attributes={})
        async def call(domain, service, data, **kwargs):
            self.calls.append((domain, service, data))
            await asyncio.sleep(0)
        self.entry = NS(entry_id='test', options={}, get_subentries_of_type=lambda _: self.desks)
        self.hass = NS(registry=entries, states=NS(get=self.states.get), services=NS(async_call=call),
            async_create_task=asyncio.create_task,
            config_entries=NS(async_update_entry=lambda entry, **kw: setattr(entry,'options',kw['options'])))
        self.fleet = module.DisplayFleet(self.hass, self.entry)

    async def asyncTearDown(self):
        await self.fleet.stop()

    async def test_power_only_targets_mapped_displays(self):
        self.desks.append(self.desks[0])
        await self.fleet.power(False, None)
        self.assertEqual(len(self.calls),2)
        self.assertTrue(all(service=='turn_off' and 'unmapped' not in data['entity_id'] for _,service,data in self.calls))

    async def test_offline_device_does_not_block_others(self):
        self.states['switch.a_3'].state = 'unavailable'
        with self.assertRaises(Error):
            await self.fleet.power(True, None)
        self.assertEqual(self.calls, [('switch','turn_on',{'entity_id':'switch.b_3'})])

    async def test_concurrent_messages_are_not_interleaved(self):
        await asyncio.gather(self.fleet.notify('first','1',5,None),self.fleet.notify('second','2',9,None))
        for device in ['a','b']:
            calls = [(s,d) for _,s,d in self.calls if f'.{device}_' in d['entity_id']]
            self.assertEqual([s for s,d in calls], ['set_value','select_option','set_value','press']*2)
            self.assertEqual([calls[i][1]['value'] for i in (0,2,4,6)], ['first',5,'second',9])

    async def test_reconnect_only_restores_settings(self):
        self.fleet.changed(NS(data={'entity_id':'number.a_0','old_state':NS(state='unavailable'),'new_state':NS(state='20')}))
        await asyncio.gather(*list(self.fleet.tasks))
        self.assertEqual(self.calls,[('number','set_value',{'entity_id':'number.a_0','value':50})])

    async def test_invalid_message_has_no_writes(self):
        for text,priority,duration in [(' ','1',5),('x','4',5),('x','1',0),('x'*256,'3',5)]:
            with self.assertRaises(Error):
                await self.fleet.notify(text,priority,duration,None)
        self.assertFalse(self.calls)

    async def test_group_send_only_to_checked_in_members(self):
        group = NS(subentry_type='group', data={'active':True,'tenant_id':'t','object_id':'g',
                   'message_text':'Team message','message_priority':'2','message_duration':9})
        self.entry.subentries = {'group':group,'person':NS(subentry_type='employee',data={'active':True,'tenant_id':'t','object_id':'u'})}
        self.entry.runtime_data = NS(directory=NS(cache={'tenant_id':'t','groups':{'g':{'members':['u']}}}))
        self.desks[0].data.update(status='checked_in',occupant='person')
        self.desks[1].data.update(status='free',occupant='person')
        await self.fleet.notify_target('group',None)
        self.assertEqual(len(self.calls),4)
        self.assertTrue(all('.a_' in data['entity_id'] for _,_,data in self.calls))
        self.assertEqual(self.calls[0][2]['value'],'Team message')
        self.calls.clear()
        self.entry.runtime_data.directory.cache['groups']['g']['members']=[]
        with self.assertRaises(Error):
            await self.fleet.notify_target('group',None)
        self.assertFalse(self.calls)

    async def test_first_message_accepts_unused_text_and_button(self):
        self.states['text.a_4'].state = 'unknown'
        self.states['button.a_7'].state = 'unknown'
        await self.fleet.notify('First message','3',5,None)
        self.assertEqual(len(self.calls),8)

    async def test_checkout_continues_after_failure(self):
        checked = []
        async def checkout(desk,context):
            checked.append(desk)
            if desk=='a': raise Error('offline')
        self.entry.runtime_data = NS(check_out=checkout)
        with self.assertRaises(Error):
            await self.fleet.checkout_all(None)
        self.assertEqual(checked,['a','b'])

    async def test_unchanged_settings_do_not_write(self):
        await self.fleet.settings_updated()
        self.assertFalse(self.calls)
