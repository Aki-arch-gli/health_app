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
