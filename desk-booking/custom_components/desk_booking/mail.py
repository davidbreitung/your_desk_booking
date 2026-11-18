"""Opt-in reminder delivery with persisted at-most-once attempts."""
import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from .records import records, records_of_type
from .booking import project_events
from .graph import GraphError
from .mail_model import DEFAULTS, settings, email, due, values


class MailManager:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.store = Store(hass, 1, f'desk_booking.{entry.entry_id}.mail', private=True)
        self.history = {}
        self.state, self.error, self.last_accepted = 'disabled', None, None
        self.lock = asyncio.Lock()
        self.retry_at = 0

    async def start(self):
        saved = await self.store.async_load() or {}
        if saved.get('tenant_id') == self.entry.data.get('m365', {}).get('tenant_id'):
            self.history = saved.get('history', {})
            self.last_accepted = saved.get('last_accepted')

    async def save(self):
        await self.store.async_save({'tenant_id':self.entry.data.get('m365', {}).get('tenant_id'),
            'history':self.history, 'last_accepted':self.last_accepted})

    @property
    def options(self):
        return settings(self.entry.options.get('mail', {}))

    async def send(self, recipient, subject, body):
        client = self.entry.runtime_data.directory.client
        if not client:
            raise GraphError('not_configured')
        await client.send_mail(self.options['sender'], email(recipient), subject, body)
        self.last_accepted = dt_util.utcnow().isoformat()
        self.state, self.error = 'accepted', None

    async def tick(self):
        if self.lock.locked() or time.time() < self.retry_at:
            return
        async with self.lock:
            options = self.options
            if not (options['start_enabled'] or options['expiry_enabled']):
                self.state = 'disabled'
                return
            runtime = self.entry.runtime_data
            client = runtime.directory.client
            if not client:
                self.state = 'not_configured'
                return
            now = dt_util.utcnow()
            # Prune only long-expired reminders; retained through every restart.
            self.history = {k:v for k,v in self.history.items() if v.get('retain_until', '') > now.isoformat()}
            try:
                for resource in list(records(self.entry).values()):
                    if resource.subentry_type not in ('desk','room') or not resource.data.get('active', True):
                        continue
                    async with runtime.lock:
                        resource = records(self.entry).get(resource.subentry_id)
                        if not resource or not runtime.bookings.info(resource.subentry_id)['fresh']:
                            continue
                        cached = runtime.bookings.cache.get(resource.subentry_id, {})
                        for event in list(cached.get('events', [])):
                            person = next((p for p in records_of_type(self.entry, 'employee') if
                                p.data.get('object_id') == event.get('booker_object_id') and
                                p.data.get('tenant_id') == self.entry.data['m365']['tenant_id'] and p.data.get('active')), None)
                            if not person:
                                continue
                            checked = resource.data.get('status') == 'checked_in' and resource.data.get('occupant') == person.subentry_id
                            for kind in ('start','expiry'):
                                if not due(event, kind, options, now, event['id'] in cached.get('attended', {}), checked, resource.subentry_type == 'room'):
                                    continue
                                key = hashlib.sha256(('|'.join((resource.subentry_id,event['id'],event['start'],event.get('booker_object_id') or '',kind))).encode()).hexdigest()
                                if key in self.history:
                                    continue
                                # Revalidate cancellation, organizer and rescheduling immediately before send.
                                raw = await client.resource_event(cached['mailbox'], event['id'])
                                fresh = project_events([raw], runtime.directory.cache.get('users', {}))
                                if not fresh or any(fresh[0].get(k) != event.get(k) for k in ('start','end','booker_object_id')):
                                    continue
                                recipient = person.data.get('mail')
                                if not recipient:
                                    self.error = 'recipient_email_missing'
                                    continue
                                email(recipient)
                                if not due(event, kind, options, dt_util.utcnow(), event['id'] in cached.get('attended', {}), checked, resource.subentry_type == 'room'):
                                    continue
                                variables = values(event, person.title, resource.title, dt_util.DEFAULT_TIME_ZONE, options['dashboard_link'])
                                self.history[key] = {'state':'pending', 'resource_id':resource.subentry_id, 'employee_id':person.subentry_id,
                                    'retain_until':(datetime.fromisoformat(event['end'])+timedelta(days=30)).isoformat()}
                                await self.save()  # Fail closed before any external side effect.
                                try:
                                    await self.send(recipient, options[kind+'_subject'].format_map(variables), options[kind+'_body'].format_map(variables))
                                except GraphError as err:
                                    self.history[key]['state'] = err.code
                                    # A rejected request is safe to retry later, uncertain outcomes are not.
                                    if err.code in ('rate_limited','invalid_auth','insufficient_permissions','mailbox_not_found','invalid_mail'):
                                        self.history.pop(key)
                                    await self.save()
                                    raise
                                self.history[key]['state'] = 'accepted'
                                await self.save()
            except (GraphError, OSError, ValueError) as err:
                self.state = 'error'
                self.error = err.code if isinstance(err, GraphError) else 'cache_error' if isinstance(err, OSError) else 'invalid_mail'
                self.retry_at = time.time() + max(300, err.retry_after if isinstance(err, GraphError) else 300)
