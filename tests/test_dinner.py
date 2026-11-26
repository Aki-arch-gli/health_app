import unittest

from modules.dinner import FOODS, PANTRY, dinner_candidates, meal_key, select_dinners, within_dinner_budget


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

    def test_choosing_another_cheap_week_introduces_a_new_meal(self):
        candidates = within_dinner_budget(dinner_candidates(20, PANTRY, set(), False), 350)
        first = select_dinners(candidates, 7, [], priority="cost")
        previous = {meal_key(meal) for meal in first}
        next_plan = select_dinners(candidates, 7, list(previous), priority="cost", previous=previous)
        self.assertEqual(len(next_plan), len(first))
        self.assertEqual(len({meal["main"]["id"] for meal in next_plan}), len(next_plan))
        self.assertTrue({meal_key(meal) for meal in next_plan} - previous)
        self.assertTrue(all(meal["cost"] <= 350 for meal in next_plan))
