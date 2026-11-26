const mealRoles = ['staple', 'main', 'side'];
const mealLabels = { staple: '主食', main: '主菜', side: '副菜' };

function mealKey(meal) {
  return mealRoles.map((role) => meal[role].id).join('/');
}

function groceries(meals, people, stock) {
  const list = new Map();
  for (const meal of meals) {
    for (const role of mealRoles) {
      for (const [name, quantity, unit] of meal[role].ingredients) {
        if (stock.has(name)) continue;
        const key = `${name}/${unit}`;
        const previous = list.get(key)?.quantity ?? 0;
        list.set(key, { name, quantity: previous + quantity * people, unit });
      }
    }
  }
  return [...list.values()].sort((a, b) => a.name.localeCompare(b.name, 'ja'));
}

function candidatesFor({ limit, stock, excluded, noShopping }) {
  const choices = Object.fromEntries(mealRoles.map((role) => [role, recipes[role].filter((dish) =>
    dish.ingredients.every(([name]) => !excluded.has(name) && (!noShopping || stock.has(name))),
  )]));
  const candidates = [];
  for (const staple of choices.staple) {
    for (const main of choices.main) {
      for (const side of choices.side) {
        const minutes = staple.minutes + main.minutes + side.minutes;
        if (minutes > limit) continue;
        const mainIngredients = new Set(main.ingredients.map(([name]) => name));
        const repeatsVegetable = side.ingredients.some(([name]) =>
          mainIngredients.has(name) && !pantryStaples.includes(name),
        );
        if (repeatsVegetable) continue;
        const meal = { staple, main, side, minutes };
        meal.missing = new Set(groceries([meal], 1, stock).map(({ name }) => name)).size;
        candidates.push(meal);
      }
    }
  }
  return candidates;
}

function selectMeals(candidates, count, history, preferFewer, discover, heldMeal) {
  const selected = [];
  const usedMains = new Set();
  const sides = new Set();
  const groups = new Set();
  const recentMains = new Set(history.slice(-14).map((key) => key.split('/')[1]));
  const recentMeals = new Set(history);
  const pool = candidates.filter((meal) => !heldMeal || mealKey(meal) !== mealKey(heldMeal));
  for (let index = 0; index < count; index += 1) {
    const score = (meal) => (
      (groups.has(meal.main.group) ? 6 : 0)
      + (sides.has(meal.side.id) ? 4 : 0)
      + (recentMeals.has(mealKey(meal)) ? 30 : 0)
      + (recentMains.has(meal.main.id) ? (discover ? 35 : 7) : 0)
      + (preferFewer ? meal.missing * 5 : 0)
    );
    const pick = pool.filter((meal) => !usedMains.has(meal.main.id))
      .reduce((best, meal) => !best || score(meal) < score(best) ? meal : best, null);
    if (!pick) break;
    selected.push(pick);
    usedMains.add(pick.main.id);
    sides.add(pick.side.id);
    groups.add(pick.main.group);
  }
  return selected;
}

function formatQuantity(quantity, unit) {
  return `${Math.round(quantity * 100) / 100}${unit}`;
}
