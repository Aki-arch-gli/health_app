import json
import os
from modules.runtime_paths import NEWS_FILE

def load_news():

    if not os.path.exists(NEWS_FILE):

        return {
            "comment": "今日は健康に気を付けて過ごしましょう😊"
        }

    try:

        with open(
            NEWS_FILE,
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if not isinstance(data, dict):
                return {
                    "comment": "今日は健康に気を付けて過ごしましょう😊"
                }

            if "comment" not in data:
                data["comment"] = "今日は健康に気を付けて過ごしましょう😊"

            return data

    except Exception:

        return {
            "comment": "今日は健康に気を付けて過ごしましょう😊"
        }
