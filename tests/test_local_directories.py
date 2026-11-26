import unittest

from modules.dining_ui import DIRECTORY as DINING, matching_places
from modules.kurashi_ui import CONTACTS, _consultation_contacts, consultation_memo_download


class LocalDirectoryTests(unittest.TestCase):
    def test_new_dining_area_filters_menu_price_and_category(self):
        origin = DINING["areas"]["武蔵境駅周辺"]
        self.assertFalse(matching_places(origin, 1, 589, True, "うどん"))
        matches = matching_places(origin, 1, 590, True, "うどん")
        self.assertEqual([place["name"] for place, _, _ in matches], ["丸亀製麺 武蔵境"])
        self.assertEqual([meal["price"] for meal in matches[0][2]], [590])
        self.assertTrue(all(DINING["menus"][place["group"]] for place in DINING["places"]))

    def test_older_persons_town_resolves_to_its_unique_center(self):
        self.assertEqual(len(CONTACTS), 8)
        towns = [town for center in CONTACTS for town in center["area"]]
        self.assertEqual(len(towns), len(set(towns)))
        local = list(_consultation_contacts("care", "西東京市", "ひばりが丘北", True))[0]
        self.assertEqual(local["title"], "栄町地域包括支援センター")
        self.assertIn("保谷苑", local["address"])
        self.assertIn("9:00", local["hours"])
        regular = list(_consultation_contacts("care", "西東京市", "ひばりが丘", True))[0]
        self.assertEqual(regular["title"], "緑町地域包括支援センター")
        fallback = list(_consultation_contacts("care", "西東京市", None, True))[0]
        self.assertEqual(fallback["phones"][0][0], "042-420-2811")

    def test_download_includes_the_destination_and_followup(self):
        contacts = list(_consultation_contacts("care", "西東京市", "田無町", True))
        memo = consultation_memo_download("家族の暮らしについて相談したい", contacts, for_older=True)
        for item in ("家族の暮らしについて相談したい", "田無町地域包括支援センター", "042-467-8850", "次に連絡する日"):
            self.assertIn(item, memo)
