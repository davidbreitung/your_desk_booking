"""Verify four independent light routes and lifecycle/reconnect behavior."""
import asyncio
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'desk_booking'
package = ModuleType('dimmer_tests')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package


class Error(Exception):
    pass


def track(hass, ids, callback):
    item = (ids, callback)
    hass.listeners.append(item)
    return lambda: hass.listeners.remove(item)


registry = NS(async_get=lambda h: h.registry, async_entries_for_device=lambda r, d: r.entries)
with patch.dict(sys.modules, {
    'homeassistant': ModuleType('homeassistant'),
    'homeassistant.core': NS(callback=lambda f: f),
    'homeassistant.exceptions': NS(HomeAssistantError=Error, ServiceValidationError=Error),
    'homeassistant.helpers': NS(entity_registry=registry),
    'homeassistant.helpers.event': NS(async_track_state_change_event=track),
    'homeassistant.helpers.dispatcher': NS(async_dispatcher_send=lambda *args: None),
}):
    spec = importlib.util.spec_from_file_location('dimmer_tests.dimmer', ROOT / 'dimmer.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def state(value, **attributes):
    return NS(state=value, attributes=attributes)


class DimmerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.calls = []
        self.states = {f'light.test{i}': state('off', supported_color_modes=['brightness']) for i in range(1, 5)}
        async def call(domain, service, data, **kw):
            self.calls.append((service, data))
        entries = []
        for slot in range(1, 5):
            suffix = '' if slot == 1 else f' {slot}'
            for domain, name in (('number', 'Dimmer Regelwert'), ('event', 'Dimmer Taster')):
                entries.append(NS(platform='esphome', domain=domain, original_name=name+suffix,
                                  entity_id=f'{domain}.slot{slot}', disabled_by=None))
        self.hass = NS(listeners=[], registry=NS(entries=entries, async_get=lambda _: None),
                       states=NS(get=self.states.get), services=NS(async_call=call), async_create_task=asyncio.create_task)
        desk = NS(subentry_id='desk', title='Desk', data={'display_device':'display', 'light_entities':list(self.states)})
        self.manager = module.DeskDimmer(self.hass, NS(entry_id='test', get_subentries_of_type=lambda _: [desk]))
        self.manager.start()

    def emit(self, entity, old, new):
        for ids, callback in self.hass.listeners:
            if entity in ids:
                callback(NS(data={'entity_id':entity, 'old_state':old, 'new_state':new}, context=None))

    async def asyncTearDown(self):
        await self.manager.stop()

    async def test_all_four_slots_are_independent(self):
        for i in range(1, 5):
            self.emit(f'number.slot{i}', state('5'), state(str(i*10)))
        await asyncio.sleep(.2)
        self.assertEqual({d['entity_id']:d['brightness_pct'] for _,d in self.calls},
                         {f'light.test{i}':i*10 for i in range(1, 5)})

    def bind_cover(self, features=132):
        self.states['cover.test'] = state('open', supported_features=features)
        self.states['number.cover_position'] = state('0')
        self.states['number.cover_tilt'] = state('45')
        for domain, name, suffix in (
            ('event','Rollo Position Befehl','position'), ('event','Lamellen Position Befehl','tilt'),
            ('number','Rollo Position Sollwert','position'), ('number','Lamellen Position Sollwert','tilt')):
            self.hass.registry.entries.append(NS(platform='esphome', domain=domain, original_name=name,
                entity_id=f'{domain}.cover_{suffix}', disabled_by=None))
        self.manager._bind_accessories(NS(subentry_id='coverdesk',title='Cover desk',data={'display_device':'display','cover_entity':'cover.test'}))

    async def test_cover_feedback_and_reconnect_do_not_move(self):
        self.bind_cover()
        self.emit('cover.test',state('open'),state('open',current_position=40))
        self.emit('number.cover_position',state('unavailable'),state('40'))
        self.emit('event.cover_position',None,state('old',event_type='apply',restored=True))
        await asyncio.sleep(.3)
        self.assertFalse(self.calls)

    async def test_cover_explicit_command_can_repeat_same_value(self):
        self.bind_cover()
        for _ in range(2):
            self.emit('event.cover_position',state('unknown'),state(datetime.now(timezone.utc).isoformat(),event_type='apply'))
            await asyncio.sleep(.3)
        self.assertEqual(self.calls,[('set_cover_position',{'entity_id':'cover.test','position':0})]*2)

    async def test_roller_without_tilt_rejects_tilt_command(self):
        self.bind_cover(4)
        self.emit('event.cover_tilt',state('unknown'),state(datetime.now(timezone.utc).isoformat(),event_type='apply'))
        await asyncio.sleep(.3)
        self.assertFalse(self.calls)

    async def test_reconnect_and_attribute_updates_do_not_switch(self):
        for old, new in ((None,state('50')), (state('unavailable'),state('50')),
                         (state('50'),state('50', friendly_name='renamed')), (state('2'),state('nan')),
                         (state('50'),state('101'))):
            self.emit('number.slot1', old, new)
        self.emit('event.slot1', state('unavailable'), state('new', event_type='toggle'))
        await asyncio.sleep(.2)
        self.assertFalse(self.calls)

    async def test_debounce_keeps_latest_and_zero_turns_off(self):
        self.emit('number.slot2', state('5'), state('40'))
        self.emit('number.slot2', state('40'), state('0'))
        await asyncio.sleep(.2)
        self.assertEqual(self.calls, [('turn_off', {'entity_id':'light.test2'})])

    async def test_touch_on_is_routed_once_and_ring_toggle_ignored(self):
        stamp = datetime.now(timezone.utc).isoformat()
        self.emit('event.slot3', state('unknown'), state(stamp, event_type='turn_on'))
        self.emit('event.slot3', state(stamp), state(stamp, event_type='turn_on'))
        self.emit('event.slot3', state('b'), state('c', event_type='other'))
        self.emit('event.slot3', state('c'), state('d', event_type='toggle'))
        await asyncio.sleep(.01)
        self.assertEqual(self.calls, [('turn_on', {'entity_id':'light.test3'})])

    async def test_touch_off_cancels_pending_brightness(self):
        self.emit('number.slot2', state('5'), state('80'))
        self.emit('event.slot2', state('unknown'), state(datetime.now(timezone.utc).isoformat(), event_type='turn_off'))
        await asyncio.sleep(.2)
        self.assertEqual(self.calls, [('turn_off', {'entity_id':'light.test2'})])

    async def test_old_restored_command_not_replayed(self):
        self.emit('event.slot1', None, state('2020-01-01T00:00:00+00:00', event_type='turn_on'))
        await asyncio.sleep(.01)
        self.assertFalse(self.calls)

    async def test_unload_cancels_waiting_commands(self):
        self.emit('number.slot1', state('0'), state('50'))
        await self.manager.stop()
        self.assertFalse(self.hass.listeners)
        self.assertFalse(self.calls)
        self.manager.unsubscribers.clear()

    async def test_unavailable_light_not_switched(self):
        self.states['light.test4'] = state('unavailable')
        self.emit('number.slot4', state('1'), state('90'))
        await asyncio.sleep(.2)
        self.assertFalse(self.calls)

    async def test_display_backlight_is_rejected(self):
        self.hass.registry.async_get = lambda _: NS(device_id='display')
        with self.assertRaises(Error):
            module.validate_light(self.hass, 'light.test1', 'display')


if __name__ == '__main__':
    unittest.main()
