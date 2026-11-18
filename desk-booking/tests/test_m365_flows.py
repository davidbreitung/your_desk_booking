"""Config/options flow behavior with real voluptuous and a fake HA flow boundary."""
import importlib
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from test_m365 import CONFIG, ROOT

pkg = ModuleType("m365_flow_tests")
pkg.__path__ = [str(ROOT / "custom_components/desk_booking")]
sys.modules[pkg.__name__] = pkg


class Flow:
    def __init_subclass__(cls, **kwargs):
        pass
    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}
    def async_show_menu(self, **kwargs):
        return {"type": "menu", **kwargs}
    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}
    def async_abort(self, **kwargs):
        return {"type": "abort", **kwargs}
    async def async_set_unique_id(self, value):
        pass
    def _abort_if_unique_id_configured(self):
        pass


selector = SimpleNamespace(TextSelector=lambda *a: str, TextSelectorConfig=lambda **kw: kw,
    NumberSelector=lambda *a: lambda value: value, NumberSelectorConfig=lambda **kw: kw,
    BooleanSelector=lambda *a: bool)
modules = {
    "homeassistant": ModuleType("homeassistant"),
    "homeassistant.core": SimpleNamespace(callback=lambda fn: fn),
    "homeassistant.config_entries": SimpleNamespace(ConfigEntry=object, ConfigFlow=Flow, OptionsFlow=Flow, ConfigSubentryFlow=Flow),
    "homeassistant.helpers": SimpleNamespace(selector=selector),
    "homeassistant.helpers.aiohttp_client": SimpleNamespace(async_get_clientsession=lambda hass: None),
    "m365_flow_tests.config_desk": SimpleNamespace(DeskSubentryFlow=Flow),
}
with patch.dict(sys.modules, modules):
    flow = importlib.import_module("m365_flow_tests.config_flow")


