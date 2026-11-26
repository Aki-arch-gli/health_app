import pandas as pd
import datetime
from modules.shopping import create_shopping_list

def load_menu():
    return pd.read_csv("data/menu_data.csv")

def current_season():
    month = datetime.datetime.now().month
    if month in [3, 4, 5]:
        return "春"
    elif month in [6, 7, 8]:
        return "夏"
    elif month in [9, 10, 11]:
        return "秋"
    else:
        return "冬"

def contains_food(row, food):
    text = f"{row.get('breakfast', '')} {row.get('lunch', '')} {row.get('dinner', '')}"
    return food in text

def generate_menu(
    age,
    disease,
    calorie,
    season="auto",
    style=None,
    difficulty=None,
    dislike=None,
    favorite_food=None,
    history=None
):
    age = int(age)
    calorie = int(calorie)
    disease = str(disease).strip()

    df = load_menu()

    # 年齢フィルター
    if "min_age" in df.columns and "max_age" in df.columns:
        df = df[(df["min_age"] <= age) & (df["max_age"] >= age)]

    # 疾患フィルター
    if "disease" in df.columns:
        df["disease"] = df["disease"].astype(str).str.strip()
        if disease in ["なし", "疾患なし"]:
            df = df[df["disease"].isin(["なし", "疾患なし"])]
        else:
            df = df[df["disease"] == disease]

    # 季節フィルター
    if season == "auto":
        season = current_season()
    if "season" in df.columns:
        df = df[(df["season"] == season) | (df["season"] == "通年")]

    # 🍱 料理スタイル（和洋中）フィルターの安全化（部分一致＆トリム）
    if style and style != "指定なし" and "japanese_style" in df.columns:
        style_clean = str(style).strip()
        filtered_df = df[df["japanese_style"].astype(str).str.contains(style_clean, na=False)]
        if len(filtered_df) > 0:
            df = filtered_df

    # ⚡ 難易度フィルター (difficulty / level 両対応)
    if difficulty and difficulty != "指定なし":
        diff_col = "difficulty" if "difficulty" in df.columns else ("level" if "level" in df.columns else None)
        if diff_col:
            difficulty_name = str(difficulty).strip()
            stars = {"簡単": "★", "普通": "★★", "本格的": "★★★"}
            filtered_df = df[df[diff_col].astype(str).str.strip().isin([difficulty_name, stars.get(difficulty_name)])]
            if len(filtered_df) > 0:
                df = filtered_df

    # 苦手食材フィルター
    if dislike:
        for food in dislike:
            if food:
                df = df[
                    ~(
                        df["breakfast"].astype(str).str.contains(food, na=False) |
                        df["lunch"].astype(str).str.contains(food, na=False) |
                        df["dinner"].astype(str).str.contains(food, na=False)
                    )
                ]

    # 🍖🐟 肉・魚料理希望フィルターのキーワード拡張
    if favorite_food and favorite_food != "指定なし":
        if favorite_food == "魚":
            fish = ["鮭", "さけ", "サケ", "さば", "サバ", "ぶり", "ブリ", "たら", "タラ", "あじ", "アジ", "白身魚", "さんま", "サンマ", "魚", "さわら", "サワラ", "赤魚", "ツナ", "エビ", "海老", "シーフード"]
            filtered_df = df[df.apply(lambda x: any(contains_food(x, f) for f in fish), axis=1)]
            if len(filtered_df) > 0:
                df = filtered_df

        elif favorite_food == "肉":
            meat = ["鶏", "チキン", "豚", "ポーク", "牛", "ビーフ", "肉", "ハンバーグ", "つくね", "ソーセージ", "ハム", "そぼろ"]
            filtered_df = df[df.apply(lambda x: any(contains_food(x, f) for f in meat), axis=1)]
            if len(filtered_df) > 0:
                df = filtered_df

    # 過去履歴除外
    if history and "id" in df.columns:
        filtered_df = df[~df["id"].isin(history)]
        if len(filtered_df) > 0:
            df = filtered_df

    if len(df) == 0:
        return None

    # カロリー差でソート
    if "calorie" in df.columns:
        df["diff"] = abs(df["calorie"] - calorie)
        df = df.sort_values("diff")

    candidates = df.head(15)
    menu = candidates.sample(1).iloc[0]

    # modules/menu_generator.py (最後の return 部分)

    return {
        "id": int(menu["id"]) if "id" in menu else 1,
        "朝食": menu.get("breakfast", ""),
        "昼食": menu.get("lunch", ""),
        "夕食": menu.get("dinner", ""),
        "理由": menu.get("reason", ""),
        "バランス": menu.get("balance", ""),
        "アドバイス": menu.get("advice", ""),
        "カロリー": int(menu.get("calorie", calorie)),
        "季節": menu.get("season", "通年"),
        "料理": menu.get("japanese_style", "和食"),
        "難易度": menu.get("difficulty", menu.get("level", "普通")),
        "買い物リスト": create_shopping_list({
            "朝食": str(menu.get("breakfast", "")),
            "昼食": str(menu.get("lunch", "")),
            "夕食": str(menu.get("dinner", ""))
        })
    }
