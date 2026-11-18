"""Read-only room calendar probe inside HA; never output credentials/tokens."""
import asyncio
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType
from datetime import datetime, timezone, timedelta
import aiohttp

root = Path('/config')
pkg = ModuleType('rooms_probe')
pkg.__path__ = [str(root / 'custom_components/desk_booking')]
sys.modules[pkg.__name__] = pkg
graph = importlib.import_module('rooms_probe.graph')
entry = next(e for e in json.loads((root / '.storage/core.config_entries').read_text())['data']['entries'] if e['domain'] == 'desk_booking')

async def main():
    async with aiohttp.ClientSession() as session:
        client = graph.GraphClient(session, entry['data']['m365'])
        rooms = [p for p in (await client.places()).values() if p['kind'] == 'room']
        print('PLACES_ROOMS:', len(rooms))
        for room in rooms:
            mailbox = room.get('mailboxDetails') or {}
            address = mailbox.get('externalDirectoryObjectId') or mailbox.get('emailAddress') or room.get('emailAddress')
            if not address:
                print('ROOM_NO_MAILBOX:', room.get('displayName'))
                continue
            events = await client.calendar_view(address, datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=365))
            print('ROOM_READ_OK:', room.get('displayName'), 'EVENTS:', len(events))
        print('READ_ONLY_PROBE_COMPLETE; NO_EVENTS_CHANGED')

asyncio.run(main())
