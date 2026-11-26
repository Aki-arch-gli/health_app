const byId = (id) => document.getElementById(id);
const mealForm = byId('meal-form');
const consultForm = byId('consult-form');
const favoriteStorage = 'kurashi-favorites-v1';
const allFoods = [...new Set(Object.values(recipes).flatMap((group) =>
  group.flatMap((dish) => dish.ingredients.map(([name]) => name)),
))].sort((a, b) => a.localeCompare(b, 'ja'));

let activePlan;
let history = [];
let checkedItems = new Set();
let favorites = loadFavorites();
let consultation;

function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}

function link(href, text, className = '') {
  const node = element('a', className, text);
  node.href = href;
  return node;
}

function action(text, listener) {
  const button = element('button', 'button secondary', text);
  button.type = 'button';
  button.addEventListener('click', listener);
  return button;
}

function checkbox(name, value, text = value) {
  const label = element('label', 'check');
  const input = element('input');
  input.type = 'checkbox';
  input.name = name;
  input.value = value;
  label.append(input, element('span', '', text));
  return label;
}

function filterFoodOptions() {
  const query = byId('food-search').value.trim().normalize('NFKC');
  for (const input of mealForm.querySelectorAll('[name="stock"], [name="exclude"]')) {
    input.closest('label').hidden = !input.checked && !input.value.normalize('NFKC').includes(query);
  }
}

function loadFavorites() {
  try {
    const items = JSON.parse(localStorage.getItem(favoriteStorage) ?? '[]');
    return Array.isArray(items) ? items.filter((item) =>
      typeof item?.key === 'string' && Number.isInteger(item.people) && item.people > 0 && item.people <= 6,
    ).slice(0, 60) : [];
  } catch {
    return [];
  }
}

function recordFavorites() {
  try {
    localStorage.setItem(favoriteStorage, JSON.stringify(favorites));
  } catch {
    byId('meal-status').textContent = 'このブラウザーでは、ページを開いている間だけ保存できます。';
  }
}

function restoreMeal(key) {
  const ids = key.split('/');
  if (ids.length !== mealRoles.length) return null;
  const meal = Object.fromEntries(mealRoles.map((role, index) =>
    [role, recipes[role].find((dish) => dish.id === ids[index])],
  ));
  if (mealRoles.some((role) => !meal[role])) return null;
  meal.minutes = mealRoles.reduce((sum, role) => sum + meal[role].minutes, 0);
  return meal;
}

function remember(meals) {
  for (const meal of meals) {
    const key = mealKey(meal);
    history = [...history.filter((item) => item !== key), key].slice(-70);
  }
}

function planMeals(discover = false) {
  const form = new FormData(mealForm);
  const stock = new Set(form.getAll('stock'));
  // Water is available independently of the optional pantry setting.
  stock.add('水');
  if (form.has('pantry')) pantryStaples.forEach((name) => stock.add(name));
  const excluded = new Set(form.getAll('exclude'));
  const limit = Number(form.get('limit'));
  const people = Number(form.get('people'));
  const count = Number(form.get('count'));
  const shopping = form.get('shopping');
  const candidates = candidatesFor({ limit, stock, excluded, noShopping: shopping === 'none' });
  const previous = activePlan?.meals[0];
  const held = discover && count === 1 && previous && candidates.length > 1 ? previous : null;
  const meals = selectMeals(candidates, count, history, shopping === 'less', discover, held);
  activePlan = { meals, people, stock, count, candidates };
  checkedItems = new Set();
  remember(meals);
  renderPlan();
}

function dishList(meal) {
  const list = element('dl', 'dish-list');
  for (const role of mealRoles) {
    const line = element('div', 'dish-line');
    line.append(element('dt', '', mealLabels[role]), element('dd', '', meal[role].title));
    list.append(line);
  }
  return list;
}

