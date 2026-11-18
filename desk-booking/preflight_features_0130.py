"""Validate package imports/schema in HA Python before changing live code."""
import asyncio
import importlib
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from zipfile import ZipFile
from hashlib import sha256
import aiohttp

root=Path('/config')
expected=json.loads((root/'desk-booking-0.13.0.sha256.json').read_text())
with tempfile.TemporaryDirectory(prefix='desk_booking_preflight_') as directory:
    stage=Path(directory)
    with ZipFile(root/'desk-booking-0.13.0.zip') as archive:
        for name in archive.namelist():
            relative=name.removeprefix('custom_components/desk_booking/')
            target=(stage/relative).resolve()
            assert target.is_relative_to(stage.resolve())
            data=archive.read(name)
            assert sha256(data).hexdigest()==expected[relative]
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    package=ModuleType('floorplan_preflight');package.__path__=[str(stage)]
    sys.modules[package.__name__]=package
    api=importlib.import_module('floorplan_preflight.floorplan')
    schema=api.websocket_floorplan._ws_schema
    assert schema({'id':1,'type':'desk_booking/floorplan','action':'snapshot'})['payload']=={}
    print('HA_IMPORT_AND_WEBSOCKET_SCHEMA_OK')
    for name in ('config_flow','sensor','mail','management','booking_sync'):
        importlib.import_module('floorplan_preflight.'+name)
    print('ALL_CHANGED_HA_IMPORTS_OK')
    graph=importlib.import_module('floorplan_preflight.graph')
    entries=json.loads((root/'.storage/core.config_entries').read_text())['data']['entries']
    entry=next(e for e in entries if e['domain']=='desk_booking')
    async def probe():
        import base64
        async with aiohttp.ClientSession() as session:
            client=graph.GraphClient(session,entry['data']['m365'])
            token=await client._token()
            part=token.split('.')[1]
            roles=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4))).get('roles',[])
            print('MAIL_SEND_ENTRA_ROLE', 'Mail.Send' in roles)
            page=await client.get(graph.GROUPS)
            print('GROUP_MAIL_QUERY_OK',len(page.get('value',[])))
    asyncio.run(probe())
print('PREFLIGHT_COMPLETE; LIVE_SOURCES_UNCHANGED')
