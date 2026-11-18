"""Read-only Graph capability probe, run inside HA Python; no token output."""
import asyncio
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType
from datetime import datetime, timezone, timedelta
import aiohttp

root=Path('/config')
pkg=ModuleType('checkin_probe');pkg.__path__=[str(root/'custom_components/desk_booking')]
sys.modules[pkg.__name__]=pkg
graph=importlib.import_module('checkin_probe.graph')
entry=next(e for e in json.loads((root/'.storage/core.config_entries').read_text())['data']['entries'] if e['domain']=='desk_booking')

async def main():
    async with aiohttp.ClientSession() as session:
        client=graph.GraphClient(session,entry['data']['m365'])
        permission=await client.has_calendar_write()
        print('CALENDARS_READWRITE_APPLICATION:', permission)
        assert permission
        for record in entry['data']['records'].values():
            if record['subentry_type']!='desk': continue
            data=record['data']
            mailbox=data.get('calendar_mailbox') or data.get('object_id') or data.get('places_email')
            events=await client.calendar_view(mailbox,datetime.now(timezone.utc),datetime.now(timezone.utc)+timedelta(days=1))
            print('RESOURCE_CALENDAR_READ_OK; events_in_next_day:',len(events))
            if events:
                event=await client.resource_event(mailbox,events[0]['id'])
                print('DELETE_PRECONDITION_METADATA:',{'etag_present':bool(event.get('@odata.etag')),'type':event.get('type')})
        print('READ_ONLY_PROBE_COMPLETE; NO_EVENTS_CHANGED')

asyncio.run(main())