function dishInstructions(dish, people) {
  const block = element('div', 'instruction');
  const ingredients = dish.ingredients.map(([name, quantity, unit]) =>
    `${name} ${formatQuantity(quantity * people, unit)}`,
  ).join('、');
  block.append(element('strong', '', dish.title), element('p', '', ingredients), element('p', '', dish.method));
  return block;
}

function mealCard(meal, people, title) {
  const card = element('article', 'panel menu-card');
  card.append(
    element('p', 'menu-kicker', title),
    element('h3', 'menu-title', meal.main.title),
    element('p', 'menu-meta muted', `${people}人分 · 約${meal.minutes}分`),
    dishList(meal),
  );
  const details = element('details');
  details.append(element('summary', '', '分量と作り方'));
  for (const role of mealRoles) details.append(dishInstructions(meal[role], people));
  details.append(link(
    'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/shokuhin/syokuchu/01_00008.html',
    '食材の扱いと加熱の目安',
  ));
  card.append(details);
  return card;
}

function toggleFavorite(key, people) {
  const isSaved = favorites.some((item) => item.key === key && item.people === people);
  favorites = isSaved
    ? favorites.filter((item) => item.key !== key || item.people !== people)
    : [{ key, people }, ...favorites].slice(0, 60);
  recordFavorites();
  renderFavorites();
  return !isSaved;
}

function favoriteLabel(button, isSaved) {
  button.textContent = isSaved ? '保存済み · 取り消す' : 'この献立を保存';
  button.setAttribute('aria-pressed', String(isSaved));
}

function renderPlan() {
  const { meals, people, count, candidates, stock } = activePlan;
  const status = byId('meal-status');
  status.textContent = meals.length === 0
    ? '条件に合う献立が見つかりませんでした。使える食材や調理時間を変更すると、候補を探し直せます。'
    : meals.length < count
      ? `条件に合う夕食を${meals.length}日分表示しました。主菜が重ならない候補を選んでいます。`
      : '';
  status.classList.toggle('empty', !meals.length);
  const cards = meals.map((meal, index) => {
    const title = count === 1 ? '今夜の献立' : `${index + 1}日目の夕食`;
    const card = mealCard(meal, people, title);
    const buttons = element('div', 'actions');
    const key = mealKey(meal);
    const otherSides = candidates.filter((candidate) =>
      candidate.main.id === meal.main.id && candidate.staple.id === meal.staple.id && candidate.side.id !== meal.side.id,
    );
    if (otherSides.length) {
      const swap = action('副菜を替える', () => {
        meals[index] = selectMeals(otherSides, 1, history, true, false)[0];
        checkedItems.clear();
        remember([meals[index]]);
        renderPlan();
        byId(`swap-${index}`)?.focus();
        status.textContent = `副菜を「${meals[index].side.title}」に替えました。`;
      });
      swap.id = `swap-${index}`;
      buttons.append(swap);
    }
    const save = action('', () => favoriteLabel(save, toggleFavorite(key, people)));
    favoriteLabel(save, favorites.some((item) => item.key === key && item.people === people));
    buttons.append(save);
    card.append(buttons);
    return card;
  });
  byId('menus').replaceChildren(...cards);
  byId('menu-actions').hidden = !meals.length;
  byId('discover').disabled = candidates.length < 2;
  const list = byId('buying-list');
  list.replaceChildren();
  const consultLink = link('#consult', '買い物や食事の用意を相談する', 'quiet-link');
  consultLink.addEventListener('click', () => {
    if (consultForm.elements.topic.value !== 'shopping') {
      consultForm.elements.topic.value = 'shopping';
      renderCircumstances();
    }
  });
  if (!meals.length) {
    list.append(consultLink);
    return;
  }
  const panel = element('div', 'panel groceries');
  panel.append(element('h3', '', '買い足すもの'));
  const items = groceries(meals, people, stock);
  if (!items.length) panel.append(element('p', 'muted', '選んだ食材で作れます。必要な量がそろっているか確認してください。'));
  for (const { name, quantity, unit } of items) {
    const key = `${name}/${unit}`;
    const label = checkbox('purchased', key, `${name} ${formatQuantity(quantity, unit)}`);
    label.firstChild.checked = checkedItems.has(key);
    label.addEventListener('change', () => {
      if (label.firstChild.checked) checkedItems.add(key);
      else checkedItems.delete(key);
    });
    panel.append(label);
  }
  panel.append(consultLink);
  list.append(panel);
}

