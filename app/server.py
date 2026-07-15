#!/usr/bin/env python3
from __future__ import annotations

import warnings

warnings.filterwarnings("ignore", message="'cgi' is deprecated.*", category=DeprecationWarning)

import cgi
import re
import json
import mimetypes
import os
import socket
import sys
import threading
import traceback
import uuid
import webbrowser
from ipaddress import ip_address
from datetime import date, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import Request, urlopen

import yaml

from runtime_paths import DATA_ROOT, RESOURCE_ROOT, initialize_user_data

initialize_user_data()

APP_DIR = RESOURCE_ROOT / "app"
SKILL_DIR = DATA_ROOT
STATIC_DIR = APP_DIR / "static"
OUTPUT_DIR = SKILL_DIR / "output"
DRAFT_HISTORY_PATH = OUTPUT_DIR / "draft-history.json"
SCRIPTS_DIR = RESOURCE_ROOT / "scripts"
TEMPLATES_DIR = RESOURCE_ROOT / "templates"
CONFIG_PATH = SKILL_DIR / "config.yaml"
CONFIG_EXAMPLE_PATH = SKILL_DIR / "config.example.yaml"
STYLE_PATH = SKILL_DIR / "style.yaml"
UPLOADS_DIR = OUTPUT_DIR / "uploads"
EXEMPLAR_IMPORTS_DIR = OUTPUT_DIR / "exemplar-imports"
LOCAL_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
PUBLIC_IP_SERVICES = (
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://checkip.amazonaws.com",
)

sys.path.insert(0, str(SCRIPTS_DIR))

from article_lib import (  # noqa: E402
    ArticleError,
    available_templates,
    dump_json,
    ensure_meta_defaults,
    find_content_images,
    is_wechat_image_url,
    load_json,
    render_article,
    validate_article,
)
from ai_provider import AIProviderError  # noqa: E402
from article_image_service import generate_ai_article_images  # noqa: E402
from draft_service import DraftServiceError, generate_article_draft, public_exemplar_library  # noqa: E402
from edit_learning_service import (  # noqa: E402
    delete_learning_rule,
    public_learning_state,
    sync_wechat_draft_and_learn,
)
from image_service import ImageServiceError, generate_cover_image  # noqa: E402
from rewrite_service import RewriteServiceError, rewrite_article_text_fields, rewrite_status  # noqa: E402
from extract_exemplar import extract_exemplar as analyze_exemplar, save_exemplar  # noqa: E402
from fetch_article import fetch_article  # noqa: E402
from import_materials import extract_document, scan_directory  # noqa: E402
from publisher import create_draft as wechat_create_draft  # noqa: E402
from wechat_api import get_access_token, upload_image, upload_thumb  # noqa: E402


TEMPLATE_META = {
    "campus-party": {
        "name": "校园党政活动报道",
        "description": "红金暖色风格，适合升旗仪式、主题党日、思政课、少先队活动。",
        "scene": "校园党政",
    },
    "studio-brief": {
        "name": "校园简报",
        "description": "克制、清爽、偏编辑部风格，适合日常活动报道。",
        "scene": "校园报道",
    },
    "neo-brutalism": {
        "name": "醒目活动风",
        "description": "高对比、强视觉，适合需要突出主题的活动或专题。",
        "scene": "专题活动",
    },
    "daily-intelligence": {
        "name": "日报资讯",
        "description": "信息流样式，适合多条资讯集合。",
        "scene": "资讯汇总",
    },
    "weekly-financial": {
        "name": "周报深读",
        "description": "报刊感模板，适合周报、复盘和多板块长文。",
        "scene": "周报复盘",
    },
    "deep-analysis": {
        "name": "深度分析",
        "description": "适合观点分析、专题解读和长文结构。",
        "scene": "深度文章",
    },
    "breaking-watch": {
        "name": "快讯观察",
        "description": "适合即时信息、事件追踪和简短说明。",
        "scene": "快讯",
    },
    "product-release": {
        "name": "产品发布",
        "description": "适合产品、项目或成果发布类文章。",
        "scene": "发布",
    },
    "industry-radar": {
        "name": "行业雷达",
        "description": "适合行业观察、趋势简报和资料整理。",
        "scene": "行业观察",
    },
}


def default_article(template: str = "campus-party") -> dict:
    today = date.today().isoformat()
    return {
        "template": template,
        "meta": {
            "title": "校园活动报道标题",
            "digest": "填写一段不超过 128 字的摘要。",
            "author": "示例编辑",
            "date": today,
        },
        "headline": {
            "title": "国旗下的思政课",
            "body": [
                "这里填写文章导语。建议说明活动背景、主题和整体情况，不虚构具体学生故事、采访原话或数据。"
            ],
        },
        "sections": [
            {
                "en": "THEME",
                "cn": "活动主题",
                "intro": "这里填写本段引导语，概括这一部分要呈现的内容。",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "这里填写正文段落。可以描述活动安排、现场氛围和教育意义，保持真实、克制、温暖。",
                    }
                ],
            },
            {
                "en": "REVIEW",
                "cn": "活动回顾",
                "intro": "这里填写第二个板块的引导语。",
                "blocks": [
                    {
                        "type": "takeaways",
                        "title": "活动要点",
                        "items": ["要点一", "要点二", "要点三"],
                    }
                ],
            },
        ],
        "conclusion": "这里填写收束语。",
        "cta": "本稿为本地预览内容，请确认后再创建微信草稿。",
    }


