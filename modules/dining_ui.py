import json
from math import asin, cos, radians, sin, sqrt
from urllib.parse import urlencode

import streamlit as st

from modules.dinner import ROOT
from modules.kurashi_ui import open_consultation


with (ROOT / "data" / "dining_directory.json").open(encoding="utf-8") as source:
    DIRECTORY = json.load(source)

LOCATE = st.components.v2.component(
    "kurashi_location",
    html='<button type="button">現在地を取得する</button>',
    css="""
    button {
        padding: .5rem .85rem;
        border: 1px solid var(--st-text-color);
        border-radius: .55rem;
        background: var(--st-background-color);
        color: var(--st-text-color);
        font: inherit;
        cursor: pointer;
    }
    """,
    js="""
    export default function ({parentElement, setTriggerValue}) {
        const button = parentElement.querySelector('button');
        button.onclick = () => {
            if (!navigator.geolocation) {
                setTriggerValue('position', {error: true});
                return;
            }
            button.disabled = true;
            const finish = (value) => {
                button.disabled = false;
                setTriggerValue('position', value);
            };
            navigator.geolocation.getCurrentPosition(
                ({coords}) => finish({
                    lat: Number(coords.latitude.toFixed(3)),
                    lon: Number(coords.longitude.toFixed(3)),
                }),
                () => finish({error: true}),
                {enableHighAccuracy: false, timeout: 10000, maximumAge: 60000},
            );
        };
    }
    """,
)


def straight_line_km(origin, destination):
    lat1, lon1 = map(radians, origin)
    lat2, lon2 = map(radians, destination)
    square = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(min(1.0, square)))


def matching_places(origin, radius_km, ceiling, vegetables_only, category=None):
    options = []
    for place in DIRECTORY["places"]:
        if category is not None and DIRECTORY["categories"][place["group"]] != category:
            continue
        distance = straight_line_km(origin, (place["lat"], place["lon"]))
        if distance > radius_km:
            continue
        meals = [
            meal for meal in DIRECTORY["menus"][place["group"]]
            if (not vegetables_only or meal["vegetables"]) and (ceiling is None or meal["price"] <= ceiling)
        ]
        if meals:
            options.append((place, distance, sorted(meals, key=lambda meal: meal["price"])))
    return sorted(options, key=lambda option: option[1])


def maps_search(query):
    return "https://www.google.com/maps/search/?" + urlencode({"api": 1, "query": query})


def render_dining():
    st.subheader("近くの外食マップ")
    st.write(f"西東京市と近隣の登録店{len(DIRECTORY['places'])}件から、予算に合うメニュー例を探せます。")
    areas = DIRECTORY["areas"]
    choice = st.selectbox("探す場所", [*areas, "現在地", "別の地域"], key="dining_area")
    if choice != "現在地":
        st.session_state.pop("dining_location", None)
    if choice == "別の地域":
        area = st.text_input("駅名・市区町村名（任意）", max_chars=40, placeholder="例 立川駅")
        st.link_button("手頃なランチをGoogle マップで探す", maps_search(f"安い ランチ 定食 {area.strip()}"))
        st.link_button("野菜料理がある店をGoogle マップで探す", maps_search(f"野菜料理 定食 {area.strip()}"))
        st.caption("外部マップの検索結果では、価格とメニューを各店舗で確認してください。")
        return

    if choice == "現在地":
        st.caption("許可した場合、位置を丸めて距離計算と地図表示に使います。外食マップを離れると消去します。")
        location = LOCATE(key="dining_geolocation", on_position_change=lambda: None).position
        if isinstance(location, dict):
            lat, lon = location.get("lat"), location.get("lon")
            if type(lat) in (int, float) and type(lon) in (int, float) and -90 <= lat <= 90 and -180 <= lon <= 180:
                st.session_state.dining_location = (round(lat, 3), round(lon, 3))
            else:
                st.session_state.pop("dining_location", None)
                st.info("現在地を取得できませんでした。「探す場所」で駅を選んでも検索できます。")
        origin = st.session_state.get("dining_location")
        if origin is None:
            return
        if st.button("現在地の利用をやめる"):
            st.session_state.pop("dining_location", None)
            st.rerun()
    else:
        origin = areas[choice]

    left, right = st.columns(2)
    radius = left.selectbox("範囲（直線距離）", [1, 2, 3, 5], index=1, format_func=lambda km: f"{km}km以内")
    ceiling = right.number_input(
        "外食の予算（1人・円）", min_value=1, value=None, step=100, placeholder="例 600", key="dining_ceiling",
    )
    left, right = st.columns(2)
    categories = sorted(set(DIRECTORY["categories"].values()))
    category = left.selectbox("料理の種類", [None, *categories], format_func=lambda name: name or "指定なし")
    sort = right.radio("並べ方", ["近い順", "掲載メニューが安い順"], horizontal=True)
    vegetables = st.checkbox("野菜料理付きの組み合わせだけ")
    matches = matching_places(origin, radius, ceiling, vegetables, category)
    if not matches:
        without_limit = matching_places(origin, radius, None, vegetables, category)
        if without_limit:
            lowest = min(meals[0]["price"] for _, _, meals in without_limit)
            st.info(f"予算内のメニュー例はありませんでした。他の条件を保つと、登録店では税込{lowest:,}円からです。")
            st.button("予算を外して見る", on_click=lambda: st.session_state.update(dining_ceiling=None))
        elif matching_places(origin, radius, None, False):
            st.info("この範囲に登録店はあります。料理の種類や野菜料理の条件を変えると、別の候補を探せます。")
        else:
            st.info("この範囲にはアプリの登録店がありません。掲載エリアは西東京市と近隣です。")
        area = choice if choice in areas else ""
        term = "野菜料理 定食" if vegetables else "手頃な価格 ランチ 定食"
        st.link_button("Google マップで近くのお店を探す", maps_search(f"{term} {area}".strip()))
        if ceiling is not None:
            st.button("食費のことを相談する", on_click=open_consultation, args=("money",))
        return

    if sort == "掲載メニューが安い順":
        matches.sort(key=lambda match: (match[2][0]["price"], match[1]))
    st.write(f"条件に合う登録店 **{len(matches)}件**")
    pins = [{"lat": origin[0], "lon": origin[1], "color": "#235da4"}]
    pins += [{"lat": place["lat"], "lon": place["lon"], "color": "#2d6040"} for place, _, _ in matches]
    st.map(pins, color="color", size=50, height=350, alt="外食候補の位置と検索の出発点")
    checked = DIRECTORY["checked_on"].replace("-", "/")
    st.caption(f"青は検索の出発点、緑は店舗です。価格は{checked}確認の公式メニューの税込例です。店舗・時間帯で変わることがあります。")
    for place, distance, meals in matches:
        with st.container(border=True):
            st.markdown(f"**{place['name']}**")
            cuisine = DIRECTORY["categories"][place["group"]]
            st.caption(f"{cuisine}　出発点から直線 約{round(distance * 1000 / 10) * 10:,}m")
            for meal in meals:
                st.write(f"{meal['title']}　**{meal['price']:,}円**")
                links = [f"[公式メニュー {index}]({url})" for index, url in enumerate(meal["sources"], 1)]
                st.markdown(" · ".join(links))
            with st.container(horizontal=True):
                st.link_button("公式の店舗情報", place["url"])
                st.link_button("地図で経路を見る", "https://www.google.com/maps/dir/?" + urlencode({
                    "api": 1, "destination": f"{place['lat']},{place['lon']}",
                }))
