import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import database


class AlbumVisibilityTests(unittest.TestCase):
    def test_private_and_legacy_restricted_posts_stay_with_the_author(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch("modules.database.DB_NAME", str(Path(folder) / "test.db")))
        database.create_tables()
        database.update_schema_for_roadmap()
        posts = [
            "[🔒 自分だけ] 下書き",
            "[🔒 家族のみ（ご家族スマホ限定）] 過去の限定投稿",
            "[🏢 施設内のみ（スタッフ・入所者へ）] 施設限定",
            "[🌐 ログイン中の参加者に公開] 公開投稿",
        ]
        for message in posts:
            database.add_post("author", message)
        self.assertEqual([row[2] for row in database.get_posts("viewer")], [posts[-1]])
        self.assertEqual([row[2] for row in database.get_posts()], [posts[-1]])
        self.assertEqual({row[2] for row in database.get_posts("author")}, set(posts))
        self.assertEqual([row["message"] for row in database.get_posts_filtered(viewer_name="viewer")], [posts[-1]])
