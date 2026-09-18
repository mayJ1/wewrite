#!/usr/bin/env python3
"""
WeChat MP Writer — 全自动流水线
================================
渲染 → 校验 → 配图上传 → 封面图上传 → 创建草稿 → (可选)发布

发布功能内置（无需外部 wechat 脚本），凭证从 config.yaml 读取。
图片生成仍可通过 --nanobanana-script 接入外部脚本。

用法:
    # 本地 dry-run（只渲染+校验）
    python3 scripts/run_pipeline.py article.json --output-dir build --dry-run

    # 创建草稿
    python3 scripts/run_pipeline.py article.json --output-dir build --create-draft

    # 创建草稿并发布
    python3 scripts/run_pipeline.py article.json --output-dir build --create-draft --publish

    # 接入外部图片生成
    python3 scripts/run_pipeline.py article.json --output-dir build \
        --nanobanana-script /path/to/generate_image.py --create-draft
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# ——— 把 scripts/ 加入路径，便于导入同目录模块 ———
sys.path.insert(0, str(Path(__file__).resolve().parent))

from article_lib import (
    ArticleError,
    dump_json,
    ensure_meta_defaults,
    find_content_images,
    load_json,
    render_article,
    validate_article,
)
from plan_images import attach_missing_image_plans
from wechat_api import get_access_token, upload_image, upload_thumb
from publisher import create_draft as wechat_create_draft


# ============================================================
# 配置加载
# ============================================================

CONFIG_SEARCH_PATHS = [
    Path(__file__).resolve().parent.parent / "config.yaml",   # skill 根目录
    Path.cwd() / "config.yaml",
    Path.home() / ".config" / "wechat-mp-writer" / "config.yaml",
]


def load_config() -> dict[str, Any]:
    """从第一个找到的 config.yaml 加载配置。"""
    for p in CONFIG_SEARCH_PATHS:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


# ============================================================
# 外部图片生成（可选）
# ============================================================


def _generate_image(nanobanana_script: str, prompt: str, filename: str) -> str:
    """调用外部图片生成脚本。"""
    return subprocess.run(
        ["python3", nanobanana_script, "--prompt", prompt, "--filename", filename, "--resolution", "1K"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


# ============================================================
# 主流程
# ============================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WeChat MP Writer — 渲染·校验·发布 全自动流水线"
    )
    parser.add_argument("input", help="Path to article JSON")
    parser.add_argument("--output-dir", default="build", help="Directory for rendered output")
    parser.add_argument("--resolved-article", help="Write resolved article JSON to this path")
    parser.add_argument("--skip-plan-images", action="store_true")
    parser.add_argument("--max-content-images", type=int, default=3)
    parser.add_argument("--nanobanana-script", help="Path to external generate_image.py")
    parser.add_argument("--create-draft", action="store_true", help="Create a WeChat draft")
    parser.add_argument("--publish", action="store_true", help="Publish immediately after draft (requires --create-draft)")
    parser.add_argument("--dry-run", action="store_true", help="Only render and validate locally")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        article = load_json(args.input)

        if args.publish and not args.create_draft:
            raise ArticleError("--publish requires --create-draft")

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # ——— 1. 配图规划 ———
        if not args.skip_plan_images:
            article = attach_missing_image_plans(
                article,
                output_dir=output_dir / "images",
                max_content_images=args.max_content_images,
            )

        meta = ensure_meta_defaults(article)
        cover = dict(meta.get("cover_image") or {})

        # ——— 2. 图片生成（如果配了外部脚本） ———
        if args.nanobanana_script and not args.dry_run:
            if cover.get("prompt") and cover.get("local_path") and not Path(cover["local_path"]).exists():
                _generate_image(args.nanobanana_script, cover["prompt"], cover["local_path"])

            for image in find_content_images(article):
                if image.get("prompt") and image.get("local_path") and not Path(image["local_path"]).exists():
                    _generate_image(args.nanobanana_script, image["prompt"], image["local_path"])

        # ——— 3. 上传图片到微信（如果有凭证） ———
        cfg = load_config()
        wechat_cfg = cfg.get("wechat", {})
        appid = wechat_cfg.get("appid", "")
        secret = wechat_cfg.get("secret", "")

        if appid and secret and not args.dry_run:
            token = get_access_token(appid, secret)
            print("✓ WeChat access token obtained", file=sys.stderr)

            # 上传封面图
            if cover.get("local_path") and not meta.get("thumb_media_id"):
                cover_path = cover["local_path"]
                if Path(cover_path).exists():
                    print(f"Uploading cover: {cover_path}", file=sys.stderr)
                    media_id = upload_thumb(token, cover_path)
                    meta["thumb_media_id"] = media_id
                    print(f"  -> media_id: {media_id}", file=sys.stderr)

            # 上传正文配图
            for image in find_content_images(article):
                local = image.get("local_path", "")
                if local and not image.get("url") and Path(local).exists():
                    print(f"Uploading image: {local}", file=sys.stderr)
                    url = upload_image(token, local)
                    image["url"] = url
                    print(f"  -> {url}", file=sys.stderr)

        # ——— 4. 渲染 HTML ———
        html_text = render_article(article)

        # ——— 5. 校验 ———
        validation = validate_article(article, html_text=html_text)
        if not validation.ok:
            for error in validation.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1

        for warning in validation.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

        # 写入 HTML
        html_path = output_dir / f"{Path(args.input).stem}.html"
        html_path.write_text(html_text, encoding="utf-8")
        print(f"HTML -> {html_path}", file=sys.stderr)

        # 写入 resolved JSON
        resolved_path = (
            Path(args.resolved_article)
            if args.resolved_article
            else output_dir / f"{Path(args.input).stem}.resolved.json"
        )
        dump_json(resolved_path, article)
        print(f"JSON -> {resolved_path}", file=sys.stderr)

        # ——— 6. 创建草稿 ———
        draft_media_id = None
        publish_id = None

        if args.create_draft:
            if args.dry_run:
                print("WARNING: --create-draft ignored during dry-run", file=sys.stderr)
            elif not appid or not secret:
                print(
                    "ERROR: config.yaml 中缺少 wechat.appid / wechat.secret，无法创建草稿",
                    file=sys.stderr,
                )
                return 1
            elif not meta.get("thumb_media_id"):
                print(
                    "ERROR: 缺少封面图 media_id（meta.thumb_media_id），请先上传封面图",
                    file=sys.stderr,
                )
                return 1
            else:
                token = get_access_token(appid, secret)
                result = wechat_create_draft(
                    access_token=token,
                    title=str(meta["title"]),
                    html=html_text,
                    digest=str(meta.get("digest", "")),
                    thumb_media_id=str(meta.get("thumb_media_id", "")),
                    author=str(meta.get("author", "")),
                )
                draft_media_id = result.media_id
                print(f"OK: Draft created. media_id: {draft_media_id}", file=sys.stderr)

                if args.publish:
                    # 发布说明：微信 publish 接口需要额外的发布步骤
                    # 当前版本创建草稿后，提示用户手动发布或通过微信后台操作
                    print(
                        "NOTE: 草稿已创建。请到公众号后台草稿箱手动发布，"
                        "或使用 preview 命令预览。",
                        file=sys.stderr,
                    )

        # ——— 7. 输出摘要 ———
        summary = {
            "html": str(html_path),
            "resolved_article": str(resolved_path),
            "draft_media_id": draft_media_id,
            "publish_id": publish_id,
            "cover_media_id": meta.get("thumb_media_id"),
            "template": article.get("template"),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    except (ArticleError, OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
