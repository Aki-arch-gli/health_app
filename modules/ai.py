from google import genai
from config import GEMINI_API_KEY
import json
from config import AI_MODEL

def ask_ai(prompt):
    if not GEMINI_API_KEY:
        raise RuntimeError("献立・ニュースの生成にはGEMINI_API_KEYの設定が必要です。")
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODELS = [
      "gemini-3.5-flash",
      "gemini-3.1-flash-lite",
       "gemini-2.0-flash",
      "gemini-flash-latest",
    ]

    last_error = ""

    for model in MODELS:

        try:
            print("AI_MODEL =", AI_MODEL)

            response = client.models.generate_content(

                model=model,

                contents=prompt

            )

            return response.text

        except Exception as e:

            last_error = str(e)

    raise Exception(last_error)

def create_prompt(age, disease, calorie, simple=False):

    if simple:

        return f"""
あなたは高齢者専門の管理栄養士です。

対象
・年齢：{age}歳
・疾患：{disease}
・必要カロリー：約{calorie}kcal

必ず以下の形式だけで回答してください。

🌅 朝食
料理名だけを書く

🌞 昼食
料理名だけを書く

🌙 夕食
料理名だけを書く

🔥 カロリー
数字だけを書く

理由
短く書く

バランス
短く書く

アドバイス
短く書く

料理名以外の説明文を朝食・昼食・夕食欄には入れないでください。
"""


    return f"""
あなたは日本の管理栄養士です。

年齢：{age}歳
疾患：{disease}
必要カロリー：約{calorie}kcal

朝食・昼食・夕食について

・料理名
・カロリー
・栄養バランス

を書いてください。

最後に

【この献立の理由】

も説明してください。
"""


def generate_ai_menu(
    age,
    disease,
    calorie,
    simple=False
):

    prompt = create_prompt(
        age,
        disease,
        calorie,
        simple
    )

    try:

        return ask_ai(prompt)

    except Exception:

        return "AI献立を作成できませんでした。"


def generate_weekly_ai_menu(

    age,

    disease,

    calorie

):

    prompt = ...

    try:

        return ask_ai(prompt)

    except Exception:

        return "週間献立を作成できませんでした。"

def generate_daily_news():

    prompt = """
高齢者向け健康ワンポイントを100文字以内で作ってください。

JSON形式のみ。

{
    "comment":"..."
}
"""

    try:

        text = ask_ai(prompt)

        import json

        text = text.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

        return json.loads(text)

    except Exception:

        return {

            "comment":

            "今日はこまめな水分補給を心がけましょう。"

        }