function renderFavorites() {
  const container = byId('favorites');
  const cards = [];
  for (const { key, people } of favorites) {
    const meal = restoreMeal(key);
    if (!meal) continue;
    const card = mealCard(meal, people, '保存した夕食');
    const buttons = element('div', 'actions');
    buttons.append(
      action('印刷', () => printMeals([meal], people, new Set(['水']))),
      action('保存を取り消す', () => {
        toggleFavorite(key, people);
        renderPlan();
        byId('saved-title').focus();
      }),
    );
    card.append(buttons);
    cards.push(card);
  }
  container.replaceChildren(...(cards.length ? cards : [element('p', 'empty', '献立の「この献立を保存」から追加できます。')]));
}

function printMeals(meals, people, stock) {
  const sheet = byId('print-sheet');
  const title = element('h1', '', meals.length === 1 ? '今夜の献立カード' : '夕食の献立カード');
  sheet.replaceChildren(title, element('p', '', `暮らしの食卓 · ${people}人分`));
  for (const [index, meal] of meals.entries()) {
    const section = element('article', 'print-menu');
    const name = meals.length === 1 ? meal.main.title : `${index + 1}日目　${meal.main.title}`;
    section.append(element('h2', '', name), element('p', '', `調理の目安 約${meal.minutes}分`));
    for (const role of mealRoles) section.append(dishInstructions(meal[role], people));
    sheet.append(section);
  }
  const shopping = element('section', 'print-shopping');
  shopping.append(element('h2', '', '買い足すもの'));
  const list = element('ul');
  for (const { name, quantity, unit } of groceries(meals, people, stock)) {
    list.append(element('li', '', `${name} ${formatQuantity(quantity, unit)}`));
  }
  shopping.append(list.children.length ? list : element('p', '', '買い足しなし'));
  shopping.append(element('p', '', '買い物や調理が難しいときは、お住まいの市区町村の福祉窓口へ。高齢の方の生活・介護は地域包括支援センターでも相談できます。'));
  sheet.append(shopping);
  document.body.classList.add('printing');
  window.print();
}

function renderCircumstances() {
  const topic = consultForm.elements.topic.value;
  byId('older-label').hidden = topic !== 'shopping';
  byId('circumstances').replaceChildren(...topics[topic].options.map((text, index) =>
    checkbox('circumstance', String(index), text),
  ));
}

function renderContact(contact) {
  const card = element('article', 'panel contact');
  card.append(element('h3', '', contact.title), element('p', 'muted', contact.description));
  const actions = element('div', 'actions');
  for (const [phone, location] of contact.phones ?? []) {
    const label = location ? `${location} ${phone}` : `${phone} に電話`;
    actions.append(link(`tel:${phone}`, label, 'button secondary'));
  }
  if (contact.url) actions.append(link(contact.url, contact.link ?? '公式ページを見る', 'quiet-link'));
  if (actions.children.length) card.append(actions);
  return card;
}

