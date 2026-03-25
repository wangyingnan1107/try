import json
import unittest
from unittest.mock import patch

from server.llm_service import analyze_post, analyze_multiple_posts, SYSTEM_PROMPT, AGGREGATION_SYSTEM_PROMPT
from server.schemas import RawPost


class FakeSingleResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        payload = {
            "summary": {"one_liner": "这篇帖子可用于学习安全控制落地。", "keywords": ["安全", "控制", "落地"]},
            "learning_insight": {
                "core_takeaways": ["先做网关签名校验，再做权限分层。"],
                "key_concepts": [{"term": "RBAC", "explanation": "角色权限控制", "application": "操作级权限"}],
                "method_playbook": ["梳理高风险操作", "给高风险操作加二次确认"],
                "evidence_snippets": ["核心是“安全方案控制”三层：1) API 网关签名校验；2) 操作级 RBAC；3) 风险指令二次确认。"],
                "pitfalls": ["只看功能不做权限边界"],
                "prerequisites": ["理解鉴权与签名基础"],
                "practice_tasks": [{"task": "实现一条风险操作二次确认", "difficulty": "入门", "expected_outcome": "误触发下降"}],
                "reflection_questions": ["你当前系统的高风险操作是什么？"],
                "next_actions_24h": ["给删除操作接入二次确认。"]
            }
        }
        return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}


class FakeAggregationResponse:
    status_code = 200

    def json(self):
        payload = {
            "topic_overview": "AI工程安全实践",
            "domain_knowledge": ["网关鉴权", "RBAC"],
            "learning_path": ["先实现签名校验", "再接权限控制"],
            "extended_insight": "强调落地顺序。",
            "concept_map": ["签名->鉴权->授权"],
            "skill_ladder": ["入门: 签名", "中级: RBAC"],
            "implementation_plan": ["本周完成签名校验", "下周完成风险确认"],
            "cross_post_consensus": ["都强调先控制风险再扩功能"],
            "cross_post_conflicts": ["是否默认全量开启严格模式"],
            "checkpoint_quiz": ["为什么先签名再授权？"]
        }
        return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}


class LearningAssistantModeTests(unittest.TestCase):
    def test_prompts_should_focus_on_learning_assistant(self):
        self.assertIn("学习教练型助理", SYSTEM_PROMPT)
        self.assertIn("跨帖子学习助理", AGGREGATION_SYSTEM_PROMPT)

    @patch("server.llm_service.requests.post", return_value=FakeSingleResponse())
    def test_single_post_should_output_learning_insight(self, _mock_post):
        post = RawPost(
            source_id="p1",
            url="https://example.com/post",
            title="Openclaw 安全方案控制实战",
            content="核心是安全方案控制三层。",
            author={"name": "tester", "uid": "u1"},
            media={"images": [], "video_cover": None},
            stats={"likes": 1, "collects": 1, "comments_count": 0},
            top_comments=[],
            tags=[]
        )
        result = analyze_post(post)
        self.assertIsNotNone(result.learning_insight)
        self.assertGreaterEqual(len(result.learning_insight.practice_tasks), 1)
        self.assertTrue(any("安全方案控制" in item for item in result.learning_insight.evidence_snippets))

    @patch("server.llm_service.requests.post", return_value=FakeAggregationResponse())
    def test_aggregation_should_include_learning_roadmap_fields(self, _mock_post):
        post = RawPost(
            source_id="p2",
            url="https://example.com/post2",
            title="Openclaw 复盘",
            content="安全方案控制在网关层开始。",
            author={"name": "tester", "uid": "u2"},
            media={"images": [], "video_cover": None},
            stats={"likes": 1, "collects": 1, "comments_count": 0},
            top_comments=[],
            tags=[]
        )
        report = analyze_multiple_posts([post])
        self.assertIsNotNone(report.summary)
        self.assertGreaterEqual(len(report.learning_insight.core_takeaways), 1)
        self.assertGreaterEqual(len(report.implementation_plan), 1)
        self.assertGreaterEqual(len(report.checkpoint_quiz), 1)


if __name__ == "__main__":
    unittest.main()
