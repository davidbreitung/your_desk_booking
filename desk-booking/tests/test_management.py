"""Destructive management must reject active or occupied records before writes."""
import asyncio
import importlib
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from test_m365_lifecycle import ha_modules

with patch.dict(sys.modules,{**ha_modules,'m365_tests.floorplan':NS(KEY='floorplans')}):
    module=importlib.import_module('m365_tests.management')


class ManagementSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_active_or_checked_records_rejected_without_writes(self):
        for active,status in ((True,'free'),(False,'checked_in'),(False,'error')):
            record=NS(subentry_id='d',data={'active':active,'status':status})
            entry=NS(subentries={'d':record},data={},runtime_data=NS(
                directory=NS(lock=asyncio.Lock()),bookings=NS(lock=asyncio.Lock()),mail=NS(lock=asyncio.Lock()),lock=asyncio.Lock()))
            with self.assertRaises(ValueError):
                await module.delete_inactive(NS(),entry,'d')

    async def test_employee_with_existing_occupant_cannot_be_deleted(self):
        person=NS(subentry_id='p',data={'active':False})
        desk=NS(subentry_id='d',data={'occupant':'p'})
        entry=NS(subentries={'p':person,'d':desk},data={},runtime_data=NS(
            directory=NS(lock=asyncio.Lock()),bookings=NS(lock=asyncio.Lock()),mail=NS(lock=asyncio.Lock()),lock=asyncio.Lock()))
        with self.assertRaises(ValueError):
            await module.delete_inactive(NS(),entry,'p')
