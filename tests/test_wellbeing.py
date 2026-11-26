import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from modules import wellbeing as store


class WellbeingTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch("modules.database.DB_NAME", str(Path(directory) / "test.db")))
        self.day = date(2026, 11, 21)
        self.now = datetime(2026, 11, 21, 3, tzinfo=timezone.utc)
        store.init_wellbeing()

    def test_edit_reuses_same_day(self):
        store.save_day("owner", self.day, "元気", None, True)
        store.save_day("owner", self.day, "ふつう", "少なめ", False)
        rows = store.own_days("owner", self.day)
        self.assertEqual(rows, [(self.day.isoformat(), "ふつう", "少なめ", 0)])
        self.assertEqual(sum(marked for _, marked in store.week_summary(rows, self.day)), 1)

    def test_stamps_only_and_revocation(self):
        store.save_day("owner", self.day, "元気", "少なめ", True)
        token = store.create_invite("owner", "本人", False, self.now)
        with ThreadPoolExecutor(max_workers=2) as workers:
            claims = list(workers.map(
                lambda viewer: store.redeem_invite(token, viewer, viewer, self.now),
                ("viewer", "other"),
            ))
        self.assertEqual(sum(claims), 1)
        viewer = "viewer" if claims[0] else "other"
        self.assertEqual(store.shared_weeks(viewer, self.day)["owner"]["days"], [
            (self.day.isoformat(), None, None),
        ])
        store.revoke_share("owner", viewer)
        self.assertEqual(store.shared_weeks(viewer, self.day), {})
        self.assertFalse(store.send_message(viewer, "owner", "応援しています"))
        expired = store.create_invite("owner", "本人", True, self.now)
        self.assertFalse(store.redeem_invite(expired, viewer, viewer, self.now + timedelta(hours=24)))

    def test_water_does_not_create_blood_pressure_or_weight(self):
        with ThreadPoolExecutor(max_workers=2) as workers:
            list(workers.map(lambda amount: store.record_water("owner", self.day, amount), (150, 200)))
        self.assertEqual(store.measure_rows("owner", self.day, 7), [
            (self.day.isoformat(), 350, None, None, None),
        ])
        store.save_measures("owner", self.day, None, 62.1, None, None)
        self.assertEqual(store.measure_rows("owner", self.day, 7), [
            (self.day.isoformat(), 350, 62.1, None, None),
        ])

    def test_favorites_are_deduplicated_and_scoped_to_the_account(self):
        key = ("rice", "tofu-sprout-egg", "cabbage", 2)
        store.set_dinner_favorite("owner", key, saved=True)
        store.set_dinner_favorite("owner", key, saved=True)
        store.set_dinner_favorite("other", key, saved=True)
        self.assertEqual(store.dinner_favorite_keys("owner"), [key])
        store.set_dinner_favorite("owner", key, saved=False)
        self.assertEqual(store.dinner_favorite_keys("owner"), [])
        self.assertEqual(store.dinner_favorite_keys("other"), [key])

    def test_measurement_correction_only_updates_selected_field_and_account(self):
        store.save_measures("owner", self.day, 200, 62.1, 120, 75)
        store.record_water("other", self.day, 200)
        store.clear_measure("owner", self.day, "水分")
        self.assertEqual(store.measure_rows("owner", self.day, 1), [
            (self.day.isoformat(), None, 62.1, 120, 75),
        ])
        self.assertEqual(store.measure_rows("other", self.day, 1)[0][1], 200)
        store.clear_measure("owner", self.day, "体重")
        store.clear_measure("owner", self.day, "血圧")
        self.assertEqual(store.measure_rows("owner", self.day, 1), [])

    def test_inverted_pressure_does_not_overwrite_existing_values(self):
        store.save_measures("owner", self.day, None, None, 120, 75)
        with self.assertRaises(ValueError):
            store.save_measures("owner", self.day, 200, None, None, 130)
        self.assertEqual(store.measure_rows("owner", self.day, 1), [
            (self.day.isoformat(), None, None, 120, 75),
        ])

    def test_profile_roundtrip_preserves_older_account_and_blank_values(self):
        self.assertEqual(store.read_profile("owner"), {})
        profile = {
            "facility_name": "", "senior_age": 53, "senior_height": 115.0, "senior_weight": 29.5,
            "senior_disease": "骨粗しょう症", "senior_birthdate": date(1973, 4, 2), "senior_gender": "未回答",
        }
        store.save_profile("owner", profile)
        self.assertEqual(store.read_profile("owner"), profile)
        self.assertEqual(store.read_profile("other"), {})
        profile["senior_birthdate"] = None
        store.save_profile("owner", profile)
        self.assertEqual(store.read_profile("owner"), profile)

    def test_restricting_share_and_removing_stamp_updates_the_view(self):
        store.save_day("owner", self.day, "元気", "少なめ", True)
        store.save_day("other", self.day, None, None, False)
        token = store.create_invite("owner", "本人", True, self.now)
        self.assertTrue(store.redeem_invite(token, "viewer", "見る人", self.now))
        self.assertEqual(store.shared_weeks("viewer", self.day)["owner"]["days"][0][1:], ("元気", "少なめ"))
        store.limit_share_to_stamps("owner", "viewer")
        self.assertEqual(store.shared_weeks("viewer", self.day)["owner"]["days"][0][1:], (None, None))
        store.clear_day("owner", self.day)
        self.assertEqual(store.shared_weeks("viewer", self.day)["owner"]["days"], [])
        self.assertEqual(len(store.own_days("other", self.day)), 1)

    def test_export_uses_permissions_at_download_time(self):
        from modules.wellbeing_ui import _shared_week_pdf

        store.save_day("owner", self.day, "元気", "少なめ", True)
        token = store.create_invite("owner", "本人", True, self.now)
        self.assertTrue(store.redeem_invite(token, "viewer", "見る人", self.now))
        with patch("modules.wellbeing_ui.store.today_in_japan", return_value=self.day), patch(
            "modules.wellbeing_ui.build_meal_card", side_effect=lambda title, sections: str(sections)
        ):
            self.assertIn("少なめ", _shared_week_pdf("viewer", "owner"))
            store.limit_share_to_stamps("owner", "viewer")
            self.assertNotIn("少なめ", _shared_week_pdf("viewer", "owner"))
            store.revoke_share("owner", "viewer")
            self.assertNotIn("本人", _shared_week_pdf("viewer", "owner"))
