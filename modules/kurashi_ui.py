import json
from urllib.error import URLError

import streamlit as st

from config import GEMINI_API_KEY, get_setting
from modules.dinner import (
    ASSETS, FOODS, PANTRY, ROLES, ROOT, dinner_candidates, estimate_ingredient_cost,
    estimate_meal_cost, meal_key, menu_photo, quantity, select_dinners, shopping_list,
    vegetable_grams, within_dinner_budget,
)
from modules.meal_print import build_meal_card
from modules.runtime_paths import TRIAL_MODE
from serve import select_questions

with (ROOT / "data" / "support_directory.json").open(encoding="utf-8") as source:
    DIRECTORY = json.load(source)

CONTACTS = DIRECTORY["centers"]
TOPICS = DIRECTORY["topics"]
TOWNS = sorted(town for center in CONTACTS for town in center["area"])
DINNER_PRIORITIES = {
    "variety": "いろいろな献立",
    "balanced_cost": "節約しながら野菜も",
    "cost": "食材費が安い順",
    "vegetables": "野菜が多い順",
}


def apply_theme(dark=False):
    palette = {
        "page": "#1b2721" if dark else "#fff8e9",
        "paper": "#28382c" if dark else "#fffdf6",
        "ink": "#f7f4e8" if dark else "#233b2c",
        "border": "#769982" if dark else "#b0bda2",
        "banner": "#314739" if dark else "#f9edbd",
        "accent": "#eeb65e" if dark else "#b84e2a",
        "selected": "#bde0a8" if dark else "#2d6040",
        "on_selected": "#14271a" if dark else "#ffffff",
    }
    variables = "".join(f"--kurashi-{key}:{value};" for key, value in palette.items())
    css = (ASSETS / "kurashi.css").read_text(encoding="utf-8")
    st.html(f"<style>:root{{{variables}}}{css}</style>")


def brand():
    st.html('<div class="kurashi-brand"><span aria-hidden="true">食</span>暮らしの食卓</div>')


def home_banner():
    with st.container(key="kurashi_hero"):
        copy, art = st.columns([1, 1], vertical_alignment="center")
        with copy:
            st.title("今日の食卓を、無理なく。")
            st.write("献立を考える日も、食事の用意が難しい日も。")
            if st.button("今夜の献立を探す", key="home_find_dinner", type="primary"):
                st.session_state.next_main_tab = "献立"
                st.rerun()
            st.html('<a href="#life-support">食費・健康の相談先を探す</a>')
            if not st.session_state.get("is_logged_in"):
                st.html('<a href="#today-check-in">今日のスタンプを試す ↓</a>')
        with art:
            st.image(ASSETS / "dinner-illustration.jpg", alt="鮭と青菜、ご飯、みそ汁を並べた手描き風の食卓", width="stretch")


def photo_for(text, meal_label=None):
    path, subject = menu_photo(text)
    caption = f"{subject}の参考写真"
    if meal_label:
        caption = f"{meal_label} · {caption}"
    st.image(path, caption=caption, alt=f"{subject}の盛り付け例", width="stretch")


def recipe_card(meal, people, label):
    with st.container(border=True, key=f"recipe_{label}"):
        image, details = st.columns([1, 1.2], vertical_alignment="center")
        with image:
            photo_for(meal["main"]["title"])
        with details:
            st.caption(f"{label}　{people}人分　調理の目安 約{meal['minutes']}分")
            st.subheader(meal["main"]["title"])
            cost = estimate_meal_cost(meal)
            if cost is not None:
                family_cost = f"（{people}人分 約{estimate_meal_cost(meal, people):,}円）" if people > 1 else ""
                st.write(f"**食材費の目安　1人 約{cost:,}円**{family_cost}")
            st.caption(f"使う野菜　1人分 約{vegetable_grams(meal)}g")
            for role, role_label in ROLES.items():
                st.write(f"**{role_label}**　{meal[role]['title']}")
        with st.expander("材料の分量と作り方"):
            for role in ROLES:
                dish = meal[role]
                st.markdown(f"**{dish['title']}**")
                st.write("、".join(
                    f"{name} {quantity(amount * people, unit)}"
                    for name, amount, unit in dish["ingredients"]
                ))
                st.write(dish["method"])
            st.markdown(
                "[食材の扱いと加熱の目安](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/shokuhin/syokuchu/01_00008.html)"
            )


