from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

from article_image_service import generate_ai_article_images  # noqa: E402
from article_lib import find_content_images, render_article  # noqa: E402


def fake_generate(**kwargs):
    output_path = Path(kwargs["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"fake-image")
    return {"provider": kwargs["provider"], "model": kwargs["model"] or "test-model"}


def sometimes_fail_generate(**kwargs):
    if Path(kwargs["output_path"]).name == "section-02.png":
        raise RuntimeError("simulated provider error")
    return fake_generate(**kwargs)


def main() -> int:
    output_dir = ROOT / "output" / "uploads" / "ai-article-image-test"
    article = {
        "template": "studio-brief",
        "meta": {"title": "AI 科技进校园"},
        "headline": {"title": "AI 科技进校园", "body": ["活动面向学生开展人工智能科普。"]},
        "sections": [
            {
                "cn": "活动启幕",
                "intro": "老师介绍人工智能基础知识与生活应用。",
                "blocks": [{"type": "paragraph", "text": "同学们认真聆听并积极提问。"}],
            },
            {
                "cn": "互动体验",
                "intro": "学生分组参与科技体验活动。",
                "blocks": [{"type": "paragraph", "text": "现场设置了有序的实践环节。"}],
            },
            {
                "cn": "活动收获",
                "intro": "活动帮助学生建立对人工智能的初步认识。",
                "blocks": [{"type": "paragraph", "text": "校园科技教育得到进一步丰富。"}],
            },
        ],
    }
    try:
        generated, errors = generate_ai_article_images(
            article,
            config={
                "image": {
                    "provider": "doubao",
                    "api_key": "test-key",
                    "model": "test-model",
                }
            },
            style={"cover_style": "清爽真实的校园科技纪实风格"},
            output_dir=output_dir,
            max_images=3,
            generate_func=fake_generate,
        )
        assert len(generated) == 3
        assert errors == []
        assert all(section.get("image", {}).get("source") == "ai" for section in article["sections"])
        assert all(Path(section["image"]["local_path"]).exists() for section in article["sections"])
        assert all("不要出现文字" in section["image"]["prompt"] for section in article["sections"])
        assert len(find_content_images(article)) == 3
        html = render_article(article)
        assert all(section["image"]["local_path"] in html for section in article["sections"])

        partial_article = {
            **article,
            "sections": [
                {**section, "image": None}
                for section in article["sections"]
            ],
        }
        partial, partial_errors = generate_ai_article_images(
            partial_article,
            config={
                "image": {
                    "provider": "doubao",
                    "api_key": "test-key",
                    "model": "test-model",
                }
            },
            style={},
            output_dir=output_dir / "partial",
            max_images=3,
            generate_func=sometimes_fail_generate,
        )
        assert len(partial) == 2
        assert len(partial_errors) == 1
        print("AI article image planning and insertion: OK")
        return 0
    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