function showConsultation() {
  const data = new FormData(consultForm);
  const topic = data.get('topic');
  const options = data.getAll('circumstance').map(Number);
  const local = data.get('region') === 'nishitokyo';
  const forOlder = topic === 'shopping' && data.has('older');
  const contacts = supportContacts(topic, local, local ? data.get('town') : '', forOlder);
  const selected = options.map((number) => topics[topic].options[number]);
  const message = selected.length ? selected.join('、') : topics[topic].label;
  consultation = { topic, options, questions: [] };
  byId('contacts').replaceChildren(...contacts.map(renderContact));
  byId('consult-status').textContent = '相談先とメモを表示しました。';
  byId('memo').value = `「${message}」のことで相談したいです。\n${topics[topic].firstQuestion}。\n\n相談先に伝えたいことがあれば、ここに書き足せます。`;
  byId('memo-panel').hidden = false;
  byId('ai-consent').checked = false;
  byId('ai-memo').disabled = true;
  byId('ai-status').textContent = '';
}

async function assistMemo() {
  const input = consultation;
  const button = byId('ai-memo');
  const status = byId('ai-status');
  if (!input || input.pending || !byId('ai-consent').checked) return;
  input.pending = true;
  button.disabled = true;
  const previous = byId('memo').value;
  status.textContent = '相談時に聞くことを整理しています。';
  try {
    const response = await fetch('/api/memo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: input.topic, options: input.options, consent: true }),
      signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) throw new Error('Memo service unavailable');
    const { questions } = await response.json();
    if (consultation !== input) return;
    const suggestions = questions.filter((key) => Object.hasOwn(followupQuestions, key) && !input.questions.includes(key));
    if (suggestions.length) {
      const memo = byId('memo');
      const base = memo.value === previous
        ? previous.replace(/\n\n相談先に伝えたいことがあれば、ここに書き足せます。$/, '')
        : memo.value;
      memo.value = `${base.trimEnd()}\n\n${suggestions.map((key) => `・${followupQuestions[key]}。`).join('\n')}`;
      input.questions.push(...suggestions);
    }
    status.textContent = suggestions.length ? '聞きたいことをメモの末尾に追加しました。' : '追加の提案はありません。';
  } catch {
    if (consultation === input) status.textContent = 'AIに接続できませんでした。表示済みのメモと相談先は引き続き使えます。';
  } finally {
    input.pending = false;
    if (consultation === input) button.disabled = !byId('ai-consent').checked;
  }
}

byId('stock-list').append(...allFoods.filter((food) => !pantryStaples.includes(food)).map((food) => checkbox('stock', food)));
byId('exclude-list').append(...allFoods.map((food) => checkbox('exclude', food)));
byId('pantry-names').textContent = pantryStaples.filter((name) => name !== '水').join('、');
byId('topic').append(...Object.entries(topics).map(([key, topic]) => new Option(topic.label, key)));
byId('town').append(...centers.flatMap((center) => center.area).sort((a, b) => a.localeCompare(b, 'ja')).map((town) => new Option(town, town)));

mealForm.addEventListener('submit', (event) => { event.preventDefault(); planMeals(); });
byId('food-search').addEventListener('input', filterFoodOptions);
byId('discover').addEventListener('click', () => planMeals(true));
byId('print-menu').addEventListener('click', () => printMeals(activePlan.meals, activePlan.people, activePlan.stock));
window.addEventListener('afterprint', () => document.body.classList.remove('printing'));
consultForm.addEventListener('submit', (event) => { event.preventDefault(); showConsultation(); });
byId('topic').addEventListener('change', renderCircumstances);
consultForm.elements.region.addEventListener('change', () => {
  byId('town-label').hidden = consultForm.elements.region.value !== 'nishitokyo';
});
byId('ai-consent').addEventListener('change', (event) => {
  byId('ai-memo').disabled = !event.target.checked || !!consultation?.pending;
});
byId('ai-memo').addEventListener('click', assistMemo);
byId('saved-title').tabIndex = -1;

planMeals();
renderCircumstances();
renderFavorites();
if (['localhost', '127.0.0.1'].includes(location.hostname) && location.protocol !== 'file:') {
  fetch('/api/status').then((response) => response.json()).then(({ ai }) => {
    byId('ai-panel').hidden = ai !== true;
  }).catch(() => {});
}
