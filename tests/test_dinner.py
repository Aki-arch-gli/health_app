import unittest

from modules.dinner import FOODS, PANTRY, dinner_candidates, select_dinners, within_dinner_budget


class DinnerBudgetTests(unittest.TestCase):
    def test_zero_budget_can_use_food_already_at_home(self):
        stocked = dinner_candidates(20, set(FOODS), set(), no_shopping=True)
        self.assertTrue(stocked)
        self.assertEqual(within_dinner_budget(stocked, 0), [])
        self.assertEqual(within_dinner_budget(stocked, 0, "extra_cost"), stocked)

    def test_sorting_and_filtering_use_the_selected_budget_basis(self):
        dishes = dinner_candidates(20, {"ご飯", "木綿豆腐"} | PANTRY, set(), no_shopping=False)
        affordable = within_dinner_budget(dishes, 150, "extra_cost")
        self.assertTrue(affordable)
        self.assertTrue(all(meal["extra_cost"] <= 150 for meal in affordable))
        result = select_dinners(affordable, 1, [], priority="cost", cost_key="extra_cost")[0]
        self.assertEqual(result["extra_cost"], min(meal["extra_cost"] for meal in affordable))
