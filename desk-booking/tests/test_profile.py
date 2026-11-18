"""Validation tests runnable without installing HA; no mocked HA behavior."""

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "desk_booking"
# Load the pure domain modules without executing the HA integration entrypoint.
package = ModuleType("desk_booking_domain_tests")
package.__path__ = [str(COMPONENT)]
sys.modules[package.__name__] = package
spec = importlib.util.spec_from_file_location(f"{package.__name__}.profile", COMPONENT / "profile.py")
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class ProfileTests(unittest.TestCase):
    def test_real_identity_is_canonical_and_tenant_scoped(self):
        value = profile.normalize_profile({"name": " Example ",
            "tenant_id": "A0B1C2D3-1111-4222-8333-123456789012",
            "object_id": "B0B1C2D3-1111-4222-8333-123456789012"})
        self.assertEqual(value["name"], "Example")
        self.assertEqual(profile.identity(value),
                         "entra:a0b1c2d3-1111-4222-8333-123456789012:b0b1c2d3-1111-4222-8333-123456789012")
        self.assertEqual((value["sitting_height"], value["standing_height"]), (72, 110))

    def test_fake_identity_requires_explicit_test_mode(self):
        with self.assertRaises(profile.ProfileError):
            profile.normalize_profile({"name": "Example", "object_id": "demo"})
        value = self.demo()
        self.assertEqual(profile.identity(value), "test:demo")
        self.assertEqual(profile.profile_title(value), "[TEST] Demo")

    def demo(self, **updates):
        return profile.normalize_profile({"name": "Demo", "test_profile": True,
                                          "object_id": "demo", **updates})

    def test_empty_names_and_ids_rejected(self):
        for updates in ({"name": " "}, {"name": "a" * 101}, {"object_id": " "}):
            with self.subTest(updates=updates), self.assertRaises(profile.ProfileError):
                self.demo(**updates)

    def test_invalid_real_ids_rejected(self):
        for bad in ("mail@example.invalid", "00000000-0000-0000-0000-000000000000", ""):
            with self.subTest(bad=bad), self.assertRaises(profile.ProfileError):
                profile.normalize_profile({"name": "Example", "tenant_id": bad, "object_id": bad})

    def test_tag_is_opaque_trimmed_and_can_be_cleared(self):
        self.assertEqual(self.demo(nfc_tag_id=" Ab-Cd ")["nfc_tag_id"], "Ab-Cd")
        self.assertEqual(self.demo(nfc_tag_id="")["nfc_tag_id"], "")

    def test_tag_validation(self):
        for tag in ("a\x00b", "a" * 256):
            with self.subTest(tag_length=len(tag)), self.assertRaises(profile.ProfileError):
                self.demo(nfc_tag_id=tag)

    def test_duplicate_identity_rejected(self):
        old = SimpleNamespace(subentry_id="1", data=self.demo())
        with self.assertRaises(profile.ProfileError) as error:
            profile.validate_unique(self.demo(), [old])
        self.assertEqual(error.exception.code, "duplicate_identity")

    def test_tag_cannot_be_reused_even_when_old_profile_disabled(self):
        old = SimpleNamespace(subentry_id="1", data=self.demo(nfc_tag_id="TEST-TAG", active=False))
        with self.assertRaises(profile.ProfileError) as error:
            profile.validate_unique(self.demo(object_id="other", nfc_tag_id="TEST-TAG"), [old])
        self.assertEqual(error.exception.code, "duplicate_tag")

    def test_reconfigure_can_keep_its_own_identity_and_tag(self):
        data = self.demo(nfc_tag_id="TEST-TAG")
        profile.validate_unique(data, [SimpleNamespace(subentry_id="1", data=data)], "1")

    def test_multiple_empty_tags_allowed(self):
        profile.validate_unique(self.demo(object_id="other"),
                                [SimpleNamespace(subentry_id="1", data=self.demo())])

    def test_valid_height_limits_and_fraction(self):
        profile.validate_heights(50, 140)
        profile.validate_heights(72.5, 110.5)

    def test_bad_heights_rejected(self):
        for sitting, standing in ((49, 110), (72, 141), (110, 110), (120, 110),
                                  (float("nan"), 110), (72, float("inf")),
                                  (True, 110), ("72", 110)):
            with self.subTest(sitting=sitting, standing=standing), self.assertRaises(profile.ProfileError):
                profile.validate_heights(sitting, standing)

    def test_disabled_profile_preserves_preferences(self):
        data = self.demo(active=False, sitting_height=74.5, standing_height=113)
        self.assertFalse(data["active"])
        self.assertEqual(data["sitting_height"], 74.5)
        self.assertEqual(profile.normalize_profile(json.loads(json.dumps(data))), data)

    def test_translations_have_same_structure(self):
        def keys(obj):
            return {k: keys(v) for k, v in obj.items()} if isinstance(obj, dict) else None
        en = json.loads((COMPONENT / "translations/en.json").read_text(encoding="utf-8"))
        de = json.loads((COMPONENT / "translations/de.json").read_text(encoding="utf-8"))
        self.assertEqual(keys(en), keys(de))


if __name__ == "__main__":
    unittest.main(verbosity=2)
