from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from ai_provider import AIProviderError  # noqa: E402
from hotspot_recommendation_service import (  # noqa: E402
    _apply_ai_results,
    local_recommendations,
    recommend_hotspots,
)


STYLE = {
    "name": "测试号",
    "industry": "教育",
    "topics": ["校园活动报道", "科普文章"],
    "target_audience": "学生家长和教师",
    "blacklist": {"words": [], "topics": []},
}


def hotspot(item_id: str, title: str, heat: float) -> dict:
    return {
        "hotspot_id": item_id,
        "title": title,
        "score": heat,
        "hot_normalized": heat,
        "platform_count": 1,
        "sources": ["微博"],
        "source_details": [],
    }


class FakeProvider:
    def generate_json(self, **_: object) -> dict:
        return {
            "recommendations": [
                {
                    "id": "edu",
                    "relevance": 92,
                    "angle_value": 86,
                    "reason": "与教育和学生成长方向高度相关",
                    "matched_topics": ["教育", "学生成长"],
                    "angle": "从家庭与学校如何共同支持学生实践切入",
                    "risk_level": "low",
                    "risk_notice": "",
                }
            ]
        }


class FailingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_json(self, **_: object) -> dict:
        self.calls += 1
        raise AIProviderError("temporary failure")


class HotspotRecommendationTests(unittest.TestCase):
    def test_local_profile_prefers_matching_education_topic(self) -> None:
        items = [
            hotspot("ent", "明星演唱会登上热搜", 100),
            hotspot("edu", "学生暑假参加科技实践活动", 72),
        ]

        result = local_recommendations(items, STYLE, limit=2)

        self.assertEqual(result[0]["hotspot_id"], "edu")
        self.assertIn("学生", result[0]["matched_topics"])

    def test_blacklisted_topic_is_removed(self) -> None:
        style = {**STYLE, "blacklist": {"words": [], "topics": ["娱乐八卦"]}}
        items = [
            hotspot("blocked", "娱乐八卦今日盘点", 100),
            hotspot("edu", "校园科技节开幕", 60),
        ]

        result = local_recommendations(items, style, limit=5)

        self.assertEqual([item["hotspot_id"] for item in result], ["edu"])

    @patch("hotspot_recommendation_service.build_provider", return_value=FakeProvider())
    def test_ai_result_uses_weighted_score_and_keeps_angle(self, _build_provider) -> None:
        payload = {"items": [hotspot("edu", "学生暑假参加科技实践活动", 80)]}

        result = recommend_hotspots(
            hotspot_payload=payload,
            style=STYLE,
            config={"ai": {"api_key": "test", "model": "test"}},
            force_refresh=True,
        )

        self.assertEqual(result["mode"], "ai")
        self.assertEqual(result["items"][0]["recommendation_score"], 86.6)
        self.assertIn("家庭与学校", result["items"][0]["suggested_angle"])

    def test_ai_failure_retries_and_fallback_excludes_unmatched_topics(self) -> None:
        provider = FailingProvider()
        payload = {
            "items": [
                hotspot("ent", "明星演唱会登上热搜", 100),
                hotspot("edu", "学生暑假参加科技实践活动", 72),
            ]
        }

        with patch("hotspot_recommendation_service.build_provider", return_value=provider):
            result = recommend_hotspots(
                hotspot_payload=payload,
                style=STYLE,
                config={"ai": {"api_key": "test", "model": "test"}},
                force_refresh=True,
            )

        self.assertEqual(provider.calls, 2)
        self.assertEqual(result["mode"], "local")
        self.assertEqual([item["hotspot_id"] for item in result["items"]], ["edu"])

    def test_contradictory_ai_angle_falls_back_to_local_angle(self) -> None:
        item = {
            **hotspot("job", "男子面试被拒收到茶水费", 80),
            "local_relevance": 40,
            "local_angle_value": 60,
            "recommendation_reason": "可讨论求职沟通与职业教育",
            "suggested_angle": "从职业教育和求职沟通规范切入",
            "matched_topics": ["职业教育"],
            "risk_level": "low",
            "risk_notice": "",
        }
        raw = {
            "recommendations": [
                {
                    "id": "job",
                    "relevance": 70,
                    "angle_value": 70,
                    "reason": "面试话题与职业教育相关",
                    "matched_topics": ["职业教育"],
                    "angle": "从面试成功案例谈学生综合素养",
                    "risk_level": "low",
                    "risk_notice": "",
                }
            ]
        }

        result = _apply_ai_results([item], raw)

        self.assertEqual(result[0]["suggested_angle"], "从职业教育和求职沟通规范切入")


if __name__ == "__main__":
    unittest.main()
