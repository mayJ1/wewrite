from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from hotspot_service import merge_hotspots, parse_baidu  # noqa: E402


class HotspotServiceTests(unittest.TestCase):
    def test_baidu_uses_index_when_hot_score_is_missing(self) -> None:
        data = {
            "data": {
                "cards": [
                    {
                        "content": [
                            {
                                "content": [
                                    {"word": "第一条热点", "index": 1, "url": "https://example.com/1"},
                                    {"word": "第二条热点", "index": 2, "url": "https://example.com/2"},
                                ]
                            }
                        ]
                    }
                ]
            }
        }

        items = parse_baidu(data)

        self.assertEqual([item["rank"] for item in items], [1, 2])
        self.assertEqual([item["hot"] for item in items], [0, 0])

    def test_merge_preserves_cross_platform_sources(self) -> None:
        items = [
            {"title": "同一 热点！", "source": "微博", "hot": 1000, "rank": 1, "url": "w", "description": "爆"},
            {"title": "同一热点", "source": "百度", "hot": 0, "rank": 2, "url": "b", "description": ""},
            {"title": "另一个热点", "source": "今日头条", "hot": 900, "rank": 1, "url": "t", "description": ""},
        ]

        result = merge_hotspots(items)
        merged = next(item for item in result if item["platform_count"] == 2)

        self.assertEqual(merged["sources"], ["微博", "百度"])
        self.assertEqual(len(merged["source_details"]), 2)
        self.assertEqual(merged["title"], "同一 热点！")


if __name__ == "__main__":
    unittest.main()
