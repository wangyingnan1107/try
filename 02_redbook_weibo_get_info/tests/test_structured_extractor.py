import json
import unittest
from pathlib import Path

from server.schemas import RawPost
from server.structured_extractor import extract_structured_post, build_weighted_context


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "xiaohongshu_20_posts.json"


class StructuredExtractorTests(unittest.TestCase):
    def setUp(self):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.posts = [RawPost(**item) for item in payload]

    def test_should_load_20_posts(self):
        self.assertEqual(len(self.posts), 20)

    def test_char_retention_ratio_should_be_at_least_98_percent(self):
        ratios = [extract_structured_post(post).metrics["char_retention_ratio"] for post in self.posts]
        avg_ratio = sum(ratios) / len(ratios)
        self.assertGreaterEqual(avg_ratio, 0.98)

    def test_should_preserve_complex_tokens(self):
        target = self.posts[0]
        extracted = extract_structured_post(target)
        segment_types = [segment.segment_type for segment in extracted.segments]
        self.assertIn("code_block", segment_types)
        self.assertIn("topic", segment_types)
        self.assertIn("mention", segment_types)
        self.assertIn("emoji", segment_types)

    def test_keyword_recall_should_be_at_least_95_percent(self):
        keywords = ["openclaw", "安全方案控制", "网关", "RBAC", "yaml"]
        extracted = extract_structured_post(self.posts[0])
        text = extracted.normalized_text.lower()
        hit = sum(1 for keyword in keywords if keyword.lower() in text)
        recall = hit / len(keywords)
        self.assertGreaterEqual(recall, 0.95)

    def test_weighted_context_should_include_evidence(self):
        extractions = [extract_structured_post(post) for post in self.posts]
        context, evidence, diagnostics = build_weighted_context(extractions)
        self.assertGreater(len(context), 0)
        self.assertGreaterEqual(diagnostics["avg_char_retention_ratio"], 0.98)
        self.assertTrue(any("安全方案控制" in item for item in evidence))


if __name__ == "__main__":
    unittest.main()
