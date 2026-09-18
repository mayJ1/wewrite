from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from ai_provider import AIProviderError, build_provider
from edit_learning_service import list_active_rules


RESOURCE_DIR = Path(os.environ.get("WEWRITE_RESOURCE_DIR") or Path(__file__).resolve().parent.parent)
SKILL_DIR = Path(os.environ.get("WEWRITE_DATA_DIR") or RESOURCE_DIR)
APP_DIR = RESOURCE_DIR / "app"
PROMPT_PATH = APP_DIR / "prompts" / "campus_article.md"
PLAYBOOK_PATH = SKILL_DIR / "playbook.md"
STYLE_PATH = SKILL_DIR / "style.yaml"
PERSONAS_DIR = SKILL_DIR / "personas"
HISTORY_PATH = SKILL_DIR / "history.yaml"
EXEMPLARS_DIR = SKILL_DIR / "references" / "exemplars"
EXEMPLAR_INDEX_PATH = EXEMPLARS_DIR / "index.yaml"


class DraftServiceError(RuntimeError):
    pass


def load_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def load_recent_history(limit: int = 5) -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    with HISTORY_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or []
    if not isinstance(data, list):
        return []
    return [item for item in data[-limit:] if isinstance(item, dict)]


def load_exemplar_index() -> list[dict[str, Any]]:
    if not EXEMPLAR_INDEX_PATH.exists():
        return []
    with EXEMPLAR_INDEX_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict) and item.get("file")]


def compact_exemplar_text(text: str, limit: int = 1400) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                lines = lines[index + 1 :]
                break
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "```":
            continue
        cleaned_lines.append(stripped)
    compacted = "\n".join(cleaned_lines)
    if len(compacted) <= limit:
        return compacted
    return compacted[:limit].rstrip() + "..."


def load_exemplar_snippet(entry: dict[str, Any], *, limit: int = 1400) -> dict[str, Any] | None:
    filename = str(entry.get("file") or "").strip()
    if not filename:
        return None
    path = (EXEMPLARS_DIR / filename).resolve()
    if not str(path).startswith(str(EXEMPLARS_DIR.resolve())) or not path.exists() or not path.is_file():
        return None
    text = load_text(path)
    snippet = compact_exemplar_text(text, limit=limit)
    if not snippet:
        return None
    return {
        "file": filename,
        "category": entry.get("category") or "general",
        "source": entry.get("source") or "",
        "extracted_at": entry.get("extracted_at") or "",
        "humanness_score": entry.get("humanness_score"),
        "snippet": snippet,
    }


def select_exemplars(requirements: dict[str, Any], *, limit: int = 3) -> list[dict[str, Any]]:
    mode = str(requirements.get("exemplar_mode") or "default").strip()
    if mode in {"none", "off", "false", "0"}:
        return []

    selected_file = str(requirements.get("exemplar_file") or "").strip()
    if selected_file and selected_file != "auto":
        for entry in load_exemplar_index():
            if str(entry.get("file") or "").strip() == selected_file:
                snippet = load_exemplar_snippet(entry)
                return [snippet] if snippet else []
        return []

    article_type = str(requirements.get("article_type") or "").strip()
    persona = str(requirements.get("persona") or "").strip()
    preferred_categories = ["general"]
    if article_type in {"campus_activity", "profile"} or persona in {"warm-editor", "campus-lively"}:
        preferred_categories = ["general", "story-emotional"]

    entries = load_exemplar_index()
    ranked = sorted(
        entries,
        key=lambda item: (
            0 if str(item.get("category") or "general") in preferred_categories else 1,
            float(item.get("humanness_score") or 999),
        ),
    )
    snippets: list[dict[str, Any]] = []
    for entry in ranked:
        snippet = load_exemplar_snippet(entry)
        if snippet:
            snippets.append(snippet)
        if len(snippets) >= limit:
            break
    return snippets


def public_exemplar_library() -> list[dict[str, Any]]:
    library = []
    for entry in load_exemplar_index():
        snippet = load_exemplar_snippet(entry, limit=260)
        item = {
            "file": entry.get("file"),
            "category": entry.get("category") or "general",
            "source": entry.get("source") or "",
            "extracted_at": entry.get("extracted_at") or "",
            "humanness_score": entry.get("humanness_score"),
            "snippet": snippet["snippet"] if snippet else "",
        }
        library.append(item)
    return library


def load_writing_context() -> dict[str, Any]:
    style = load_yaml(STYLE_PATH)
    persona_name = str(style.get("writing_persona") or "warm-editor").strip()
    persona = load_yaml(PERSONAS_DIR / f"{persona_name}.yaml")
    return {
        "playbook": load_text(PLAYBOOK_PATH),
        "style": style,
        "persona_name": persona_name,
        "persona": persona,
        "history": load_recent_history(),
        "learned_edit_rules": list_active_rules(minimum_confidence=0.55, limit=12),
    }


def compact_materials(materials: Any, materials_text: str) -> dict[str, Any]:
    if isinstance(materials, dict):
        documents = materials.get("documents") if isinstance(materials.get("documents"), list) else []
        photos = materials.get("photos") if isinstance(materials.get("photos"), list) else []
        text_parts = []
        for doc in documents:
            if not isinstance(doc, dict):
                continue
            filename = str(doc.get("filename") or "未命名文档")
            text = str(doc.get("text") or "").strip()
            if text:
                text_parts.append(f"【{filename}】\n{text}")
        return {
            "text": "\n\n".join(text_parts) or materials_text,
            "photos": photos[:60],
            "categories": materials.get("categories"),
            "stats": materials.get("stats"),
        }
    return {"text": materials_text, "photos": [], "categories": None, "stats": None}


