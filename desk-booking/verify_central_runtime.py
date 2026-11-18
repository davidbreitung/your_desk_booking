"""Isolated checks against installed HA classes; does not access a running instance."""
import asyncio
import sys
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, '/config/desk_booking_stage_050')
from custom_components.desk_booking.config_desk import DeskSubentryFlow
from custom_components.desk_booking.config_flow import DeskBookingOptionsFlow
from custom_components.desk_booking.sensor import DeskOccupant

async def main():
    data = {'name':'Desk', 'display_name':'Desk label', 'display_device':'display',
            'light_entities':['light.front','light.back'],
            'light_details':{'light.front':{'name':'vorne','icon':'mdi:spotlight-beam'},
                             'light.back':{'name':'hinten','icon':'mdi:led-strip-variant'}},
            'status':'checked_in','occupant':'employee','applied':{'sitting_height':66,'standing_height':111}}
    desk = NS(data=data,subentry_id='desk',title='Desk',subentry_type='desk')
    profile = NS(data={'name':'Expected profile name'},subentry_id='employee',title='Virtual device title')
    entry = NS(entry_id='isolated',options={'company_name':'Keep company'},subentries={'desk':desk,'employee':profile},get_subentries_of_type=lambda _: [desk])
    fake_hass = NS(states=NS(get=lambda eid: NS(state='off', attributes={'supported_color_modes':['brightness']},name=eid)))
    with patch.object(DeskSubentryFlow,'_get_entry',return_value=entry), \
         patch.object(DeskSubentryFlow,'_get_reconfigure_subentry',return_value=desk), \
         patch.object(DeskSubentryFlow,'async_show_form',side_effect=lambda **kw: kw), \
         patch('custom_components.desk_booking.config_desk.display_targets'), \
         patch('custom_components.desk_booking.config_desk.validate_light'), \
         patch.object(DeskSubentryFlow,'async_update_and_abort',side_effect=lambda *a,**kw: kw):
        flow=DeskSubentryFlow()
        flow.hass=fake_hass
        form=await flow.async_step_reconfigure()
        fields={str(k) for k in form['data_schema'].schema}
        assert {'light_1_entity','light_1_name','light_1_icon','cover_entity','switch_entity'} <= fields
        submitted={'name':'Desk','display_name':'Desk label','display_device':'display',
                   'light_1_entity':'light.front','light_1_name':'vorne','light_1_icon':'mdi:spotlight-beam',
                   'light_2_entity':'light.back','light_2_name':'hinten','light_2_icon':'mdi:led-strip-variant'}
        result=await flow.async_step_reconfigure(submitted)
        saved=result['data']
        assert saved['status']=='checked_in' and saved['occupant']=='employee'
        assert saved['applied']==data['applied'] and saved['light_details']==data['light_details']
    with patch.object(DeskBookingOptionsFlow,'config_entry',new=property(lambda self:entry)), \
         patch.object(DeskBookingOptionsFlow,'async_show_form',side_effect=lambda **kw:kw), \
         patch.object(DeskBookingOptionsFlow,'async_create_entry',side_effect=lambda **kw:kw):
        flow=DeskBookingOptionsFlow()
        form=await flow.async_step_init()
        assert {'company_name','display_brightness','standby_brightness','standby_timeout','standby_home'} == {str(k) for k in form['data_schema'].schema}
        invalid=await flow.async_step_init({'company_name':'Keep company','display_brightness':float('nan')})
        assert invalid['errors']['display_brightness']=='invalid_display_setting'
    sensor=DeskOccupant(entry,desk,'occupant')
    assert sensor.native_value=='Expected profile name'
    print('ISOLATED_HA_FLOW_AND_PROFILE_CHECKS_OK')

asyncio.run(main())
