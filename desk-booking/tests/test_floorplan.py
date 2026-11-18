"""Floorplan validation, authorization, persistence, day windows and photo reads."""
import asyncio
import base64
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import importlib
import sys
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch
import unittest
import voluptuous
from zoneinfo import ZoneInfo
from test_m365 import graph, CONFIG, Session, Response
from test_m365_lifecycle import ha_modules, Entry, Store

model=importlib.import_module('m365_tests.floorplan_model')
PLAN={'id':'c0b1c2d3-1111-4222-8333-123456789012','name':'Office','items':[{'resource_id':'desk','x':30,'y':60}],'image':''}


class ModelTests(unittest.TestCase):
    def test_appearance_defaults_and_limits(self):
        old=model.validate_plan(PLAN,{'desk'})
        self.assertEqual((old['object_scale'],old['object_opacity'],old['white_background']),(100,100,True))
        small=deepcopy(PLAN);small['items'][0]['size']=16
        small.update(object_scale=25,object_opacity=20,white_background=False)
        saved=model.validate_plan(small,{'desk'})
        self.assertEqual(saved['items'][0]['size'],16)
        self.assertFalse(saved['white_background'])
        for key,value in [('object_scale',0),('object_opacity',101),('object_scale',float('nan'))]:
            with self.assertRaises(ValueError):model.validate_plan({**PLAN,key:value},{'desk'})

    def test_coordinates_and_duplicate_or_unknown_resources(self):
        self.assertEqual(model.validate_plan(PLAN,{'desk'})['items'][0]['size'],64)
        for value in (float('nan'),float('inf'),-1,101,True,'30'):
            p=deepcopy(PLAN);p['items'][0]['x']=value
            with self.assertRaises(ValueError):model.validate_plan(p,{'desk'})
        with self.assertRaises(ValueError):model.validate_plan(PLAN,set())
        with self.assertRaises(ValueError):model.validate_plan({**PLAN,'items':PLAN['items']*2},{'desk'})

    def test_image_whitelist_rejects_scripts_and_mismatched_mime(self):
        for value in ('https://evil.test/image','data:image/svg+xml;base64,PHN2Zz4=',
                      'data:image/png;base64,PGh0bWw+','data:image/webp;base64,UklGRmJhZGJhZA=='):
            with self.assertRaises(ValueError):model.image_data(value)
        png='data:image/png;base64,'+base64.b64encode(b'\x89PNG\r\n\x1a\nsynthetic').decode()
        self.assertEqual(model.image_data(png),png)

    def test_local_day_dst_and_horizon(self):
        for selected,hours in [('2026-03-29',23),('2026-10-25',25)]:
            now=datetime.fromisoformat(selected+'T12:00:00+00:00')
            day,start,end=model.day_window(selected,now,'Europe/Berlin')
            self.assertEqual((end-start).total_seconds()/3600,hours)
        now=datetime(2026,11,15,23,30,tzinfo=timezone.utc)
        self.assertEqual(str(model.day_window(None,now,'Europe/Berlin')[0]),'2026-11-16')
        for day in ('2026-11-15','2026-12-17'):
            with self.assertRaises(ValueError):model.day_window(day,now,'Europe/Berlin')

    def test_overlap_midnight_and_exclusive_end(self):
        _,start,end=model.day_window('2026-11-15',datetime(2026,11,15,12,tzinfo=timezone.utc),'Europe/Berlin')
        events=[{'id':'overlap','start':(start-timedelta(hours=1)).isoformat(),'end':(start+timedelta(hours=1)).isoformat()},
                {'id':'ended','start':(start-timedelta(hours=2)).isoformat(),'end':start.isoformat()},
                {'id':'nextday','start':end.isoformat(),'end':(end+timedelta(hours=1)).isoformat()}]
        self.assertEqual([e['id'] for e in model.day_events(events,start,end)],['overlap'])


ws=NS(websocket_command=lambda schema:lambda f:f,async_response=lambda f:f)
class PhotoStore(Store):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
mods={**ha_modules,'probatio':voluptuous,'homeassistant.components':NS(websocket_api=ws),
      'homeassistant.components.http':NS(StaticPathConfig=object),
      'homeassistant.helpers.storage':NS(Store=PhotoStore),
      'homeassistant.auth.permissions.const':NS(POLICY_READ='read')}
with patch.dict(sys.modules,mods):
    api=importlib.import_module('m365_lifecycle_tests.floorplan')


class ApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass=NS(data={},config=NS(time_zone='Europe/Berlin'))
        self.manager=api.Floorplans(self.hass);self.hass.data[api.KEY]=self.manager
        self.manager.resources=lambda:{'desk':None}

    async def test_password_enforced_for_save_and_not_exposed(self):
        from functools import partial
        import asyncio
        settings_module=importlib.import_module('m365_lifecycle_tests.floorplan_settings')
        stored=settings_module.hash_password('test-only-password')
        self.manager.entries={'entry':NS(options={'floorplan':{'password_hash':stored}})}
        async def executor(fn,*args):
            return await asyncio.to_thread(partial(fn,*args))
        self.hass.async_add_executor_job=executor
        user=NS(id='admin',is_admin=True)
        connection=NS(user=user,send_error=Mock(),send_result=Mock())
        await api.websocket_floorplan(self.hass,connection,{'id':1,'action':'save','payload':PLAN})
        self.assertEqual(connection.send_error.call_args.args[1],'password_required')
        self.assertFalse(self.manager.plans)
        with self.assertRaises(ValueError):await self.manager.authorize(user,'wrong')
        token=(await self.manager.authorize(user,'test-only-password'))['token']
        self.assertFalse(self.manager.can_save(NS(id='other'),token))
        await api.websocket_floorplan(self.hass,connection,{'id':2,'action':'save','payload':{**PLAN,'edit_token':token}})
        self.assertEqual(len(self.manager.plans),1)
        self.assertFalse(self.manager.can_save(user,token))
        self.assertNotIn('edit_token',next(iter(self.manager.plans.values())))
        for _ in range(3):
            with self.assertRaises(ValueError):await self.manager.authorize(user,'wrong')
        with self.assertRaises(ValueError):await self.manager.authorize(user,'test-only-password')

    async def test_unprotected_save_needs_no_token_and_non_admin_cannot_unlock(self):
        self.assertTrue(self.manager.can_save(NS(),''))
        connection=NS(user=NS(is_admin=False),send_error=Mock(),send_result=Mock())
        await api.websocket_floorplan(self.hass,connection,{'id':1,'action':'authorize','payload':{}})
        self.assertEqual(connection.send_error.call_args.args[1],'unauthorized')

    async def test_save_conflict_and_failed_storage_leave_previous_plan(self):
        result=await self.manager.save(PLAN)
        self.assertEqual(result['revision'],1)
        with self.assertRaises(ValueError):await self.manager.save(PLAN)
        self.manager.store.fail=True
        with self.assertRaises(OSError):await self.manager.save({**result,'name':'Changed'})
        self.assertEqual(self.manager.plans[result['id']]['name'],'Office')

    async def test_normal_user_cannot_write_even_with_forged_payload(self):
        connection=NS(user=NS(is_admin=False),send_error=Mock(),send_result=Mock())
        await api.websocket_floorplan(self.hass,connection,{'id':1,'action':'save','payload':PLAN})
        self.assertFalse(self.manager.plans)
        self.assertEqual(connection.send_error.call_args.args[1],'unauthorized')

    async def test_photo_cache_handles_missing_permission_and_tenant_identity(self):
        person=NS(subentry_id='p',data={'tenant_id':'tenant','object_id':'oid','name':'Employee'})
        client=NS(profile_photo=AsyncMock(side_effect=api.GraphError('not_found')))
        entry=NS(runtime_data=NS(directory=NS(client=client)))
        self.manager.entries={'e':entry};self.manager.people=lambda e,u:{'oid':person}
        self.assertEqual((await self.manager.photo('p',NS()))['status'],'not_found')
        await self.manager.photo('p',NS())
        client.profile_photo.assert_awaited_once_with('oid')
        self.assertIn('tenant:oid',self.manager.photo_store.data['photos'])
        with self.assertRaises(ValueError):await self.manager.photo('not-authorized',NS())

    async def test_snapshot_filters_resources_and_links_allowed_employee(self):
        entry=Entry();entry.options={}
        from test_m365 import TENANT
        person=NS(subentry_id='person',subentry_type='employee',data={'tenant_id':TENANT,'object_id':'oid','name':'Anna'})
        resource=NS(subentry_id='desk',subentry_type='desk',title='Desk',data={'active':True,'status':'checked_in','occupant':'person'})
        entry.subentries={'person':person,'desk':resource}
        events=[{'id':'today','start':'2026-11-15T12:00:00+00:00','end':'2026-11-15T13:00:00+00:00','booker_object_id':'oid'},
                {'id':'tomorrow','start':'2026-11-15T23:10:00+00:00','end':'2026-11-16T00:00:00+00:00','booker_object_id':'oid'}]
        entry.runtime_data=NS(bookings=NS(cache={'desk':{'events':events}},info=lambda _: {'fresh':True,'last_success':'now','error':None}))
        self.manager.entries={'entry':entry};self.manager.resources=lambda:{'desk':(entry,resource)}
        user=NS(is_admin=False,permissions=NS(check_entity=lambda entity,policy:entity!='hidden'))
        with patch.object(api.dt_util,'utcnow',return_value=datetime(2026,11,15,12,tzinfo=timezone.utc)), \
             patch.object(api.dt_util,'get_time_zone',side_effect=ZoneInfo,create=True), \
             patch.object(api.er,'async_get',return_value=NS(async_get_entity_id=lambda *args:args[-1])), \
             patch.object(api.dr,'async_get',return_value=NS(async_get_device_by_identifier=lambda *a:NS(id='employee-device'))):
            data=self.manager.snapshot('2026-11-15',user)
            item=data['resources'][0]
            self.assertEqual(len(item['events']),1)
            self.assertEqual(item['following']['id'],'tomorrow')
            self.assertEqual(item['events'][0]['person']['device_id'],'employee-device')
            self.assertEqual(item['occupant']['name'],'Anna')
            user.permissions.check_entity=lambda *a:False
            self.assertEqual(self.manager.snapshot('2026-11-15',user)['resources'],[])


class PhotoTests(unittest.IsolatedAsyncioTestCase):
    def response(self,data):
        response=Response()
        async def chunks(size):
            for offset in range(0,len(data),size):yield data[offset:offset+size]
        response.content=NS(iter_chunked=chunks)
        return response

    async def test_photo_binary_limit_type_and_token_refresh(self):
        for data in (b'<html>private error',b'\xff\xd8\xff'+b'x'*262144):
            client=graph.GraphClient(Session(self.response(data)),CONFIG)
            client.token,client.expires='token',float('inf')
            with self.assertRaises(graph.GraphError):await client.profile_photo('oid')
        client=graph.GraphClient(Session(Response(401),Response(data={'access_token':'new'}),self.response(b'\xff\xd8\xffimage')),CONFIG)
        client.token,client.expires='old',float('inf')
        data,mime=await client.profile_photo('a/b')
        self.assertEqual(mime,'image/jpeg')
        self.assertIn('a%2Fb/photos/96x96/',client.session.calls[0][1])


if __name__=='__main__':unittest.main()