def _remember(meals):
    history = st.session_state.get("simple_dinner_history", [])
    for meal in meals:
        key = meal_key(meal)
        history = [seen for seen in history if seen != key] + [key]
    st.session_state.simple_dinner_history = history[-70:]


def render_dinner():
    st.subheader("食材から夕食を探す")
    with st.form("simple_dinner"):
        first, second, third = st.columns(3)
        people = first.selectbox("人数", range(1, 7), format_func=lambda n: f"{n}人分")
        limit = second.selectbox("調理時間", [15, 20, 25, 40], index=1, format_func=lambda n: f"{n}分以内")
        count = third.selectbox("日数", [1, 7], format_func=lambda n: "今夜" if n == 1 else "1週間")
        budget, order = st.columns(2)
        ceiling = budget.number_input("1人1食の予算（円・任意）", min_value=1, value=None, step=50, placeholder="例 250")
        priority = order.selectbox("優先すること", list(DINNER_PRIORITIES), format_func=DINNER_PRIORITIES.__getitem__)
        stock = st.multiselect("家にある食材", [food for food in FOODS if food not in PANTRY], placeholder="食材名を入力")
        with st.expander("使わない食材・基本の調味料"):
            excluded = st.multiselect("好みで使わない食材", FOODS, placeholder="食材名を入力")
            pantry = st.checkbox("基本の調味料は家にある", value=True)
            st.caption("、".join(sorted(PANTRY - {"水"})))
        shopping = st.radio("買い足し", ["指定なし", "なるべく少なく", "買い足しなし"], horizontal=True)
        submitted = st.form_submit_button("献立を探す", type="primary")
    st.caption("時間は炊飯を除いた目安です。療養食や食物アレルギーは専門職や商品の原材料表示で確認してください。")
    st.caption("予算は家にあるものも含めた食材の使用分です。アプリ内の参考単価で計算しており、お店の価格や袋・パックで買う金額とは異なります。")

    if submitted:
        available = set(stock) | (PANTRY if pantry else {"水"})
        matching = dinner_candidates(limit, available, set(excluded), shopping == "買い足しなし")
        candidates = within_dinner_budget(matching, ceiling)
        st.session_state.simple_dinner_plan = {
            "candidates": candidates, "count": count, "people": people, "stock": available,
            "prefer_fewer": shopping == "なるべく少なく", "priority": priority, "ceiling": ceiling,
            "lowest_cost": min((meal["cost"] for meal in matching if meal["cost"] is not None), default=None),
        }
        st.session_state.simple_dinner_results = select_dinners(
            candidates, count, st.session_state.get("simple_dinner_history", []),
            shopping == "なるべく少なく", priority=priority,
        )
        _remember(st.session_state.simple_dinner_results)
    plan = st.session_state.get("simple_dinner_plan")
    if plan is None:
        return
    meals = st.session_state.simple_dinner_results
    people = plan["people"]
    count = plan["count"]
    candidates = plan["candidates"]
    priority = plan.get("priority", "variety")
    if not meals:
        lowest = plan.get("lowest_cost")
        if lowest is not None and plan.get("ceiling") is not None:
            st.info(f"この予算に収まる献立が見つかりませんでした。他の条件を保つと、最も安い候補は1人約{lowest:,}円です。")
        else:
            st.info("条件に合う献立がありませんでした。時間や手持ち食材を変えて探せます。")
        if st.button("買い物や食事の用意を相談する", key="dinner_support"):
            st.session_state.next_main_tab = "ホーム"
            st.session_state.consult_topic_seed = "money" if plan.get("ceiling") is not None else "shopping"
            st.rerun()
        return
    if len(meals) < count:
        st.info(f"主菜が重ならない候補を{len(meals)}日分表示しています。")
    if st.button("別の献立を探す", key="simple_dinner_another", disabled=len(candidates) < 2):
        others = candidates
        if count == 1:
            others = [meal for meal in candidates if meal_key(meal) != meal_key(meals[0])]
        meals = select_dinners(others, count, st.session_state.simple_dinner_history, plan["prefer_fewer"], discover=True, priority=priority)
        st.session_state.simple_dinner_results = meals
        _remember(meals)

    favorites = st.session_state.setdefault("simple_dinner_favorites", {})
    for index, meal in enumerate(meals):
        label = "今夜の夕食" if count == 1 else f"{index + 1}日目の夕食"
        recipe_card(meal, people, label)
        sides = [
            alternative for alternative in candidates if alternative["main"] == meal["main"]
            and alternative["staple"] == meal["staple"] and alternative["side"] != meal["side"]
        ]
        swap, favorite = st.columns(2)
        if swap.button("副菜を替える", key=f"simple_swap_{index}", disabled=not sides):
            meals[index] = select_dinners(sides, 1, st.session_state.simple_dinner_history, plan["prefer_fewer"], priority=priority)[0]
            _remember([meals[index]])
            st.rerun()
        key = (*meal_key(meal), people)
        if favorite.button("保存を取り消す" if key in favorites else "お気に入りに保存", key=f"simple_save_{index}"):
            if key in favorites:
                del favorites[key]
            else:
                favorites[key] = (meal, people)
            st.rerun()
    items = shopping_list(meals, people, plan["stock"])
    st.markdown("#### 買い足すもの")
    estimated = estimate_ingredient_cost(items)
    if items and estimated is not None:
        st.caption(f"買い足す食材の使用分　合計 約{estimated:,}円。袋やパックの購入額は店頭で確認してください。")
    if not items:
        st.write("買い足しなし")
    for name, amount, unit in items:
        st.checkbox(f"{name} {quantity(amount, unit)}", key=f"dinner_bought_{name}_{unit}_{amount}")
    sections = []
    for index, meal in enumerate(meals):
        lines = [f"{people}人分　調理の目安 約{meal['minutes']}分"]
        cost = estimate_meal_cost(meal)
        if cost is not None:
            lines.append(f"1人分の食材費 約{cost:,}円（参考単価の使用分）")
        for role in ROLES:
            dish = meal[role]
            lines.append(f"{ROLES[role]}　{dish['title']}")
            lines.append("、".join(f"{name} {quantity(amount * people, unit)}" for name, amount, unit in dish["ingredients"]))
            lines.append(dish["method"])
        sections.append((f"{index + 1}日目の夕食" if count > 1 else "今夜の夕食", lines))
    shopping_text = [f"{name} {quantity(amount, unit)}" for name, amount, unit in items] or ["買い足しなし"]
    st.download_button("夕食の献立カードをPDF保存", build_meal_card("暮らしの食卓", sections, shopping_text),
                       file_name="dinner-card.pdf", mime="application/pdf", on_click="ignore")


