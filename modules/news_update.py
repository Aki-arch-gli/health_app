import json

from datetime import datetime

from modules.ai import generate_daily_news
from modules.runtime_paths import NEWS_FILE


def update_news():

    print("update_news開始")

    news = generate_daily_news()

    print(news)

    with open(
        NEWS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            news,
            f,
            ensure_ascii=False,
            indent=4
        )
