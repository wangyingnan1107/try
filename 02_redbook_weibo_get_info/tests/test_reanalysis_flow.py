import unittest
from pathlib import Path


class ReanalysisFlowTests(unittest.TestCase):
    def test_index_should_always_render_analyze_button(self):
        html = Path("server/templates/index.html").read_text(encoding="utf-8")
        self.assertNotIn('v-if="!selectedPost.insight"', html)
        self.assertIn("🔁 重新分析", html)
        self.assertIn("⏳ 分析中...", html)

    def test_list_posts_should_query_latest_insight(self):
        code = Path("server/main.py").read_text(encoding="utf-8")
        self.assertIn("SELECT MAX(id) FROM insights", code)

    def test_database_init_should_include_version_fields(self):
        code = Path("server/database.py").read_text(encoding="utf-8")
        self.assertIn('"version"', code)
        self.assertIn('"is_latest"', code)


if __name__ == "__main__":
    unittest.main()
