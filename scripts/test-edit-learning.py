#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

import draft_service  # noqa: E402
import edit_learning_service as learning  # noqa: E402


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_json(self, **_: object) -> dict:
        self.calls += 1
        return {
            "summary": "用户缩短了段落，并把标题改得更直接。",
            "rules": [
                {
                    "key": "shorter_paragraphs",
                    "type": "length",
                    "rule": "正文每段尽量控制在三句话以内。",
                    "evidence": "用户拆分并删减了多个长段落。",
                    "confidence": 0.72,
                },
                {
                    "key": "direct_titles",
                    "type": "title",
                    "rule": "标题直接点明活动主题，避免空泛口号。",
                    "evidence": "用户将口号式标题改成活动主题。",
                    "confidence": 0.68,
                },
            ],
        }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="wewrite-learning-") as temp:
        lessons_dir = Path(temp) / "lessons"
        learning.LESSONS_DIR = lessons_dir
        learning.STORE_PATH = lessons_dir / "edit-learning.json"
        provider = FakeProvider()
        provider_factory = lambda _: provider

        original = {
            "title": "携手逐梦 共赴未来",
            "digest": "校园科技活动顺利举行。",
            "body": learning.extract_editorial_text(
                "<section><p>第一段内容很长，包含较多重复表达。</p><p>第二段介绍活动过程。</p></section>"
            ),
        }
        final = {
            "title": "人工智能科普进校园",
            "digest": "校园科技活动顺利举行。",
            "body": learning.extract_editorial_text(
                "<section><p>同学们参与人工智能科普体验。</p><p>活动过程清晰有序。</p></section>"
            ),
        }

        first = learning.learn_from_documents(
            history_id="history-1",
            media_id="media-1",
            local=original,
            final=final,
            config={"ai": {"api_key": "test"}},
            provider_factory=provider_factory,
        )
        assert first["changed"] is True
        assert first["already_synced"] is False
        assert len(first["rules"]) == 2
        assert provider.calls == 1

        repeated = learning.learn_from_documents(
            history_id="history-1",
            media_id="media-1",
            local=original,
            final=final,
            config={"ai": {"api_key": "test"}},
            provider_factory=provider_factory,
        )
        assert repeated["already_synced"] is True
        assert provider.calls == 1

        revised_final = {
            **final,
            "body": final["body"] + "\n结尾进一步压缩。",
        }
        second = learning.learn_from_documents(
            history_id="history-1",
            media_id="media-1",
            local=original,
            final=revised_final,
            config={"ai": {"api_key": "test"}},
            provider_factory=provider_factory,
        )
        assert second["already_synced"] is False
        assert provider.calls == 2
        assert all(rule["occurrences"] == 2 for rule in second["rules"])

        active_rules = learning.list_active_rules(minimum_confidence=0.55)
        assert len(active_rules) == 2
        context = draft_service.load_writing_context()
        assert len(context["learned_edit_rules"]) == 2

        deleted_id = active_rules[0]["id"]
        learning.delete_learning_rule(deleted_id)
        assert len(learning.list_active_rules()) == 1

        unchanged_provider = FakeProvider()
        unchanged = learning.learn_from_documents(
            history_id="history-2",
            media_id="media-2",
            local=original,
            final=original,
            config={"ai": {"api_key": "test"}},
            provider_factory=lambda _: unchanged_provider,
        )
        assert unchanged["changed"] is False
        assert unchanged["rules"] == []
        assert unchanged_provider.calls == 0

        print(
            {
                "ok": True,
                "first_rules": len(first["rules"]),
                "deduplicated": repeated["already_synced"],
                "occurrences": second["rules"][0]["occurrences"],
                "active_after_delete": len(learning.list_active_rules()),
                "unchanged_skips_ai": unchanged_provider.calls == 0,
            }
        )


if __name__ == "__main__":
    main()