class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_manual_links_use_separate_tabs_without_literal_icu_tags(self):
        result=await flow.DeskBookingOptionsFlow().async_step_manuals()
        self.assertEqual(result['step_id'],'manuals')
        links=result['description_placeholders']['links']
        self.assertEqual(links.count('target="_blank"'),4)
        self.assertIn('/desk_booking_static/docs/benutzer.html',links)
        self.assertIn('/desk_booking_static/docs/administrator.html',links)

    async def test_floorplan_settings_keep_and_remove_password_and_reject_script_url(self):
        instance=flow.DeskBookingOptionsFlow()
        instance.config_entry=SimpleNamespace(options={'keep':True,'floorplan':{'password_hash':'stored'}})
        result=await instance.async_step_floorplan({'booking_url':'https://places.cloud.microsoft/test'})
        self.assertEqual(result['data']['floorplan']['password_hash'],'stored')
        self.assertTrue(result['data']['keep'])
        result=await instance.async_step_floorplan({'booking_url':'https://places.cloud.microsoft/test','clear_password':True})
        self.assertNotIn('password_hash',result['data']['floorplan'])
        result=await instance.async_step_floorplan({'booking_url':'javascript:alert(1)'})
        self.assertEqual(result['errors']['base'],'invalid_floorplan_settings')

    async def test_mail_help_passes_literal_braces_as_a_value(self):
        instance = flow.DeskBookingOptionsFlow()
        result = await instance.async_step_mail_placeholders()
        self.assertIn('{mitarbeiter}',result['description_placeholders']['help'])
        self.assertIn('{dashboard_link}',result['description_placeholders']['help'])

    async def test_mail_options_accept_empty_optional_dashboard_link(self):
        instance = flow.DeskBookingOptionsFlow()
        instance.config_entry = SimpleNamespace(options={'company_name':'Keep'})
        result = await instance.async_step_mail_settings({})
        self.assertEqual(result['type'],'create_entry')
        self.assertEqual(result['data']['mail']['dashboard_link'],'')
        self.assertFalse(result['data']['mail']['start_enabled'])
        self.assertEqual(result['data']['company_name'],'Keep')

    def setUp(self):
        self.entry = SimpleNamespace(data={"m365": CONFIG}, options={"company_name": "Keep", "display_brightness": 45})
        self.writes = []
        def update(entry, **kwargs):
            self.writes.append(kwargs)
            for key, value in kwargs.items():
                setattr(entry, key, value)
        self.hass = SimpleNamespace(config_entries=SimpleNamespace(async_update_entry=update))

    async def test_initial_configuration_requires_validated_connection(self):
        instance = flow.DeskBookingConfigFlow()
        instance.hass = self.hass
        with patch.object(flow.GraphClient, "test_connection", new_callable=AsyncMock) as check:
            result = await instance.async_step_user(CONFIG)
        self.assertEqual(result["type"], "create_entry")
        check.assert_awaited_once()
        self.assertEqual(result["data"]["m365"]["sync_interval"], 15)

    async def test_failed_connection_does_not_save(self):
        instance = flow.DeskBookingOptionsFlow()
        instance.hass, instance.config_entry = self.hass, self.entry
        with patch.object(flow.GraphClient, "test_connection", new_callable=AsyncMock, side_effect=flow.GraphError("invalid_auth")):
            result = await instance.async_step_m365({**CONFIG, "client_secret": "wrong-synthetic-secret"})
        self.assertEqual(result["errors"], {"base": "invalid_auth"})
        self.assertFalse(self.writes)
        self.assertNotIn("synthetic-test-secret", str(result))

    async def test_blank_secret_preserved_and_display_options_untouched(self):
        instance = flow.DeskBookingOptionsFlow()
        instance.hass, instance.config_entry = self.hass, self.entry
        with patch.object(flow.GraphClient, "test_connection", new_callable=AsyncMock):
            result = await instance.async_step_m365({**CONFIG, "client_secret": "", "sync_interval": 30})
        self.assertEqual(self.entry.data["m365"]["client_secret"], CONFIG["client_secret"])
        self.assertEqual(result["data"], self.entry.options)
        self.assertEqual(self.entry.data["m365"]["sync_interval"], 30)

    async def test_tenant_change_rejected_before_network(self):
        with patch.object(flow.GraphClient, "test_connection", new_callable=AsyncMock) as check:
            with self.assertRaises(flow.GraphError):
                await flow.validate_m365(self.hass, {**CONFIG, "tenant_id": CONFIG["client_id"]}, CONFIG)
        check.assert_not_called()

    async def test_manual_creation_aborted(self):
        result = await flow.EmployeeSubentryFlow().async_step_user({"name": "Injected"})
        self.assertEqual(result, {"type": "abort", "reason": "managed_by_m365"})

    async def test_booking_interval_preserves_other_options(self):
        instance = flow.DeskBookingOptionsFlow()
        instance.config_entry = self.entry
        result = await instance.async_step_bookings({'booking_interval': 7})
        self.assertEqual(result['data']['booking_interval'], 7)
        self.assertEqual(result['data']['company_name'], 'Keep')
        for value in (0, 1441, 1.5, True, float('nan')):
            result = await instance.async_step_bookings({'booking_interval': value})
            self.assertEqual(result['type'], 'form')
            self.assertIn('base', result['errors'])

    async def test_no_manual_creation_buttons_registered(self):
        self.assertEqual(flow.DeskBookingConfigFlow.async_get_supported_subentry_types(self.entry), {})

    async def test_daily_checkout_time_validated_and_defaults_midnight(self):
        instance=flow.DeskBookingOptionsFlow()
        instance.config_entry=self.entry
        result=await instance.async_step_bookings({'booking_interval':5})
        self.assertEqual(result['data']['daily_checkout_time'],'00:00')
        result=await instance.async_step_bookings({'booking_interval':5,'daily_checkout_time':'23:15'})
        self.assertEqual(result['data']['daily_checkout_time'],'23:15')
        for value in ('24:00','00:60','wrong',None):
            result=await instance.async_step_bookings({'booking_interval':5,'daily_checkout_time':value})
            self.assertEqual(result['errors']['base'],'invalid_checkout_time')

    async def test_options_menu_retains_display_configuration(self):
        result = await flow.DeskBookingOptionsFlow().async_step_init()
        self.assertEqual(result["menu_options"], ["display", "m365", "bookings", "desk", "employee", "objects", "mail", "floorplan", "manuals"])


if __name__ == "__main__":
    unittest.main()