def json_response(handler: SimpleHTTPRequestHandler, payload: object, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler: SimpleHTTPRequestHandler, text: str, status: int = 200, content_type: str = "text/plain") -> None:
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", f"{content_type}; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def is_within_path(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def local_image_preview_url(raw_url: str) -> str | None:
    value = str(raw_url or "").strip()
    if not value or re.match(r"^(https?:|data:|/local-file/)", value, flags=re.I):
        return None
    path = Path(value)
    if not path.is_absolute():
        path = (SKILL_DIR / value).resolve()
    else:
        path = path.resolve()
    if path.suffix.lower() not in LOCAL_IMAGE_EXTENSIONS or not path.exists() or not path.is_file():
        return None
    if not is_within_path(path, UPLOADS_DIR):
        return None
    relative = path.relative_to(UPLOADS_DIR.resolve()).as_posix()
    return f"/local-file/{quote(relative, safe='/')}"


def rewrite_local_image_sources(html_text: str) -> str:
    if not html_text:
        return html_text

    def replace_src(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        preview_url = local_image_preview_url(src)
        if not preview_url:
            return match.group(0)
        return f"{prefix}{preview_url}{suffix}"

    return re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")', replace_src, html_text, flags=re.I)


def hydrate_article_image_previews(article: dict) -> dict:
    for image in find_content_images(article):
        if not isinstance(image, dict):
            continue
        if image.get("preview_url"):
            continue
        raw_url = str(image.get("local_path") or image.get("url") or "").strip()
        preview_url = local_image_preview_url(raw_url)
        if not preview_url and raw_url.startswith(("http://", "https://", "/local-file/")):
            preview_url = raw_url
        if preview_url:
            image["preview_url"] = preview_url
    cover = article.get("meta", {}).get("cover_image") if isinstance(article.get("meta"), dict) else None
    if isinstance(cover, dict) and not cover.get("preview_url"):
        raw_url = str(cover.get("local_path") or cover.get("url") or "").strip()
        preview_url = local_image_preview_url(raw_url)
        if not preview_url and raw_url.startswith(("http://", "https://", "/local-file/")):
            preview_url = raw_url
        if preview_url:
            cover["preview_url"] = preview_url
    return article


def user_friendly_issues(errors: list[str], warnings: list[str], *, image_mode: str = "") -> dict[str, list[str]]:
    friendly_errors: list[str] = []
    for error in errors:
        text = str(error)
        if "meta.title" in text:
            friendly_errors.append("文章标题缺失或过长，请稍后在编辑页调整标题。")
        elif "meta.digest" in text:
            friendly_errors.append("文章摘要缺失或过长，请稍后在编辑页调整摘要。")
        elif "rendered HTML still contains unresolved placeholders" in text:
            friendly_errors.append("排版模板里还有未替换的占位内容，请重新生成或换一个模板。")
        else:
            friendly_errors.append("文章结构还有一处需要检查，请稍后在编辑页查看。")

    friendly_warnings: list[str] = []
    has_missing_cover = any("thumb_media_id" in str(item) for item in warnings)
    if has_missing_cover:
        friendly_warnings.append("还没有设置公众号封面图。发布前需要选择或上传一张封面图。")
    for warning in warnings:
        text = str(warning)
        if "does not look like WeChat CDN" in text or "thumb_media_id" in text:
            continue
        if "has no blocks" in text:
            friendly_warnings.append("有一个文章小节内容偏少，建议预览时检查是否需要补充。")
        else:
            friendly_warnings.append("有一处内容建议发布前再检查。")

    return {
        "errors": list(dict.fromkeys(friendly_errors)),
        "warnings": list(dict.fromkeys(friendly_warnings)),
    }


def resolve_local_upload_image(raw_value: str) -> Path | None:
    value = str(raw_value or "").strip()
    if not value or re.match(r"^https?:", value, flags=re.I):
        return None
    if value.startswith("/local-file/"):
        path = (UPLOADS_DIR / unquote(value.removeprefix("/local-file/")).lstrip("/")).resolve()
    else:
        candidate = Path(value)
        path = candidate.resolve() if candidate.is_absolute() else (SKILL_DIR / candidate).resolve()
    if not (path.exists() and path.is_file() and is_within_path(path, UPLOADS_DIR)):
        normalized = value.replace("\\", "/")
        marker = "/output/uploads/"
        marker_index = normalized.lower().find(marker)
        if marker_index >= 0:
            relative = normalized[marker_index + len(marker) :].lstrip("/")
            path = (UPLOADS_DIR / relative).resolve()
    if (
        path.exists()
        and path.is_file()
        and path.suffix.lower() in LOCAL_IMAGE_EXTENSIONS
        and is_within_path(path, UPLOADS_DIR)
    ):
        return path
    return None


def resolve_article_image_upload(image: dict) -> Path | None:
    for value in (
        image.get("local_path"),
        image.get("url"),
        image.get("preview_url"),
    ):
        path = resolve_local_upload_image(str(value or ""))
        if path:
            return path
    return None


def save_article_outputs(article: dict, html_text: str, *, suffix: str = "") -> dict[str, str]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = article.get("meta") if isinstance(article.get("meta"), dict) else {}
    title = str(meta.get("title") or "article")
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S-") + uuid.uuid4().hex[:6]
    stem = f"{stamp}-{title}{suffix}"
    json_path = safe_output_path(stem, ".json")
    html_path = safe_output_path(stem, ".html")
    resolved_path = safe_output_path(stem, ".resolved.json")
    dump_json(json_path, article)
    html_path.write_text(html_text, encoding="utf-8")
    dump_json(resolved_path, article)
    return {
        "json_path": str(json_path),
        "html_path": str(html_path),
        "resolved_path": str(resolved_path),
        "preview_url": f"/preview/{html_path.name}",
    }


def load_draft_history() -> list[dict]:
    if not DRAFT_HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(DRAFT_HISTORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def save_draft_history(records: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DRAFT_HISTORY_PATH.write_text(
        json.dumps(records[:100], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_draft_history(article: dict, html_text: str, *, template: str = "") -> dict:
    paths = save_article_outputs(article, html_text, suffix="-local-draft")
    meta = article.get("meta") if isinstance(article.get("meta"), dict) else {}
    record = {
        "id": uuid.uuid4().hex,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "title": str(meta.get("title") or "未命名文章"),
        "digest": str(meta.get("digest") or ""),
        "template": str(article.get("template") or template or "studio-brief"),
        "status": "local",
        "media_id": "",
        "json_file": Path(paths["json_path"]).name,
        "html_file": Path(paths["html_path"]).name,
        "preview_url": paths["preview_url"],
    }
    records = [record, *[item for item in load_draft_history() if item.get("id") != record["id"]]]
    save_draft_history(records)
    return record


def update_draft_history(record_id: str, **updates: object) -> dict | None:
    records = load_draft_history()
    updated = None
    for record in records:
        if str(record.get("id") or "") != record_id:
            continue
        record.update(updates)
        updated = record
        break
    if updated:
        save_draft_history(records)
    return updated


def delete_draft_history(record_id: str) -> dict:
    value = str(record_id or "").strip()
    records = load_draft_history()
    record = next((item for item in records if str(item.get("id") or "") == value), None)
    if not record:
        raise ValueError("没有找到要删除的草稿。")
    save_draft_history([item for item in records if str(item.get("id") or "") != value])
    deleted_files: list[str] = []
    json_name = Path(str(record.get("json_file") or "")).name
    html_name = Path(str(record.get("html_file") or "")).name
    names = [json_name, html_name]
    if json_name.lower().endswith(".json"):
        names.append(f"{json_name[:-5]}.resolved.json")
    for name in names:
        if not name:
            continue
        path = (OUTPUT_DIR / name).resolve()
        if not is_within_path(path, OUTPUT_DIR) or not path.exists() or not path.is_file():
            continue
        path.unlink()
        deleted_files.append(name)
    return {
        "ok": True,
        "record_id": value,
        "title": str(record.get("title") or "未命名文章"),
        "deleted_files": deleted_files,
    }


def load_draft_history_detail(record_id: str) -> dict:
    record = next(
        (item for item in load_draft_history() if str(item.get("id") or "") == record_id),
        None,
    )
    if not record:
        raise ValueError("没有找到这篇本地草稿。")
    json_file = Path(str(record.get("json_file") or "")).name
    html_file = Path(str(record.get("html_file") or "")).name
    json_path = (OUTPUT_DIR / json_file).resolve()
    html_path = (OUTPUT_DIR / html_file).resolve()
    if not is_within_path(json_path, OUTPUT_DIR) or not json_path.exists():
        raise ValueError("这篇草稿的文章文件已不存在。")
    article = load_json(json_path)
    hydrate_article_image_previews(article)
    html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else render_article(article)
    return {
        "record": record,
        "article": article,
        "html": rewrite_local_image_sources(html_text),
        "ok": True,
        "errors": [],
        "warnings": [],
        "user_issues": {"errors": [], "warnings": []},
    }


def cover_image_payload(path: Path, *, source: str, prompt: str = "") -> dict[str, str]:
    resolved = path.resolve()
    preview_url = local_image_preview_url(str(resolved))
    if not preview_url:
        raise ValueError("封面图没有保存在允许的本地目录中。")
    return {
        "filename": resolved.name,
        "local_path": str(resolved),
        "url": str(resolved),
        "preview_url": preview_url,
        "source": source,
        "prompt": prompt,
    }


def build_cover_prompt(article: dict, style: dict, custom_prompt: str = "") -> str:
    meta = article.get("meta") if isinstance(article.get("meta"), dict) else {}
    headline = article.get("headline") if isinstance(article.get("headline"), dict) else {}
    title = str(meta.get("title") or headline.get("title") or "校园活动").strip()
    digest = str(meta.get("digest") or "").strip()
    cover_style = str(style.get("cover_style") or "清爽、温暖、真实的校园纪实摄影风格").strip()
    extra = str(custom_prompt or "").strip()
    parts = [
        f"为微信公众号文章《{title}》生成一张横版封面图。",
        f"主题摘要：{digest[:180]}" if digest else "",
        f"视觉风格：{cover_style}。",
        "画面比例 16:9，主体清晰，适合微信公众号封面裁切，构图简洁，有真实校园氛围。",
        "不要出现文字、标题、水印、品牌标志，不要生成可辨认的学生正脸特写。",
        f"补充要求：{extra}" if extra else "",
    ]
    return " ".join(part for part in parts if part)


def create_wechat_draft(article_input: dict, config: dict) -> dict:
    article = json.loads(json.dumps(article_input, ensure_ascii=False))
    meta = ensure_meta_defaults(article)
    validation_html = render_article(article)
    validation = validate_article(article, html_text=validation_html)
    if validation.errors:
        return {
            "ok": False,
            "errors": validation.errors,
            "user_issues": user_friendly_issues(validation.errors, validation.warnings),
        }

    wechat = config.get("wechat") if isinstance(config.get("wechat"), dict) else {}
    appid = str(wechat.get("appid") or "").strip()
    secret = str(wechat.get("secret") or "").strip()
    if not appid or not secret:
        raise ValueError("请先在设置里填写微信公众号 AppID 和 AppSecret。")

    token = get_access_token(appid, secret)
    uploaded_images = 0
    unresolved_images: list[str] = []

    for index, image in enumerate(find_content_images(article), start=1):
        if not isinstance(image, dict):
            continue
        local_path = resolve_article_image_upload(image)
        if local_path:
            image["local_path"] = str(local_path)
            image["url"] = upload_image(token, str(local_path))
            uploaded_images += 1
        elif not is_wechat_image_url(str(image.get("url") or "")):
            unresolved_images.append(str(image.get("caption") or image.get("filename") or f"正文图片 {index}"))

    if unresolved_images:
        labels = "、".join(unresolved_images[:5])
        raise ValueError(
            f"有 {len(unresolved_images)} 张正文图片找不到本地原文件：{labels}。"
            "请重新导入这些图片，或从正文中移除后再推送。"
        )

    cover_path = None
    cover = meta.get("cover_image") if isinstance(meta.get("cover_image"), dict) else {}
    if cover:
        cover_path = resolve_article_image_upload(cover)
    if cover_path is None:
        for image in find_content_images(article):
            cover_path = resolve_article_image_upload(image)
            if cover_path:
                break
    if cover_path and not meta.get("thumb_media_id"):
        meta["thumb_media_id"] = upload_thumb(token, str(cover_path))

    if not meta.get("thumb_media_id"):
        raise ValueError("没有可用封面图。请先上传至少一张活动图片，或之后接入 AI 生成封面。")

    html_text = render_article(article)
    validation = validate_article(article, html_text=html_text)
    if validation.errors:
        return {
            "ok": False,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "user_issues": user_friendly_issues(validation.errors, validation.warnings),
        }

    paths = save_article_outputs(article, html_text, suffix="-wechat-draft")
    result = wechat_create_draft(
        access_token=token,
        title=str(meta.get("title") or ""),
        html=html_text,
        digest=str(meta.get("digest") or ""),
        thumb_media_id=str(meta.get("thumb_media_id") or ""),
        author=str(meta.get("author") or ""),
    )
    return {
        "ok": True,
        "media_id": result.media_id,
        "uploaded_images": uploaded_images,
        "cover_media_id": meta.get("thumb_media_id"),
        "article": article,
        "html": rewrite_local_image_sources(html_text),
        **paths,
    }


def parse_wechat_error(raw_error: str) -> tuple[str | None, str]:
    code_match = re.search(r"errcode=([-\d]+)", raw_error)
    message_match = re.search(r"errmsg=([^,}]+)", raw_error)
    code = code_match.group(1) if code_match else None
    errmsg = message_match.group(1).strip() if message_match else raw_error
    return code, errmsg


def friendly_wechat_error(raw_error: str) -> dict[str, object] | None:
    if "WeChat" not in raw_error and "wechat" not in raw_error and "微信" not in raw_error:
        return None
    code, errmsg = parse_wechat_error(raw_error)
    actions: list[str] = []
    title = "微信草稿创建失败。"

    if code == "40164" or "invalid ip" in raw_error.lower() or "not in whitelist" in raw_error.lower():
        title = "微信拒绝了这台电脑的 IP。"
        actions = [
            "打开右上角“设置”，复制当前出口 IP。",
            "登录微信公众平台，在“开发设置”里找到“IP 白名单”。",
            "把这个 IP 加入白名单并保存，然后回到 WeWrite 重新推送。",
        ]
    elif code in {"40013", "41002"}:
        title = "公众号 AppID 不正确或没有填写。"
        actions = [
            "打开右上角“设置”。",
            "检查 AppID 是否从当前公众号后台复制，注意不要多复制空格。",
            "保存后重新推送到草稿箱。",
        ]
    elif code in {"40125", "41004", "40001"}:
        title = "公众号 AppSecret 不正确或已失效。"
        actions = [
            "登录微信公众平台，重新复制 AppSecret。",
            "打开 WeWrite 右上角“设置”，粘贴新的 AppSecret 并保存。",
            "如果刚重置过 AppSecret，请等待一小会儿再重试。",
        ]
    elif code in {"48001", "48002", "48004"}:
        title = "当前公众号还没有开通这个微信接口权限。"
        actions = [
            "确认当前账号是已认证或具备草稿箱/素材接口权限的公众号。",
            "在微信公众平台检查开发者接口权限。",
            "权限开通后再回到 WeWrite 重新推送。",
        ]
    elif code in {"45009", "45011", "45047"}:
        title = "微信接口调用太频繁了。"
        actions = [
            "先等待几分钟再重试。",
            "如果连续测试很多次，建议稍后再继续。",
        ]
    elif "upload_image" in raw_error or "upload_thumb" in raw_error or "media/upload" in raw_error:
        title = "图片上传到微信失败。"
        actions = [
            "检查素材图片是否能正常打开。",
            "尽量使用 jpg、jpeg 或 png 图片。",
            "如果图片特别大，先压缩后重新上传素材。",
        ]
    elif "create_draft" in raw_error or "draft/add" in raw_error:
        title = "微信草稿箱没有创建成功。"
        actions = [
            "先确认 AppID、AppSecret 和 IP 白名单都配置正确。",
            "检查文章标题、摘要和封面图是否正常。",
            "稍后重新点击“推送到微信草稿箱”。",
        ]
    else:
        actions = [
            "检查公众号 AppID、AppSecret 和 IP 白名单是否配置正确。",
            "确认网络可以访问微信公众平台接口。",
            "如果重复失败，把下方技术信息发给维护人员排查。",
        ]

    return {
        "error": title,
        "error_code": code,
        "error_detail": errmsg,
        "action_steps": actions,
        "raw_error": raw_error,
    }


def friendly_error_payload(exc: Exception) -> dict[str, object]:
    raw = str(exc)
    wechat_payload = friendly_wechat_error(raw)
    if wechat_payload:
        return {"ok": False, **wechat_payload}
    return {"ok": False, "error": raw}


def read_json_body(handler: SimpleHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object.")
    return data


def safe_upload_parts(filename: str) -> list[str]:
    parts: list[str] = []
    for part in filename.replace("\\", "/").split("/"):
        cleaned = part.strip().strip(".")
        if not cleaned:
            continue
        cleaned = "".join(ch for ch in cleaned if ch not in '<>:"|?*')
        if cleaned:
            parts.append(cleaned)
    return parts or ["uploaded-file"]


def choose_material_root(upload_dir: Path) -> Path:
    files = [entry for entry in upload_dir.iterdir() if entry.is_file()]
    dirs = [entry for entry in upload_dir.iterdir() if entry.is_dir()]
    if not files and len(dirs) == 1:
        return dirs[0]
    return upload_dir


def import_uploaded_materials(upload_dir: Path) -> dict:
    material_root = choose_material_root(upload_dir)
    scan_result = scan_directory(material_root)
    documents = [extract_document(doc) for doc in scan_result["documents"]]

    def photo_result(img: dict) -> dict:
        preview_url = local_image_preview_url(str(img["path"]))
        result = {
            "filename": img["filename"],
            "url": img["path"],
            "preview_url": preview_url or "",
            "error": None,
            "local_only": True,
        }
        if img.get("category"):
            result["category"] = img["category"]
        return result

    photos = [photo_result(img) for img in scan_result["images"]]
    return {
        "directory": str(material_root.resolve()),
        "documents": documents,
        "photos": photos,
        "categories": scan_result.get("categories"),
        "stats": {
            "total_docs": len(scan_result["documents"]),
            "total_photos": len(scan_result["images"]),
            "total_chars": sum(doc.get("char_count", 0) for doc in documents),
            "docs_with_errors": sum(1 for doc in documents if doc.get("error")),
            "photos_uploaded": 0,
            "photos_failed": 0,
            "photos_local_only": True,
        },
    }


def load_config() -> dict:
    source = CONFIG_PATH if CONFIG_PATH.exists() else CONFIG_EXAMPLE_PATH
    if not source.exists():
        return {}
    with source.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        return {}
    return data


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def load_style() -> dict:
    if not STYLE_PATH.exists():
        return {}
    with STYLE_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def save_style(style: dict) -> None:
    STYLE_PATH.write_text(
        yaml.safe_dump(style, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def split_list_value(value: object) -> list[str]:
    if isinstance(value, list):
        raw_items = value
    else:
        text = str(value or "")
        raw_items = text.replace("，", ",").replace("、", ",").replace("\n", ",").split(",")
    return [str(item).strip() for item in raw_items if str(item).strip()]


def public_style(style: dict | None = None) -> dict:
    data = style if style is not None else load_style()
    blacklist = data.get("blacklist") if isinstance(data.get("blacklist"), dict) else {}
    return {
        "exists": STYLE_PATH.exists(),
        "name": str(data.get("name") or ""),
        "full_name": str(data.get("full_name") or ""),
        "industry": str(data.get("industry") or ""),
        "topics": data.get("topics") if isinstance(data.get("topics"), list) else [],
        "tone": str(data.get("tone") or ""),
        "writing_persona": str(data.get("writing_persona") or "warm-editor"),
        "target_audience": str(data.get("target_audience") or ""),
        "voice": str(data.get("voice") or ""),
        "author": str(data.get("author") or ""),
        "template": str(data.get("template") or "studio-brief"),
        "cover_style": str(data.get("cover_style") or ""),
        "reference_accounts": data.get("reference_accounts") if isinstance(data.get("reference_accounts"), list) else [],
        "blacklist": {
            "words": blacklist.get("words") if isinstance(blacklist.get("words"), list) else [],
            "topics": blacklist.get("topics") if isinstance(blacklist.get("topics"), list) else [],
        },
    }


def has_value(config: dict, *keys: str) -> bool:
    value: object = config
    for key in keys:
        if not isinstance(value, dict):
            return False
        value = value.get(key)
    return bool(str(value or "").strip())


def config_status(config: dict | None = None) -> dict:
    cfg = config if config is not None else load_config()
    ai = cfg.get("ai") if isinstance(cfg.get("ai"), dict) else {}
    image = cfg.get("image") if isinstance(cfg.get("image"), dict) else {}
    rewrite = rewrite_status(cfg, RESOURCE_ROOT)
    return {
        "exists": CONFIG_PATH.exists(),
        "wechat": {
            "appid": has_value(cfg, "wechat", "appid"),
            "secret": has_value(cfg, "wechat", "secret"),
        },
        "ai": {
            "api_key": has_value(cfg, "ai", "api_key"),
            "provider": str(ai.get("provider") or "").strip(),
            "base_url": str(ai.get("base_url") or "").strip(),
            "model": str(ai.get("model") or "").strip(),
        },
        "image": {
            "api_key": has_value(cfg, "image", "api_key"),
            "provider": str(image.get("provider") or "").strip(),
            "model": str(image.get("model") or "").strip(),
        },
        "rewrite": rewrite,
    }


def fetch_public_ip() -> str:
    errors: list[str] = []
    for service_url in PUBLIC_IP_SERVICES:
        try:
            request = Request(service_url, headers={"User-Agent": "WeChatMPWriterApp/0.1"})
            with urlopen(request, timeout=6) as response:
                raw = response.read(128).decode("utf-8", errors="replace").strip()
            parsed = ip_address(raw)
            return str(parsed)
        except Exception as exc:
            errors.append(f"{service_url}: {exc}")
    raise RuntimeError("无法获取当前出口 IP，请稍后重试或手动搜索“我的 IP”。")


def safe_output_path(name: str, suffix: str) -> Path:
    cleaned = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("-_")
    if not cleaned:
        cleaned = f"article-{date.today().isoformat()}"
    return OUTPUT_DIR / f"{cleaned}{suffix}"


def import_exemplar_text(text: str, *, source: str, category: str = "general") -> dict:
    cleaned = str(text or "").strip()
    if len(cleaned) < 80:
        raise ValueError("范文内容太短，无法提取风格。")
    exemplar = analyze_exemplar(cleaned, category=category or "general", source=source or "未命名范文")
    path = save_exemplar(exemplar)
    return {
        "file": path.name,
        "source": exemplar.get("source"),
        "category": exemplar.get("category"),
        "humanness_score": exemplar.get("humanness_score"),
        "char_count": exemplar.get("char_count"),
    }


def exemplar_path(filename: str) -> Path:
    safe_name = Path(str(filename or "")).name
    if not safe_name or safe_name != str(filename or ""):
        raise ValueError("范文文件名不安全。")
    target = (SKILL_DIR / "references" / "exemplars" / safe_name).resolve()
    root = (SKILL_DIR / "references" / "exemplars").resolve()
    if not str(target).startswith(str(root)) or target.suffix.lower() != ".md":
        raise ValueError("范文文件路径不安全。")
    return target


def parse_exemplar_markdown(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                meta_text = "\n".join(lines[1:index])
                body = "\n".join(lines[index + 1 :]).strip()
                meta = yaml.safe_load(meta_text) or {}
                return (meta if isinstance(meta, dict) else {}, body)
    return {}, text.strip()


def load_exemplar_detail(filename: str) -> dict:
    path = exemplar_path(filename)
    if not path.exists():
        raise ValueError("范文不存在。")
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_exemplar_markdown(raw)
    index_entry = next(
        (item for item in public_exemplar_library() if item.get("file") == path.name),
        {},
    )
    return {
        "file": path.name,
        "source": meta.get("source") or index_entry.get("source") or path.stem,
        "category": meta.get("category") or index_entry.get("category") or "general",
        "extracted_at": meta.get("extracted_at") or index_entry.get("extracted_at") or "",
        "humanness_score": meta.get("humanness_score", index_entry.get("humanness_score")),
        "metrics": {
            "sentence_stddev": meta.get("sentence_stddev"),
            "negative_ratio": meta.get("negative_ratio"),
            "paragraph_cv": meta.get("paragraph_cv"),
            "short_paragraphs": meta.get("short_paragraphs"),
            "vocab_temperature": meta.get("vocab_temperature") if isinstance(meta.get("vocab_temperature"), dict) else {},
        },
        "learned": describe_exemplar_learning(meta),
        "content": body,
        "raw": raw,
    }


def describe_exemplar_learning(meta: dict) -> dict:
    category = str(meta.get("category") or "general")
    temp = meta.get("vocab_temperature") if isinstance(meta.get("vocab_temperature"), dict) else {}
    dominant_temp = max(temp, key=temp.get) if temp else "balanced"
    persona_map = {
        "story-emotional": "温暖编辑",
        "list-practical": "实用清单型编辑",
        "tech-opinion": "行业观察者",
        "hot-take": "观点评论型作者",
        "general": "通用编辑",
    }
    tone_map = {
        "cold": "更克制、理性，偏信息说明",
        "warm": "更温暖、亲近，适合校园/情感叙事",
        "hot": "情绪更强，适合强调现场感和感染力",
        "wild": "表达更活跃，句式更有变化",
        "balanced": "语气较均衡",
    }
    paragraph_cv = meta.get("paragraph_cv")
    sentence_stddev = meta.get("sentence_stddev")
    short_paragraphs = meta.get("short_paragraphs")
    features = []
    if isinstance(sentence_stddev, (int, float)):
        features.append("句长变化明显" if sentence_stddev >= 18 else "句长相对稳定")
    if isinstance(paragraph_cv, (int, float)):
        features.append("段落长短错落" if paragraph_cv >= 0.8 else "段落节奏较均匀")
    if isinstance(short_paragraphs, int) and short_paragraphs > 0:
        features.append("会使用短段落制造停顿")
    if not features:
        features.append("保留基础结构和表达节奏")
    return {
        "persona": persona_map.get(category, "通用编辑"),
        "tone": tone_map.get(dominant_temp, "语气较均衡"),
        "style": features,
    }


def delete_exemplar_file(filename: str) -> dict:
    path = exemplar_path(filename)
    if not path.exists():
        raise ValueError("范文不存在。")
    index_path = SKILL_DIR / "references" / "exemplars" / "index.yaml"
    index = []
    if index_path.exists():
        with index_path.open("r", encoding="utf-8") as handle:
            index = yaml.safe_load(handle) or []
    if not isinstance(index, list):
        index = []
    index = [item for item in index if not (isinstance(item, dict) and item.get("file") == path.name)]
    index_path.write_text(yaml.safe_dump(index, allow_unicode=True, sort_keys=False), encoding="utf-8")
    path.unlink()
    return {"file": path.name}


class AppHandler(SimpleHTTPRequestHandler):
    server_version = "WeChatMPWriterApp/0.1"

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path == "/":
                return self.serve_static("index.html")
            if path.startswith("/static/"):
                return self.serve_static(path.removeprefix("/static/"))
            if path == "/api/config":
                return json_response(self, {"config": config_status()})
            if path == "/api/style":
                return json_response(self, {"style": public_style()})
            if path == "/api/public-ip":
                return json_response(self, {"ip": fetch_public_ip()})
            if path == "/api/templates":
                return self.handle_templates()
            if path == "/api/exemplars":
                return json_response(self, {"exemplars": public_exemplar_library()})
            if path == "/api/draft-history":
                return json_response(self, {"history": load_draft_history()})
            if path == "/api/draft-history/detail":
                query = parse_qs(parsed.query)
                record_id = query.get("id", [""])[0]
                return json_response(self, load_draft_history_detail(record_id))
            if path == "/api/edit-learning":
                return json_response(self, public_learning_state())
            if path == "/api/exemplars/detail":
                query = parse_qs(parsed.query)
                filename = query.get("file", [""])[0]
                return json_response(self, {"exemplar": load_exemplar_detail(filename)})
            if path == "/api/sample":
                template = "campus-party"
                return json_response(self, {"article": default_article(template)})
            if path.startswith("/preview/"):
                name = path.removeprefix("/preview/")
                return self.serve_output_html(name)
            if path.startswith("/local-file/"):
                name = path.removeprefix("/local-file/")
                return self.serve_local_file(name)
            return text_response(self, "Not found", HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.handle_error(exc)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path == "/api/render":
                return self.handle_render(save=False)
            if path == "/api/save":
                return self.handle_render(save=True)
            if path == "/api/config":
                return self.handle_save_config()
            if path == "/api/style":
                return self.handle_save_style()
            if path == "/api/exemplars/upload":
                return self.handle_exemplar_upload()
            if path == "/api/exemplars/from-url":
                return self.handle_exemplar_from_url()
            if path == "/api/exemplars/delete":
                return self.handle_exemplar_delete()
            if path == "/api/materials/upload":
                return self.handle_material_upload()
            if path == "/api/images/cover":
                return self.handle_generate_cover()
            if path == "/api/images/cover-upload":
                return self.handle_cover_upload()
            if path == "/api/draft":
                return self.handle_draft()
            if path == "/api/wechat-draft":
                return self.handle_wechat_draft()
            if path == "/api/draft-history/learn":
                return self.handle_learn_wechat_edits()
            if path == "/api/draft-history/delete":
                return self.handle_delete_draft_history()
            if path == "/api/edit-learning/delete":
                return self.handle_delete_learning_rule()
            return text_response(self, "Not found", HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.handle_error(exc)

    def handle_templates(self) -> None:
        templates = []
        for template in sorted(available_templates()):
            path = TEMPLATES_DIR / f"{template}.html"
            meta = TEMPLATE_META.get(template, {})
            templates.append(
                {
                    "id": template,
                    "name": meta.get("name", template),
                    "description": meta.get("description", "自定义微信公众号模板。"),
                    "scene": meta.get("scene", "通用"),
                    "size": path.stat().st_size if path.exists() else 0,
                }
            )
        json_response(self, {"templates": templates})

    def handle_save_config(self) -> None:
        payload = read_json_body(self)
        step = str(payload.get("step") or "").strip()
        value = str(payload.get("value") or "").strip()
        skipped = bool(payload.get("skip"))
        if step not in {"appid", "secret", "ai_api", "image_api"}:
            raise ValueError("Unknown config step.")
        if step in {"appid", "secret", "ai_api"} and not value:
            raise ValueError("This item cannot be empty.")

        config = load_config()
        wechat = config.setdefault("wechat", {})
        ai = config.setdefault("ai", {})
        image = config.setdefault("image", {})
        if not isinstance(wechat, dict) or not isinstance(ai, dict) or not isinstance(image, dict):
            raise ValueError("config.yaml has an unexpected shape.")

        if step == "appid":
            wechat["appid"] = value
        elif step == "secret":
            wechat["secret"] = value
        elif step == "ai_api":
            ai["provider"] = "deepseek"
            ai["base_url"] = "https://api.deepseek.com"
            ai["api_key"] = value
            ai["model"] = "deepseek-v4-flash"
        elif step == "image_api" and not skipped:
            image["api_key"] = value
            provider = str(payload.get("provider") or image.get("provider") or "doubao").strip().lower()
            if provider not in {"doubao", "agnes"}:
                raise ValueError("AI 生图服务目前支持豆包和 Agnes。")
            image["provider"] = provider
            requested_model = str(payload.get("model") or "").strip()
            if requested_model:
                image["model"] = requested_model
            elif provider == "doubao":
                image["model"] = "doubao-seedream-4-0-250828"
            else:
                image["model"] = "agnes-image-2.1-flash"

        save_config(config)
        json_response(self, {"ok": True, "config": config_status(config)})

    def handle_save_style(self) -> None:
        payload = read_json_body(self)
        style = load_style()

        string_fields = [
            "name",
            "full_name",
            "industry",
            "tone",
            "writing_persona",
            "target_audience",
            "voice",
            "author",
            "template",
            "cover_style",
        ]
        for field in string_fields:
            if field in payload:
                style[field] = str(payload.get(field) or "").strip()

        if "topics" in payload:
            style["topics"] = split_list_value(payload.get("topics"))
        if "reference_accounts" in payload:
            style["reference_accounts"] = split_list_value(payload.get("reference_accounts"))

        blacklist = style.get("blacklist") if isinstance(style.get("blacklist"), dict) else {}
        if "blacklist_words" in payload:
            blacklist["words"] = split_list_value(payload.get("blacklist_words"))
        if "blacklist_topics" in payload:
            blacklist["topics"] = split_list_value(payload.get("blacklist_topics"))
        if blacklist:
            style["blacklist"] = blacklist

        if not str(style.get("name") or "").strip():
            raise ValueError("请填写公众号名称。")
        if not str(style.get("industry") or "").strip():
            raise ValueError("请填写行业/机构类型。")
        if not style.get("topics"):
            raise ValueError("请至少填写一个内容方向。")
        if not str(style.get("tone") or "").strip():
            raise ValueError("请填写写作风格。")

        style.setdefault("writing_persona", "warm-editor")
        style.setdefault("template", "studio-brief")
        style.setdefault("author", style.get("name") or "编辑部")

        save_style(style)
        (SKILL_DIR / "corpus").mkdir(exist_ok=True)
        (SKILL_DIR / "lessons").mkdir(exist_ok=True)
        history_path = SKILL_DIR / "history.yaml"
        if not history_path.exists():
            history_path.write_text("[]\n", encoding="utf-8")
        json_response(self, {"ok": True, "style": public_style(style)})

    def handle_exemplar_upload(self) -> None:
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )
        file_item = form["file"] if "file" in form else None
        if file_item is None or not getattr(file_item, "filename", None):
            raise ValueError("请选择一篇 Word 范文。")

        source = str(form.getfirst("source") or Path(file_item.filename).stem).strip()
        category = str(form.getfirst("category") or "general").strip() or "general"
        parts = safe_upload_parts(file_item.filename)
        filename = parts[-1]
        ext = Path(filename).suffix.lower()
        if ext not in {".docx", ".txt", ".md"}:
            raise ValueError("目前支持 .docx Word 文件，也支持 .txt/.md。老式 .doc 请先另存为 .docx。")

        import_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
        import_dir = EXEMPLAR_IMPORTS_DIR / import_id
        import_dir.mkdir(parents=True, exist_ok=True)
        target = (import_dir / filename).resolve()
        if not str(target).startswith(str(import_dir.resolve())):
            raise ValueError("范文文件路径不安全。")
        data = file_item.file.read()
        if not data:
            raise ValueError("上传的范文文件为空。")
        target.write_bytes(data)

        extracted = extract_document({"filename": filename, "ext": ext, "path": str(target)})
        if extracted.get("error"):
            raise ValueError(str(extracted["error"]))
        text = str(extracted.get("text") or "").strip()
        title = source or Path(filename).stem
        markdown = f"# {title}\n\n{text}"
        imported = import_exemplar_text(markdown, source=title, category=category)
        json_response(self, {"ok": True, "imported": imported, "exemplars": public_exemplar_library()})

    def handle_exemplar_from_url(self) -> None:
        payload = read_json_body(self)
        url = str(payload.get("url") or "").strip()
        source = str(payload.get("source") or "").strip()
        category = str(payload.get("category") or "general").strip() or "general"
        if not url:
            raise ValueError("请填写公众号文章链接。")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("公众号文章链接需要以 http:// 或 https:// 开头。")
        try:
            result = fetch_article(url=url)
        except SystemExit as exc:
            raise ValueError("无法抓取公众号文章正文。请确认链接可公开访问，或稍后改用 Word 导入。") from exc
        title = source or result.get("title") or result.get("author") or url
        markdown = result.get("markdown") or ""
        if result.get("title") and not markdown.lstrip().startswith("#"):
            markdown = f"# {result['title']}\n\n{markdown}"
        imported = import_exemplar_text(markdown, source=title, category=category)
        json_response(self, {"ok": True, "imported": imported, "exemplars": public_exemplar_library()})

    def handle_exemplar_delete(self) -> None:
        payload = read_json_body(self)
        filename = str(payload.get("file") or "").strip()
        if not filename:
            raise ValueError("缺少要删除的范文文件名。")
        deleted = delete_exemplar_file(filename)
        json_response(self, {"ok": True, "deleted": deleted, "exemplars": public_exemplar_library()})

    def handle_material_upload(self) -> None:
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )
        file_items = form["files"] if "files" in form else []
        if not isinstance(file_items, list):
            file_items = [file_items]
        file_items = [item for item in file_items if getattr(item, "filename", None)]
        if not file_items:
            raise ValueError("请选择一个素材文件夹。")

        upload_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
        upload_dir = UPLOADS_DIR / upload_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_count = 0
        upload_root = upload_dir.resolve()
        for item in file_items:
            parts = safe_upload_parts(item.filename)
            target = upload_dir.joinpath(*parts).resolve()
            if not str(target).startswith(str(upload_root)):
                raise ValueError("素材文件路径不安全。")
            target.parent.mkdir(parents=True, exist_ok=True)
            data = item.file.read()
            if data:
                target.write_bytes(data)
                saved_count += 1

        if saved_count == 0:
            raise ValueError("没有收到可导入的素材文件。")

        materials = import_uploaded_materials(upload_dir)
        json_response(
            self,
            {
                "ok": True,
                "upload_id": upload_id,
                "saved_count": saved_count,
                "materials": materials,
            },
        )

    def handle_generate_cover(self) -> None:
        payload = read_json_body(self)
        article = payload.get("article")
        if not isinstance(article, dict):
            raise ValueError("请先生成文章，再生成封面图。")

        config = load_config()
        image_config = config.get("image") if isinstance(config.get("image"), dict) else {}
        api_key = str(image_config.get("api_key") or "").strip()
        provider = str(image_config.get("provider") or "agnes").strip().lower()

        custom_prompt = str(payload.get("prompt") or "").strip()
        prompt = build_cover_prompt(article, load_style(), custom_prompt)
        cover_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
        target = (UPLOADS_DIR / "generated-covers" / f"{cover_id}.png").resolve()
        result = generate_cover_image(
            provider=provider,
            api_key=api_key,
            prompt=prompt,
            output_path=target,
            model=str(image_config.get("model") or ""),
            base_url=str(image_config.get("base_url") or ""),
        )
        cover = cover_image_payload(target, source="ai", prompt=prompt)
        cover["custom_prompt"] = custom_prompt
        json_response(
            self,
            {
                "ok": True,
                "cover": cover,
                "provider": result["provider"],
                "model": result["model"],
            },
        )

    def handle_cover_upload(self) -> None:
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )
        file_item = form["file"] if "file" in form else None
        if file_item is None or not getattr(file_item, "filename", None):
            raise ValueError("请选择一张封面图片。")
        filename = safe_upload_parts(file_item.filename)[-1]
        ext = Path(filename).suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError("封面图支持 JPG、PNG 或 WebP 格式。")
        data = file_item.file.read()
        if not data:
            raise ValueError("上传的封面图片为空。")
        if len(data) > 10 * 1024 * 1024:
            raise ValueError("封面图片不能超过 10 MB。")

        cover_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
        target = (UPLOADS_DIR / "custom-covers" / f"{cover_id}{ext}").resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        json_response(self, {"ok": True, "cover": cover_image_payload(target, source="upload")})

    def handle_draft(self) -> None:
        payload = read_json_body(self)
        requirements = payload.get("requirements") if isinstance(payload.get("requirements"), dict) else {}
        image_mode = str(requirements.get("image_mode") or "").strip()
        rewrite_enabled = bool(requirements.get("rewrite_enabled"))
        config = load_config()
        if image_mode in {"ai_generated", "ai_cover"} and not has_value(config, "image", "api_key"):
            raise ValueError("已选择 AI 生成插图，请先在设置中配置 AI 生图 API Key。")
        result = generate_article_draft(
            request=payload,
            config=config,
            render_article=render_article,
            validate_article=validate_article,
        )
        article = result.get("article")
        if image_mode in {"ai_generated", "ai_cover"} and isinstance(article, dict):
            generation_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
            generated, generation_errors = generate_ai_article_images(
                article,
                config=config,
                style=load_style(),
                output_dir=UPLOADS_DIR / "generated-content" / generation_id,
                max_images=3,
            )
            for item in generated:
                preview_url = local_image_preview_url(str(item.get("local_path") or ""))
                if preview_url:
                    item["preview_url"] = preview_url
                    section_index = int(item.get("section_index", -1))
                    sections = article.get("sections") if isinstance(article.get("sections"), list) else []
                    if 0 <= section_index < len(sections) and isinstance(sections[section_index].get("image"), dict):
                        sections[section_index]["image"]["preview_url"] = preview_url
            rendered = render_article(article)
            validation = validate_article(article, html_text=rendered)
            result.update(
                {
                    "ok": validation.ok,
                    "article": article,
                    "html": rendered,
                    "errors": validation.errors,
                    "warnings": validation.warnings,
                    "image_generation": {
                        "mode": "ai_generated",
                        "generated_count": len(generated),
                        "images": generated,
                        "errors": generation_errors,
                    },
                }
            )
        if rewrite_enabled and isinstance(result.get("article"), dict):
            try:
                rewritten_article, rewrite_info = rewrite_article_text_fields(
                    result["article"],
                    config=config,
                    resource_root=RESOURCE_ROOT,
                )
                rendered = render_article(rewritten_article)
                validation = validate_article(rewritten_article, html_text=rendered)
                result.update(
                    {
                        "ok": validation.ok,
                        "article": rewritten_article,
                        "html": rendered,
                        "errors": validation.errors,
                        "warnings": validation.warnings,
                        "rewrite": rewrite_info,
                    }
                )
            except RewriteServiceError as exc:
                warnings = [str(item) for item in result.get("warnings") or []]
                warnings.append(f"自然润色未完成：{exc}")
                result["warnings"] = warnings
                result["rewrite"] = {
                    "enabled": True,
                    "changed_count": 0,
                    "errors": [str(exc)],
                }
        result["html"] = rewrite_local_image_sources(str(result.get("html") or ""))
        result["user_issues"] = user_friendly_issues(
            [str(item) for item in result.get("errors") or []],
            [str(item) for item in result.get("warnings") or []],
            image_mode=image_mode,
        )
        if isinstance(result.get("article"), dict) and result.get("html"):
            history_record = add_draft_history(
                result["article"],
                str(result["html"]),
                template=str(payload.get("template") or ""),
            )
            result["history_id"] = history_record["id"]
        json_response(self, result, 200 if result.get("ok") else 422)

    def handle_wechat_draft(self) -> None:
        payload = read_json_body(self)
        article = payload.get("article")
        history_id = str(payload.get("history_id") or "").strip()
        if not isinstance(article, dict):
            raise ValueError("缺少要推送的文章内容，请先生成文章预览。")
        result = create_wechat_draft(article, load_config())
        if result.get("ok") and history_id:
            update_draft_history(
                history_id,
                status="wechat",
                media_id=str(result.get("media_id") or ""),
                pushed_at=datetime.now().isoformat(timespec="seconds"),
                json_file=Path(str(result.get("json_path") or "")).name,
                html_file=Path(str(result.get("html_path") or "")).name,
                preview_url=str(result.get("preview_url") or ""),
                cover_media_id=str(result.get("cover_media_id") or ""),
            )
        json_response(self, result, 200 if result.get("ok") else 422)

    def handle_learn_wechat_edits(self) -> None:
        payload = read_json_body(self)
        history_id = str(payload.get("history_id") or "").strip()
        if not history_id:
            raise ValueError("缺少要学习的草稿记录。")
        detail = load_draft_history_detail(history_id)
        record = detail["record"]
        result = sync_wechat_draft_and_learn(
            record=record,
            article=detail["article"],
            original_html=detail["html"],
            config=load_config(),
        )
        learned_at = datetime.now().isoformat(timespec="seconds")
        learning_status = "learned" if result.get("changed") else "unchanged"
        update_draft_history(
            history_id,
            learning_status=learning_status,
            learned_at=learned_at,
            learned_rule_count=len(result.get("rules") or []),
        )
        result["learning"] = public_learning_state()
        json_response(self, result)

    def handle_delete_draft_history(self) -> None:
        payload = read_json_body(self)
        json_response(self, delete_draft_history(str(payload.get("history_id") or "")))

    def handle_delete_learning_rule(self) -> None:
        payload = read_json_body(self)
        result = delete_learning_rule(str(payload.get("rule_id") or ""))
        result["learning"] = public_learning_state()
        json_response(self, result)

    def handle_render(self, *, save: bool) -> None:
        payload = read_json_body(self)
        article = payload.get("article")
        if not isinstance(article, dict):
            raise ValueError("Missing article object.")

        html_text = render_article(article)
        validation = validate_article(article, html_text=html_text)
        response: dict[str, object] = {
            "ok": validation.ok,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "user_issues": user_friendly_issues(validation.errors, validation.warnings),
            "html": rewrite_local_image_sources(html_text),
        }

        if save:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            meta = article.get("meta") if isinstance(article.get("meta"), dict) else {}
            title = str(meta.get("title") or "article")
            stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            stem = f"{stamp}-{title}"
            json_path = safe_output_path(stem, ".json")
            html_path = safe_output_path(stem, ".html")
            resolved_path = safe_output_path(stem, ".resolved.json")
            dump_json(json_path, article)
            html_path.write_text(html_text, encoding="utf-8")
            dump_json(resolved_path, article)
            response.update(
                {
                    "json_path": str(json_path),
                    "html_path": str(html_path),
                    "resolved_path": str(resolved_path),
                    "preview_url": f"/preview/{html_path.name}",
                }
            )

        json_response(self, response, 200 if validation.ok else 400)

    def serve_static(self, relative: str) -> None:
        target = (STATIC_DIR / relative).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists() or not target.is_file():
            return text_response(self, "Not found", HTTPStatus.NOT_FOUND)
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_output_html(self, name: str) -> None:
        target = (OUTPUT_DIR / name).resolve()
        if not str(target).startswith(str(OUTPUT_DIR.resolve())) or target.suffix.lower() != ".html" or not target.exists():
            return text_response(self, "Not found", HTTPStatus.NOT_FOUND)
        text_response(self, rewrite_local_image_sources(target.read_text(encoding="utf-8")), content_type="text/html")

    def serve_local_file(self, name: str) -> None:
        relative = unquote(name).replace("\\", "/").lstrip("/")
        target = (UPLOADS_DIR / relative).resolve()
        if (
            not is_within_path(target, UPLOADS_DIR)
            or target.suffix.lower() not in LOCAL_IMAGE_EXTENSIONS
            or not target.exists()
            or not target.is_file()
        ):
            return text_response(self, "Not found", HTTPStatus.NOT_FOUND)
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "private, max-age=3600")
        self.end_headers()
        self.wfile.write(body)

    def handle_error(self, exc: Exception) -> None:
        traceback.print_exc()
        status = (
            HTTPStatus.BAD_REQUEST
            if isinstance(
                exc,
                (
                    ValueError,
                    ArticleError,
                    AIProviderError,
                    DraftServiceError,
                    ImageServiceError,
                    RewriteServiceError,
                    json.JSONDecodeError,
                ),
            )
            else HTTPStatus.INTERNAL_SERVER_ERROR
        )
        json_response(self, friendly_error_payload(exc), status)


def main() -> int:
    args = [arg for arg in sys.argv[1:] if arg != "--no-browser"]
    port = int(args[0]) if args else 8770
    url = f"http://127.0.0.1:{port}/"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if probe.connect_ex(("127.0.0.1", port)) == 0:
            print(f"WeWrite already appears to be running: {url}")
            if "--no-browser" not in sys.argv:
                webbrowser.open(url)
            return 0
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    print(f"WeWrite local app: {url}")
    print(f"User data: {DATA_ROOT}")
    print("Press Ctrl+C to stop.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
