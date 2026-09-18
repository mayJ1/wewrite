#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

import server  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="wewrite-history-images-") as temp:
        uploads = Path(temp).resolve()
        local_image = uploads / "history-photo.jpg"
        local_image.write_bytes(b"test")
        server.UPLOADS_DIR = uploads

        article = {
            "meta": {},
            "headline": {},
            "sections": [
                {
                    "cn": "活动现场",
                    "blocks": [
                        {
                            "type": "image",
                            "url": str(local_image),
                            "local_path": str(local_image),
                            "caption": "本地正文图片",
                        },
                        {
                            "type": "image",
                            "url": "https://mmbiz.qpic.cn/example.jpg",
                            "caption": "微信正文图片",
                        },
                    ],
                }
            ],
        }
        restored = server.hydrate_article_image_previews(article)
        images = restored["sections"][0]["blocks"]
        assert images[0]["preview_url"] == "/local-file/history-photo.jpg"
        assert images[1]["preview_url"] == "https://mmbiz.qpic.cn/example.jpg"
        print(
            {
                "ok": True,
                "local_preview": images[0]["preview_url"],
                "remote_preview": images[1]["preview_url"],
            }
        )


if __name__ == "__main__":
    main()
