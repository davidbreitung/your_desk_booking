"""Timezone-aware daily checkout with persistent, occupant-specific retries."""
import asyncio
from datetime import timedelta
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util
from homeassistant.exceptions import HomeAssistantError
from .records import records_of_type


class CheckoutSchedule:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.time = entry.options.get('daily_checkout_time', '00:00')
        self.store = Store(hass, 1, f'desk_booking.{entry.entry_id}.checkout_schedule')
        self.data = {}
        self.task, self.cancel = None, None
        self.state = 'idle'

    def due_day(self, now):
        hour, minute = map(int, self.time.split(':')[:2])
        local = dt_util.as_local(now)
        date = local.date() if (local.hour, local.minute) >= (hour, minute) else local.date() - timedelta(days=1)
        return date.isoformat()

    async def start(self):
        self.data = await self.store.async_load() or {}
        if 'last_due_day' not in self.data or self.data.get('time') != self.time:
            # First installation must not retroactively check out today's users.
            self.data = {'last_due_day':self.due_day(dt_util.utcnow()),'pending':self.data.get('pending', {}), 'time':self.time}
            await self.store.async_save(self.data)
        self.cancel = async_track_time_interval(self.hass, self.scheduled, timedelta(seconds=30))
        self.task = self.hass.async_create_task(self.run(), 'Desk Booking daily checkout recovery')

    async def scheduled(self, now):
        if not self.task or self.task.done():
            self.task = self.hass.async_create_task(self.run(), 'Desk Booking daily checkout')

    async def run(self):
        due = self.due_day(dt_util.utcnow())
        if due > self.data['last_due_day']:
            pending = dict(self.data.get('pending', {}))
            async with self.entry.runtime_data.lock:
                for desk in records_of_type(self.entry, 'desk'):
                    if desk.data.get('status', 'free') != 'free':
                        pending[desk.subentry_id] = desk.data.get('occupant', '')
            updated = {**self.data,'last_due_day':due,'pending':pending}
            try:
                await self.store.async_save(updated)
            except OSError:
                self.state = 'cache_error'
                return
            self.data = updated
        for desk_id, occupant in list(self.data.get('pending', {}).items()):
            try:
                await self.entry.runtime_data.check_out(desk_id, None, expected_occupant=occupant)
            except (HomeAssistantError, TimeoutError, KeyError):
                continue
            self.data['pending'].pop(desk_id, None)
            try:
                await self.store.async_save(self.data)
            except OSError:
                self.state = 'cache_error'
                return
        self.state = 'retrying' if self.data.get('pending') else 'ok'

    async def stop(self):
        if self.cancel:
            self.cancel()
        if self.task and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