def render_dinner_favorites():
    favorites = st.session_state.get("simple_dinner_favorites", {})
    if favorites:
        st.markdown("#### 保存した夕食")
    for number, (key, (meal, people)) in enumerate(favorites.items()):
        recipe_card(meal, people, f"保存した夕食 {number + 1}")
        if st.button("この夕食の保存を取り消す", key=f"forget_dinner_{key}"):
            del favorites[key]
            st.rerun()


def _older_contact(local, town):
    center = next((entry for entry in CONTACTS if town in entry["area"]), None) if local else None
    if center:
        return {**center, "description": f"高齢の方やご家族の暮らし・介護の相談先です。担当地域は{'・'.join(center['area'])}です。"}
    if local:
        return dict(title="西東京市 地域包括支援センター", description="町名ごとの担当窓口を市のページで確認できます。",
                    url=DIRECTORY["centersSource"])
    return dict(title="お住まいの地域の地域包括支援センター",
                description="高齢の方の介護や、食事・暮らしの相談ができます。ご家族からも相談できます。",
                url=DIRECTORY["nationalCenters"])


def _consultation_contacts(topic, region, town, for_older):
    local = region == "西東京市"
    if topic == "care" or (topic == "shopping" and for_older):
        yield _older_contact(local, town)
        if local and topic == "shopping":
            yield dict(title="西東京市 高齢者見守り配食サービス", description="対象要件と申し込み先を市のページで確認できます。",
                       url="https://www.city.nishitokyo.lg.jp/kenko_hukusi/koreisyasien/kaigo_dailylife/haisyoku202107.html")
    elif topic == "unsure":
        yield DIRECTORY["localGeneral"] if local else dict(
            title="お住まいの市区町村の福祉相談窓口",
            description="福祉の担当窓口に「困りごとが重なり、どこに相談すればよいかわからない」と伝え、地域の窓口を尋ねてください。",
            url=DIRECTORY["nationalLiving"], link="厚生労働省の相談窓口一覧を見る",
        )
    elif topic == "nutrition":
        yield DIRECTORY["localNutrition"] if local else dict(
            title="市区町村の保健センター",
            description="お住まいの自治体に「栄養相談」や「食生活相談」とお尋ねください。",
        )
    elif topic == "feelings":
        yield DIRECTORY["mentalHealth"]
    else:
        yield DIRECTORY["localLiving"] if local else dict(
            title="お住まいの地域の自立相談支援機関",
            description="お住まいの市区町村に、生活や食費について相談できる窓口を確認できます。",
            url=DIRECTORY["nationalLiving"],
        )
    if for_older and topic in {"money", "nutrition", "unsure"}:
        yield _older_contact(local, town)