def build_prompt_payload(request: dict[str, Any]) -> dict[str, Any]:
    topic = str(request.get("topic") or "").strip()
    materials_text = str(request.get("materials_text") or "").strip()
    template = str(request.get("template") or "studio-brief").strip() or "studio-brief"
    requirements = request.get("requirements") if isinstance(request.get("requirements"), dict) else {}
    materials = compact_materials(request.get("materials"), materials_text)
    image_mode = str(requirements.get("image_mode") or "").strip()
    if image_mode in {"ai_generated", "ai_cover", "none"}:
        materials["photos"] = []
    if not topic:
        raise DraftServiceError("请填写文章主题。")
    if not materials["text"]:
        raise DraftServiceError("请提供素材文本。")
    context = load_writing_context()
    payload = {
        "topic": topic,
        "template": template,
        "date": str(request.get("date") or date.today().isoformat()),
        "requirements": requirements,
        "materials": materials,
        "exemplars": select_exemplars(requirements),
        "writing_context": context,
    }
    previous_article = compact_previous_article(request.get("previous_article"))
    if previous_article:
        payload["previous_article"] = previous_article
    return payload


def compact_previous_article(article: Any) -> dict[str, Any] | None:
    if not isinstance(article, dict):
        return None
    meta = article.get("meta") if isinstance(article.get("meta"), dict) else {}
    headline = article.get("headline") if isinstance(article.get("headline"), dict) else {}
    compact: dict[str, Any] = {
        "title": meta.get("title") or headline.get("title") or "",
        "digest": meta.get("digest") or "",
        "headline_body": headline.get("body") or [],
        "sections": [],
    }
    for section in article.get("sections") or []:
        if not isinstance(section, dict):
            continue
        blocks = []
        for block in section.get("blocks") or []:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "paragraph")
            if block_type == "image":
                blocks.append({"type": "image", "caption": str(block.get("caption") or "")[:80]})
            else:
                text = block.get("text") or block.get("body") or block.get("title") or ""
                blocks.append(
                    {
                        "type": block_type,
                        "title": str(block.get("title") or "")[:80],
                        "text": str(text)[:240],
                    }
                )
        compact["sections"].append(
            {
                "cn": section.get("cn") or section.get("title") or "",
                "intro": str(section.get("intro") or "")[:240],
                "blocks": blocks[:8],
            }
        )
    return compact


def build_prompts(payload: dict[str, Any]) -> tuple[str, str]:
    system_prompt = load_text(PROMPT_PATH)
    if not system_prompt:
        raise DraftServiceError("缺少写稿 prompt 模板。")
    user_prompt = (
        "请根据以下 JSON 输入生成一篇微信公众号文章。\n"
        "务必只返回一个合法 JSON 对象，不要 Markdown，不要解释。\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    requirements = payload.get("requirements") if isinstance(payload.get("requirements"), dict) else {}
    revision_request = str(requirements.get("revision_request") or "").strip()
    if revision_request:
        user_prompt = (
            "请根据以下 JSON 输入重新生成一篇微信公众号文章。输入中包含 previous_article 和 revision_request："
            "你需要参考 previous_article 的当前版本，并优先执行 revision_request 中的修改意见。"
            "事实仍只能来自 materials 和 requirements，不得因为修改意见而编造素材外细节。\n"
            "务必只返回一个合法 JSON 对象，不要 Markdown，不要解释。\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
    return system_prompt, user_prompt


def normalize_article(raw: dict[str, Any]) -> dict[str, Any]:
    article = raw.get("article") if isinstance(raw.get("article"), dict) else raw
    if not isinstance(article, dict):
        raise DraftServiceError("AI 没有返回 article 对象。")
    return article


def generate_article_draft(
    *,
    request: dict[str, Any],
    config: dict[str, Any],
    render_article,
    validate_article,
) -> dict[str, Any]:
    provider = build_provider(config)
    payload = build_prompt_payload(request)
    system_prompt, user_prompt = build_prompts(payload)
    raw = provider.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
    article = normalize_article(raw)

    html_text = render_article(article)
    validation = validate_article(article, html_text=html_text)
    response: dict[str, Any] = {
        "ok": validation.ok,
        "article": article,
        "html": html_text,
        "errors": validation.errors,
        "warnings": validation.warnings,
    }
    if validation.ok:
        return response

    repair_prompt = (
        "上一次生成的 article JSON 没有通过本地校验。\n"
        "请只返回修复后的合法 article JSON 对象。\n"
        f"校验错误：{json.dumps(validation.errors, ensure_ascii=False)}\n"
        f"校验提醒：{json.dumps(validation.warnings, ensure_ascii=False)}\n"
        f"原始 article：{json.dumps(article, ensure_ascii=False)}"
    )
    try:
        repaired_raw = provider.generate_json(system_prompt=system_prompt, user_prompt=repair_prompt)
        repaired_article = normalize_article(repaired_raw)
        repaired_html = render_article(repaired_article)
        repaired_validation = validate_article(repaired_article, html_text=repaired_html)
        return {
            "ok": repaired_validation.ok,
            "article": repaired_article,
            "html": repaired_html,
            "errors": repaired_validation.errors,
            "warnings": repaired_validation.warnings,
            "repaired": True,
        }
    except (AIProviderError, DraftServiceError) as exc:
        response["repair_error"] = str(exc)
        return response
