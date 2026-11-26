import json
import re
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
with (ROOT / "data" / "dinner_recipes.json").open(encoding="utf-8") as source:
    DATA = json.load(source)
with (ROOT / "data" / "ingredient_prices.json").open(encoding="utf-8") as source:
    REFERENCE_PRICES = json.load(source)

RECIPES = DATA["recipes"]
PANTRY = set(DATA["pantry"])
ROLES = {"staple": "主食", "main": "主菜", "side": "副菜"}
FOODS = sorted({
    name for dishes in RECIPES.values() for dish in dishes
    for name, _, _ in dish["ingredients"]
})
VEGETABLES = {
    "きゅうり", "そのまま食べられるカット野菜", "にんじん", "キャベツ", "トマト",
    "冷凍ほうれん草", "冷凍ブロッコリー", "小松菜", "玉ねぎ", "長ねぎ", "もやし",
}

PHOTO_PATTERNS = (
    (r"たら|タラ|カレイ|煮魚|さば.{0,5}煮|ぶり大根|ホイル焼|包み蒸", "fish_simmered.jpg", "魚料理"),
    (r"さば|サバ|魚|鮭|サケ|サーモン|ぶり|ツナ|さんま|あじ|いわし|ムニエル|刺身", "fish_grilled.jpg", "魚料理"),
    (r"豚|ポーク|とんかつ|カツレツ", "pork_dish.jpg", "豚肉料理"),
    (r"鶏|チキン|から揚げ|唐揚げ", "chicken_dish.jpg", "鶏肉料理"),
    (r"鍋|水炊き|すき焼き|ひよこ豆.{0,5}煮", "pot_dish.jpg", "煮込み料理"),
    (r"親子丼|牛丼|豚丼|カツ丼|天丼|丼", "rice_grain.jpg", "丼もの"),
    (r"みそ汁|味噌汁|スープ|お吸い物", "soup_miso.jpg", "汁物"),
    (r"冷奴|豆腐|厚揚げ|おから", "tofu_dish.jpg", "豆腐料理"),
    (r"サラダ|おひたし|ひじき|きんぴら|和え|ナムル", "salad_vegetable.jpg", "野菜料理"),
    (r"パン|トースト|サンドイッチ", "breakfast_western.jpg", "パン"),
    (r"ご飯|ごはん|雑穀|おにぎり|納豆|粥|かゆ", "breakfast_japanese.jpg", "ご飯もの"),
)


def menu_photo(text):
    dishes = re.split(r"[・、／\n]", str(text or ""))
    if any("鮭の香ばし焼き" in dish for dish in dishes):
        return ASSETS / "dinner-hero.jpg", "鮭料理"
    for pattern, filename, caption in PHOTO_PATTERNS:
        if any(re.search(pattern, dish) for dish in dishes):
            return ASSETS / filename, caption
    return ASSETS / "default.jpg", "食卓"


def meal_key(meal):
    return tuple(meal[role]["id"] for role in ROLES)


def shopping_list(meals, people=1, stock=()):
    quantities = Counter()
    for meal in meals:
        for role in ROLES:
            for name, amount, unit in meal[role]["ingredients"]:
                if name not in stock:
                    quantities[name, unit] += amount * people
    return [(name, quantity, unit) for (name, unit), quantity in sorted(quantities.items())]


def estimate_ingredient_cost(items):
    total = 0
    for name, amount, unit in items:
        price = REFERENCE_PRICES.get(name, {}).get(unit)
        if price is None:
            return None
        total += price * amount
    return round(total)


def estimate_meal_cost(meal, people=1):
    return estimate_ingredient_cost(shopping_list([meal], people))


def vegetable_grams(meal):
    return round(sum(amount for name, amount, unit in shopping_list([meal]) if unit == "g" and name in VEGETABLES))


def within_dinner_budget(candidates, ceiling):
    if ceiling is None:
        return candidates
    return [meal for meal in candidates if meal["cost"] is not None and meal["cost"] <= ceiling]


def dinner_candidates(limit, stock, excluded, no_shopping):
    options = [
        [dish for dish in RECIPES[role] if all(
            name not in excluded and (not no_shopping or name in stock)
            for name, _, _ in dish["ingredients"]
        )]
        for role in ROLES
    ]
    meals = []
    for staple, main, side in product(*options):
        minutes = sum(dish["minutes"] for dish in (staple, main, side))
        if minutes > limit:
            continue
        main_foods = {name for name, _, _ in main["ingredients"]} - PANTRY
        if any(name in main_foods for name, _, _ in side["ingredients"]):
            continue
        meal = dict(staple=staple, main=main, side=side, minutes=minutes)
        meal["missing"] = len({name for name, _, _ in shopping_list([meal], stock=stock)})
        meal["cost"] = estimate_meal_cost(meal)
        meal["vegetables"] = vegetable_grams(meal)
        meals.append(meal)
    return meals


def select_dinners(candidates, count, history, prefer_fewer=False, discover=False, priority="variety"):
    seen_meals = set(history)
    recent_mains = {key[1] for key in history[-14:]}
    used_mains, sides, groups = set(), set(), set()
    results = []

    def score(meal):
        variety = (
            (6 if meal["main"]["group"] in groups else 0)
            + (4 if meal["side"]["id"] in sides else 0)
            + (30 if meal_key(meal) in seen_meals else 0)
            + ((35 if discover else 7) if meal["main"]["id"] in recent_mains else 0)
            + (meal["missing"] * 5 if prefer_fewer else 0)
        )
        if priority == "variety":
            return (variety,)
        cost = meal["cost"] if meal["cost"] is not None else float("inf")
        if priority == "cost":
            return (cost, variety)
        if priority == "vegetables":
            return (-meal["vegetables"], variety)
        if priority == "balanced_cost":
            return (cost - meal["vegetables"] * 0.6 + variety,)
        return (variety,)

    for _ in range(count):
        available = (meal for meal in candidates if meal["main"]["id"] not in used_mains)
        best = min(available, key=score, default=None)
        if best is None:
            break
        results.append(best)
        used_mains.add(best["main"]["id"])
        groups.add(best["main"]["group"])
        sides.add(best["side"]["id"])
    return results


def quantity(value, unit):
    return f"{round(value, 2):g}{unit}"
