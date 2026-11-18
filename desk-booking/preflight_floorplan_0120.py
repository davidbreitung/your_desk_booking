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
expected=json.loads((root/'desk-booking-0.12.0.sha256.json').read_text())
with tempfile.TemporaryDirectory(prefix='desk_booking_preflight_') as directory:
    stage=Path(directory)
    with ZipFile(root/'desk-booking-0.12.0.zip') as archive:
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
    graph=importlib.import_module('floorplan_preflight.graph')
    entries=json.loads((root/'.storage/core.config_entries').read_text())['data']['entries']
    entry=next(e for e in entries if e['domain']=='desk_booking')
    async def probe():
        async with aiohttp.ClientSession() as session:
            client=graph.GraphClient(session,entry['data']['m365'])
            counts={}
            for record in entry['data']['records'].values():
                data=record['data']
                if record['subentry_type']!='employee' or not data.get('active') or not data.get('object_id'):continue
                try:
                    photo,mime=await client.profile_photo(data['object_id'])
                    assert mime in ('image/jpeg','image/png') and photo
                    status='photo_available'
                except graph.GraphError as err:
                    status=err.code
                counts[status]=counts.get(status,0)+1
                if status in ('insufficient_permissions','rate_limited','invalid_auth'):break
            print('READ_ONLY_M365_PHOTO_PROBE:',counts)
    asyncio.run(probe())
print('PREFLIGHT_COMPLETE; LIVE_SOURCES_UNCHANGED')