def render_consultation():
    st.header("暮らしの困りごとを相談する", anchor="life-support")
    st.write("食費や食事の心配が重なっていたり、使える制度がわからなかったりするときも、相談先を探せます。")
    seed = st.session_state.pop("consult_topic_seed", None)
    if seed:
        st.session_state.consult_topic = seed
    topic = st.selectbox("何に困っていますか", list(TOPICS), format_func=lambda key: TOPICS[key]["label"], key="consult_topic")
    topic_data = TOPICS[topic]
    region = st.radio("相談したい方の地域", ["西東京市以外・わからない", "西東京市"], horizontal=True)
    for_older = topic == "care" or (
        topic in {"money", "nutrition", "shopping", "unsure"}
        and st.checkbox("高齢のご本人や、ご家族のことも相談したい")
    )
    town = st.selectbox("相談したい方が住む町名（任意）", ["選ばずに探す", *TOWNS]) if region == "西東京市" and for_older else None
    circumstances = st.multiselect("当てはまること（任意）", topic_data["options"], key=f"consult_{topic}_options", placeholder="当てはまる項目を選ぶ")
    selection = (topic, region, town, for_older, tuple(circumstances))
    if st.button("相談先とメモを見る", key="show_consultation", type="primary"):
        st.session_state.consult_selection = selection
        st.session_state.consult_consent = False
        about = "、".join(circumstances) or topic_data["label"]
        st.session_state.consult_memo = f"「{about}」のことで相談したいです。\n{topic_data['firstQuestion']}。"
        st.session_state.consult_added = []
    if st.session_state.get("consult_selection") == selection:
        if "今日食べるものの用意が難しい" in circumstances:
            st.info("相談の最初に「今日食べるものの用意が難しい」と伝え、今利用できる食料支援があるか尋ねてください。")
        for contact in _consultation_contacts(topic, region, town, for_older):
            with st.container(border=True):
                st.subheader(contact["title"])
                st.write(contact["description"])
                for phone, label in contact.get("phones", []):
                    st.markdown(f"[{label + ' ' if label else ''}{phone} に電話](tel:{phone})")
                if contact.get("url"):
                    st.link_button(contact.get("link", "公式ページを開く"), contact["url"])
        ai_enabled = not TRIAL_MODE and bool(GEMINI_API_KEY and str(get_setting("ENABLE_LOCAL_CONSULT_AI", "")).lower() in {"1", "true"})
        if ai_enabled:
            consent = st.checkbox("私は18歳以上です。選択したテーマと項目をGeminiへ送ることに同意します。", key="consult_consent")
            if st.button("AIで聞きたいことを整理", disabled=not consent):
                try:
                    indexes = [topic_data["options"].index(value) for value in circumstances]
                    found = select_questions(GEMINI_API_KEY, topic, indexes)
                    new = [key for key in found if key not in st.session_state.consult_added]
                    if new:
                        questions = DIRECTORY["followupQuestions"]
                        st.session_state.consult_memo += "\n\n" + "\n".join(f"・{questions[key]}。" for key in new)
                        st.session_state.consult_added.extend(new)
                    else:
                        st.info("追加の質問はありませんでした。")
                except (URLError, OSError, ValueError, KeyError, TypeError, AttributeError, IndexError):
                    st.warning("AIに接続できませんでした。相談先と作成済みのメモは引き続き使えます。")
        memo = st.text_area("電話や面談で使う相談メモ", key="consult_memo", height=145, max_chars=1500)
        st.download_button("相談メモを保存", memo, file_name="相談メモ.txt", mime="text/plain", on_click="ignore", disabled=not memo.strip())
        st.caption("メモは窓口への電話や面談で使えます。アプリから窓口へ自動送信されません。")
    st.markdown(
        "急病やけがで救急車が必要なときは **119**。つらさを人に話したいときは "
        "[＃いのちSOS](https://www.lifelink.or.jp/inochisos/?oai_link_source=model_response_hotline) に相談できます。"
    )
