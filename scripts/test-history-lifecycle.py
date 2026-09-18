#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

import server  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="wewrite-history-lifecycle-") as temp:
        root = Path(temp).resolve()
        output = root / "output"
        uploads = output / "uploads"
        current_image = uploads / "generated-content" / "session-1" / "section-01.jpg"
        current_image.parent.mkdir(parents=True)
        current_image.write_bytes(b"image")

        server.OUTPUT_DIR = output
        server.UPLOADS_DIR = uploads
        server.DRAFT_HISTORY_PATH = output / "draft-history.json"

        old_path = (
            "D:\\old-install\\WeWrite\\data\\output\\uploads\\"
            "generated-content\\session-1\\section-01.jpg"
        )
        article = {
            "template": "studio-brief",
            "meta": {
                "title": "历史草稿图片测试",
                "digest": "验证迁移后的正文图片和封面能够重新上传。",
                "author": "编辑部",
                "date": "2026-06-30",
                "cover_image": {
                    "filename": "section-01.jpg",
                    "local_path": old_path,
                    "url": old_path,
                    "preview_url": "/local-file/generated-content/session-1/section-01.jpg",
                    "source": "ai",
                },
            },
            "headline": {
                "title": "历史草稿图片测试",
                "body": ["这是一段测试导语。"],
            },
            "sections": [
                {
                    "cn": "活动现场",
                    "blocks": [
                        {
                            "type": "image",
                            "url": old_path,
                            "local_path": old_path,
                            "preview_url": "/local-file/generated-content/session-1/section-01.jpg",
                            "caption": "历史正文图片",
                        }
                    ],
                }
            ],
            "conclusion": "测试完成。",
            "cta": "编辑部",
        }

        uploaded_paths: list[str] = []
        server.get_access_token = lambda *_: "token"
        server.upload_image = lambda _token, path: (
            uploaded_paths.append(path) or "https://mmbiz.qpic.cn/body-image.jpg"
        )
        server.upload_thumb = lambda _token, path: (
            uploaded_paths.append(path) or "thumb-media-id"
        )
        server.wechat_create_draft = lambda **kwargs: SimpleNamespace(media_id="draft-media-id")

        result = server.create_wechat_draft(
            article,
            {"wechat": {"appid": "appid", "secret": "secret"}},
        )
        assert result["ok"] is True
        assert result["uploaded_images"] == 1
        assert result["cover_media_id"] == "thumb-media-id"
        assert all(Path(path).resolve() == current_image.resolve() for path in uploaded_paths)
        assert "https://mmbiz.qpic.cn/body-image.jpg" in result["html"]
        assert "old-install" not in result["html"]
        assert "/local-file/" not in result["html"]

        record_id = "history-delete-test"
        json_file = output / "delete-test-local-draft.json"
        html_file = output / "delete-test-local-draft.html"
        resolved_file = output / "delete-test-local-draft.resolved.json"
        for path in (json_file, html_file, resolved_file):
            path.write_text("test", encoding="utf-8")
        server.save_draft_history(
            [
                {
                    "id": record_id,
                    "title": "待删除草稿",
                    "json_file": json_file.name,
                    "html_file": html_file.name,
                }
            ]
        )
        deleted = server.delete_draft_history(record_id)
        assert deleted["ok"] is True
        assert server.load_draft_history() == []
        assert not json_file.exists()
        assert not html_file.exists()
        assert not resolved_file.exists()

        print(
            json.dumps(
                {
                    "ok": True,
                    "uploaded_images": result["uploaded_images"],
                    "cover_media_id": result["cover_media_id"],
                    "rebased_path": str(current_image),
                    "deleted_files": len(deleted["deleted_files"]),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
