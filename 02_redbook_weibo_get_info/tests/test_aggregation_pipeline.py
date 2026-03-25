import json
import unittest
from pathlib import Path
from unittest.mock import patch

from server.llm_service import analyze_multiple_posts
from server.schemas import RawPost


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "xiaohongshu_20_posts.json"


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        payload = {
            "topic_overview": "AI工程与安全实践",
            "domain_knowledge": ["网关鉴权", "RBAC", "灰度发布"],
            "learning_path": ["先理解接口签名", "再实现规则引擎", "最后做灰度监控"],
            "extended_insight": "该批帖子强调工程落地。",
        }
        return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}


class AggregationPipelineTests(unittest.TestCase):
    def setUp(self):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.posts = [RawPost(**item) for item in payload]

    @patch("server.llm_service.requests.post", return_value=FakeResponse())
    def test_openclaw_security_text_should_exist_in_final_report(self, _mock_post):
        report = analyze_multiple_posts(self.posts)
        self.assertIn("原文证据片段", report.extended_insight)
        self.assertIn("安全方案控制", report.extended_insight)
        self.assertGreaterEqual(report.extraction_diagnostics.get("avg_char_retention_ratio", 0), 0.98)
        self.assertGreaterEqual(len(report.source_evidence), 1)


if __name__ == "__main__":
    unittest.main()
