"""Migration and grouped-record behavior at the HA registry boundary."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from uuid import uuid4

spec = importlib.util.spec_from_file_location("category_records", Path(__file__).resolve().parents[1] / "custom_components/desk_booking/records.py")
r = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = r
spec.loader.exec_module(r)


class CategoriesTests(unittest.TestCase):
    def setUp(self):
        self.entry = NS(entry_id="integration", data={"m365": {"tenant_id": "tenant", "client_secret": "synthetic"}}, subentries={})
        for kind in r.KINDS:
            self.entry.subentries[kind] = NS(subentry_id=kind, subentry_type=kind,
                unique_id="cloud:"+kind, title=kind, data={"nfc_tag_id":"local", "sitting_height":75,
                "display_device":"display", "occupant":"employee", "history":["kept"], "active":True})
        self.before = {key:r.serialize(value) for key,value in self.entry.subentries.items()}
        self.devices = [NS(id="device-"+kind, identifiers={("desk_booking",kind)},
            config_subentry_id=kind, name_by_user="User override", area_id="office") for kind in r.KINDS]
        self.entities = [NS(entity_id="sensor."+kind, unique_id=kind+"_status", config_subentry_id=kind,
            device_id="device-"+kind, disabled_by="user", name="Custom", labels={"keep"}) for kind in r.KINDS]
        self.devices.append(NS(id="central",identifiers={("desk_booking","integration")},config_subentry_id=None))
        self.entities.append(NS(entity_id="sensor.central",unique_id="integration_central_status",config_subentry_id=None))
        def update_entry(entry, **kwargs):
            for key,value in kwargs.items(): setattr(entry,key,value)
        def add_subentry(entry, item): entry.subentries[item.subentry_id] = item
        def remove_subentry(entry, key):
            # Model HA cleanup: still-associated entities/devices would be lost.
            self.assertFalse(any(x.config_subentry_id==key for x in self.entities+self.devices))
            del entry.subentries[key]
        def update_device(key, new_config_subentry_id):
            next(x for x in self.devices if x.id==key).config_subentry_id=new_config_subentry_id
        def update_entity(key, config_subentry_id):
            next(x for x in self.entities if x.entity_id==key).config_subentry_id=config_subentry_id
        self.hass = NS(config_entries=NS(async_update_entry=update_entry,async_add_subentry=add_subentry,async_remove_subentry=remove_subentry))
        self.dr=NS(async_get=lambda hass:NS(async_update_device=update_device),async_entries_for_config_entry=lambda *a:self.devices)
        self.er=NS(async_get=lambda hass:NS(async_update_entity=update_entity),async_entries_for_config_entry=lambda *a:self.entities)
        def subentry(**kwargs): return NS(subentry_id=uuid4().hex, **kwargs)
        self.modules={"homeassistant.config_entries":NS(ConfigSubentry=subentry),
            "homeassistant.helpers":NS(device_registry=self.dr,entity_registry=self.er)}

    def migrate(self):
        with patch.dict(sys.modules,self.modules): r.ensure_categories(self.hass,self.entry)

    def test_migration_keeps_identity_overrides_disabled_entities_and_local_data(self):
        devices_before=deepcopy(self.devices);entities_before=deepcopy(self.entities)
        self.migrate()
        self.assertEqual(len(self.entry.subentries),4)
        self.assertEqual(self.entry.data["records"],self.before)
        for before,after in zip(devices_before,self.devices):
            self.assertEqual({k:v for k,v in vars(before).items() if k!='config_subentry_id'},
                             {k:v for k,v in vars(after).items() if k!='config_subentry_id'})
        for before,after in zip(entities_before,self.entities):
            self.assertEqual({k:v for k,v in vars(before).items() if k!='config_subentry_id'},
                             {k:v for k,v in vars(after).items() if k!='config_subentry_id'})
        for kind in r.KINDS:
            target=r.category_id(self.entry,r.records(self.entry)[kind])
            self.assertEqual(next(x for x in self.devices if x.id=='device-'+kind).config_subentry_id,target)
            self.assertEqual(next(x for x in self.entities if x.entity_id=='sensor.'+kind).config_subentry_id,target)
        self.assertIsNone(self.devices[-1].config_subentry_id)
        self.assertIsNone(self.entities[-1].config_subentry_id)

    def test_repeat_and_partial_migration_are_idempotent(self):
        actual=self.er.async_get
        def fail(*args,**kwargs): raise RuntimeError('interrupted')
        self.er.async_get=lambda hass:NS(async_update_entity=fail)
        with self.assertRaises(RuntimeError): self.migrate()
        self.er.async_get=actual
        self.migrate()
        first=deepcopy(self.entry.data);ids=set(self.entry.subentries)
        self.migrate()
        self.assertEqual(self.entry.data,first)
        self.assertEqual(set(self.entry.subentries),ids)

    def test_new_cloud_records_reuse_categories_and_updates_keep_other_records(self):
        self.migrate()
        categories=set(self.entry.subentries)
        for kind in r.KINDS:
            new=r.Record('new-'+kind,kind,'New', 'new-cloud:'+kind,{'active':True})
            r.add_record(self.hass,self.entry,new)
            self.assertEqual(r.category_id(self.entry,new),r.category_id(self.entry,r.records(self.entry)[kind]))
        current=r.records(self.entry)['employee']
        r.update_record(self.hass,self.entry,current,data={**current.data,'sitting_height':80})
        self.assertEqual(r.records(self.entry)['employee'].data['sitting_height'],80)
        self.assertEqual(r.records(self.entry)['employee'].data['nfc_tag_id'],'local')
        self.assertEqual(len(r.records(self.entry)),8)
        self.assertEqual(set(self.entry.subentries),categories)
        with self.assertRaises(ValueError):
            r.add_record(self.hass,self.entry,r.Record('duplicate','employee','Duplicate','cloud:employee',{}))

    def test_resource_conversion_moves_existing_device_and_retains_record_id(self):
        self.migrate()
        r.add_record(self.hass,self.entry,r.Record('employee','desk','Resource','places:resource',{'active':True}))
        self.migrate()
        target=r.category_id(self.entry,r.records(self.entry)['employee'])
        self.assertEqual(next(x for x in self.devices if x.id=='device-employee').config_subentry_id,target)
        self.assertEqual(next(x for x in self.entities if x.entity_id=='sensor.employee').config_subentry_id,target)
