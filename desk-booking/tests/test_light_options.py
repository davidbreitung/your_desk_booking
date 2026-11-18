"""User labels/icons remain attached to their light across reordering."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('light_options', Path(__file__).resolve().parents[1] / 'custom_components/desk_booking/light_options.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LightOptionsTests(unittest.TestCase):
    def test_reorder_keeps_labels_with_the_light(self):
        existing = {'light.a': {'name':'Spots', 'icon':'mdi:spotlight-beam'},
                    'light.b': {'name':'LED', 'icon':'mdi:led-strip-variant'}}
        self.assertEqual(module.normalize_light_details(['light.b','light.a'], {}, existing), existing)

    def test_clear_name_preserves_icon(self):
        details = module.normalize_light_details(['light.a'], {'light_1_name':''},
                 {'light.a':{'name':'Spots', 'icon':'mdi:spotlight-beam'}})
        self.assertEqual(details['light.a'], {'name':'','icon':'mdi:spotlight-beam'})

    def test_invalid_icon_and_control_characters_rejected(self):
        for values in ({'light_1_icon':'mdi:nonexistent'}, {'light_1_name':'bad\nname'}, {'light_1_name':'a'*61}):
            with self.assertRaises(ValueError):
                module.normalize_light_details(['light.a'], values, {})

    def test_new_light_gets_offline_default(self):
        self.assertEqual(module.normalize_light_details(['light.a'], {}, {})['light.a'],
                         {'name':'','icon':'mdi:lightbulb-outline'})
