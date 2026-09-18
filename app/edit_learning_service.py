from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from bs4 import BeautifulSoup

from ai_provider import build_provider
from publisher import get_draft_article
from wechat_api import get_access_token


RESOURCE_DIR = Path(os.environ.get("WEWRITE_RESOURCE_DIR") or Path(__file__).resolve().parent.parent)
DATA_DIR = Path(os.environ.get("WEWRITE_DATA_DIR") or RESOURCE_DIR)
LESSONS_DIR = DATA_DIR / "lessons"
STORE_PATH = LESSONS_DIR / "edit-learning.json"

ALLOWED_RULE_TYPES = {
    "title",
    "tone",
    "structure",
    "length",
    "wording",
    "opening",
    "ending",
    "format",
}

ANALYSIS_SYSTEM_PROMPT = """你是微信公众号编辑偏好分析器。
请比较 AI 初稿和用户在微信草稿箱修改后的版本，只提取以后写其他文章时仍然适用的写作偏好。

必须遵守：
- 只返回合法 JSON 对象，不要 Markdown，不要解释。
- 不得把本篇活动事实的增删、姓名、时间、地点、数据和图片变化当成长期偏好。
- 不得学习可能导致虚构事实的规则。
- 只提取标题、语气、结构、篇幅、措辞、开头、结尾和格式方面的可复用偏好。
- 没有足够证据时 rules 返回空数组，不要勉强总结。
- 每条 rule 必须是简短、明确、可执行的中文指令。
- 最多返回 5 条规则。

返回结构：
{
  "summary": "一句话说明用户主要修改了什么",
  "rules": [
    {
      "key": "稳定的英文 snake_case 标识",
      "type": "title|tone|structure|length|wording|opening|ending|format",
      "rule": "以后写稿时可直接执行的中文指令",
      "evidence": "本次修改中支持该规则的简短证据",
      "confidence": 0.55
    }
  ]
}
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _empty_store() -> dict[str, Any]:
    return {"version": 1, "rules": [], "sessions": []}


def load_learning_store() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return _empty_store()
    try:
        data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_store()
    if not isinstance(data, dict):
        return _empty_store()
    rules = data.get("rules") if isinstance(data.get("rules"), list) else []
    sessions = data.get("sessions") if isinstance(data.get("sessions"), list) else []
    return {"version": 1, "rules": rules, "sessions": sessions}


def save_learning_store(store: dict[str, Any]) -> None:
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "rules": store.get("rules") if isinstance(store.get("rules"), list) else [],
        "sessions": (store.get("sessions") if isinstance(store.get("sessions"), list) else [])[:100],
    }
    temp_path = STORE_PATH.with_name(f"{STORE_PATH.name}.{uuid.uuid4().hex}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(STORE_PATH)


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def extract_editorial_text(html_text: str) -> str:
    soup = BeautifulSoup(str(html_text or ""), "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    lines: list[str] = []
    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote"]):
        text = _clean_text(element.get_text(" ", strip=True))
        if text and (not lines or lines[-1] != text):
            lines.append(text)
    if not lines:
        fallback = _clean_text(soup.get_text("\n", strip=True))
        return fallback
    return "\n".join(lines)


def local_document(article: dict[str, Any], html_text: str) -> dict[str, str]:
    meta = article.get("meta") if isinstance(article.get("meta"), dict) else {}
    return {
        "title": _clean_text(meta.get("title")),
        "digest": _clean_text(meta.get("digest")),
        "body": extract_editorial_text(html_text),
    }


def wechat_document(article: dict[str, Any]) -> dict[str, str]:
    return {
        "title": _clean_text(article.get("title")),
        "digest": _clean_text(article.get("digest")),
        "body": extract_editorial_text(str(article.get("content") or "")),
    }


def _document_text(document: dict[str, str]) -> str:
    return "\n".join(
        part
        for part in (
            f"标题：{document.get('title', '')}" if document.get("title") else "",
            f"摘要：{document.get('digest', '')}" if document.get("digest") else "",
            document.get("body", ""),
        )
        if part
    )


def build_edit_snapshot(local: dict[str, str], final: dict[str, str]) -> dict[str, Any]:
    local_text = _document_text(local)
    final_text = _document_text(final)
    diff_lines = list(
        difflib.unified_diff(
            local_text.splitlines(),
            final_text.splitlines(),
            fromfile="AI 初稿",
            tofile="微信修改稿",
            lineterm="",
            n=2,
        )
    )
    additions = [line for line in diff_lines if line.startswith("+") and not line.startswith("+++")]
    deletions = [line for line in diff_lines if line.startswith("-") and not line.startswith("---")]
    normalized_local = _clean_text(local_text)
    normalized_final = _clean_text(final_text)
    return {
        "changed": normalized_local != normalized_final,
        "title_changed": local.get("title") != final.get("title"),
        "digest_changed": local.get("digest") != final.get("digest"),
        "similarity": round(difflib.SequenceMatcher(None, normalized_local, normalized_final).ratio(), 4),
        "char_delta": len(normalized_final) - len(normalized_local),
        "lines_added": len(additions),
        "lines_deleted": len(deletions),
        "local": {
            "title": local.get("title", ""),
            "digest": local.get("digest", ""),
            "body": local.get("body", "")[:9000],
        },
        "final": {
            "title": final.get("title", ""),
            "digest": final.get("digest", ""),
            "body": final.get("body", "")[:9000],
        },
        "diff_excerpt": "\n".join(diff_lines[:180])[:12000],
    }


def _content_hash(document: dict[str, str]) -> str:
    return hashlib.sha256(_document_text(document).encode("utf-8")).hexdigest()


def _rule_key(raw_key: Any, rule: str) -> str:
    key = re.sub(r"[^a-z0-9_]+", "_", str(raw_key or "").strip().lower()).strip("_")
    if key:
        return key[:80]
    return f"rule_{hashlib.sha1(rule.encode('utf-8')).hexdigest()[:12]}"


def _normalize_rules(raw_rules: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_rules, list):
        return []
    normalized: list[dict[str, Any]] = []
    for raw in raw_rules[:5]:
        if not isinstance(raw, dict):
            continue
        rule = _clean_text(raw.get("rule"))
        if len(rule) < 6:
            continue
        rule_type = str(raw.get("type") or "wording").strip().lower()
        if rule_type not in ALLOWED_RULE_TYPES:
            rule_type = "wording"
        try:
            confidence = float(raw.get("confidence") or 0.6)
        except (TypeError, ValueError):
            confidence = 0.6
        normalized.append(
            {
                "key": _rule_key(raw.get("key"), rule),
                "type": rule_type,
                "rule": rule[:180],
                "evidence": _clean_text(raw.get("evidence"))[:220],
                "confidence": round(max(0.5, min(0.9, confidence)), 2),
            }
        )
    return normalized


def analyze_edit_preferences(
    snapshot: dict[str, Any],
    config: dict[str, Any],
    *,
    provider_factory: Callable[[dict[str, Any]], Any] = build_provider,
) -> dict[str, Any]:
    provider = provider_factory(config)
    result = provider.generate_json(
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        user_prompt=(
            "请分析下面的初稿与微信修改稿，提取可复用编辑偏好：\n\n"
            + json.dumps(snapshot, ensure_ascii=False, indent=2)
        ),
        temperature=0.2,
        max_tokens=1800,
    )
    return {
        "summary": _clean_text(result.get("summary"))[:300] or "已完成修改对比。",
        "rules": _normalize_rules(result.get("rules")),
    }


def _public_rule(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        key: rule.get(key)
        for key in (
            "id",
            "key",
            "type",
            "rule",
            "evidence",
            "confidence",
            "occurrences",
            "first_seen",
            "last_seen",
        )
    }


def _merge_rules(
    store: dict[str, Any],
    learned_rules: list[dict[str, Any]],
    *,
    history_id: str,
    revision_hash: str,
) -> list[dict[str, Any]]:
    now = _now()
    stored_rules = store.setdefault("rules", [])
    session_rule_ids: list[str] = []
    for learned in learned_rules:
        existing = next(
            (
                item
                for item in stored_rules
                if isinstance(item, dict) and str(item.get("key") or "") == learned["key"]
            ),
            None,
        )
        source_key = f"{history_id}:{revision_hash}"
        if existing:
            sources = existing.setdefault("sources", [])
            if source_key not in sources:
                sources.append(source_key)
                existing["occurrences"] = int(existing.get("occurrences") or 1) + 1
                existing["confidence"] = round(
                    min(0.98, max(float(existing.get("confidence") or 0.5), learned["confidence"]) + 0.06),
                    2,
                )
            existing.update(
                {
                    "type": learned["type"],
                    "rule": learned["rule"],
                    "evidence": learned["evidence"],
                    "last_seen": now,
                    "active": True,
                }
            )
            session_rule_ids.append(str(existing.get("id")))
            continue
        item = {
            "id": uuid.uuid4().hex,
            **learned,
            "occurrences": 1,
            "first_seen": now,
            "last_seen": now,
            "active": True,
            "sources": [source_key],
        }
        stored_rules.append(item)
        session_rule_ids.append(item["id"])
    return [
        _public_rule(item)
        for item in stored_rules
        if isinstance(item, dict) and str(item.get("id") or "") in session_rule_ids
    ]


def learn_from_documents(
    *,
    history_id: str,
    media_id: str,
    local: dict[str, str],
    final: dict[str, str],
    config: dict[str, Any],
    provider_factory: Callable[[dict[str, Any]], Any] = build_provider,
) -> dict[str, Any]:
    store = load_learning_store()
    snapshot = build_edit_snapshot(local, final)
    revision_hash = _content_hash(final)
    previous = next(
        (
            item
            for item in store.get("sessions", [])
            if isinstance(item, dict)
            and item.get("history_id") == history_id
            and item.get("revision_hash") == revision_hash
        ),
        None,
    )
    if previous:
        rule_ids = set(previous.get("rule_ids") or [])
        rules = [
            _public_rule(item)
            for item in store.get("rules", [])
            if isinstance(item, dict) and item.get("id") in rule_ids and item.get("active", True)
        ]
        return {
            "ok": True,
            "changed": bool(previous.get("changed")),
            "already_synced": True,
            "summary": previous.get("summary") or "这一版微信草稿已经学习过了。",
            "rules": rules,
            "diff": previous.get("diff") or {},
        }

    analysis = {"summary": "微信草稿与本地初稿一致，没有发现需要学习的修改。", "rules": []}
    if snapshot["changed"]:
        analysis = analyze_edit_preferences(snapshot, config, provider_factory=provider_factory)
    rules = _merge_rules(
        store,
        analysis["rules"],
        history_id=history_id,
        revision_hash=revision_hash,
    )
    session = {
        "id": uuid.uuid4().hex,
        "history_id": history_id,
        "media_id": media_id,
        "revision_hash": revision_hash,
        "created_at": _now(),
        "changed": snapshot["changed"],
        "summary": analysis["summary"],
        "rule_ids": [rule["id"] for rule in rules],
        "diff": {
            key: snapshot[key]
            for key in (
                "title_changed",
                "digest_changed",
                "similarity",
                "char_delta",
                "lines_added",
                "lines_deleted",
            )
        },
    }
    store.setdefault("sessions", []).insert(0, session)
    save_learning_store(store)
    return {
        "ok": True,
        "changed": snapshot["changed"],
        "already_synced": False,
        "summary": analysis["summary"],
        "rules": rules,
        "diff": session["diff"],
    }


def sync_wechat_draft_and_learn(
    *,
    record: dict[str, Any],
    article: dict[str, Any],
    original_html: str,
    config: dict[str, Any],
    provider_factory: Callable[[dict[str, Any]], Any] = build_provider,
) -> dict[str, Any]:
    history_id = str(record.get("id") or "").strip()
    media_id = str(record.get("media_id") or "").strip()
    if not history_id or not media_id:
        raise ValueError("这篇文章还没有推送到微信草稿箱，暂时无法同步修改。")
    wechat = config.get("wechat") if isinstance(config.get("wechat"), dict) else {}
    appid = str(wechat.get("appid") or "").strip()
    secret = str(wechat.get("secret") or "").strip()
    if not appid or not secret:
        raise ValueError("请先在设置中配置微信公众号 AppID 和 AppSecret。")
    token = get_access_token(appid, secret)
    final_article = get_draft_article(token, media_id)
    return learn_from_documents(
        history_id=history_id,
        media_id=media_id,
        local=local_document(article, original_html),
        final=wechat_document(final_article),
        config=config,
        provider_factory=provider_factory,
    )


def list_active_rules(*, minimum_confidence: float = 0.0, limit: int = 20) -> list[dict[str, Any]]:
    store = load_learning_store()
    rules = [
        item
        for item in store.get("rules", [])
        if isinstance(item, dict)
        and item.get("active", True)
        and float(item.get("confidence") or 0) >= minimum_confidence
    ]
    rules.sort(
        key=lambda item: (
            float(item.get("confidence") or 0),
            int(item.get("occurrences") or 0),
            str(item.get("last_seen") or ""),
        ),
        reverse=True,
    )
    return [_public_rule(item) for item in rules[:limit]]


def public_learning_state() -> dict[str, Any]:
    store = load_learning_store()
    sessions = [
        {
            key: item.get(key)
            for key in ("id", "history_id", "created_at", "changed", "summary", "rule_ids", "diff")
        }
        for item in store.get("sessions", [])[:20]
        if isinstance(item, dict)
    ]
    rules = list_active_rules()
    return {
        "rules": rules,
        "sessions": sessions,
        "rule_count": len(rules),
        "session_count": len(store.get("sessions", [])),
    }


def delete_learning_rule(rule_id: str) -> dict[str, Any]:
    value = str(rule_id or "").strip()
    if not value:
        raise ValueError("缺少要删除的学习规则。")
    store = load_learning_store()
    before = len(store.get("rules", []))
    store["rules"] = [
        item
        for item in store.get("rules", [])
        if not (isinstance(item, dict) and str(item.get("id") or "") == value)
    ]
    if len(store["rules"]) == before:
        raise ValueError("没有找到这条学习规则。")
    save_learning_store(store)
    return {"ok": True, "rule_id": value}
