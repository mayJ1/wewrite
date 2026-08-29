from __future__ import annotations

import re
import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests


TIMEOUT = (10, 15)
MAX_RETRIES = 3
RETRY_BACKOFF = (1, 2)
CACHE_SECONDS = 180
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}
SOURCE_NAMES = {
    "weibo": "微博",
    "toutiao": "今日头条",
    "baidu": "百度",
}
LABELS = {
    "hot": "热",
    "new": "新",
    "refuterumors": "辟谣",
    "recentprogress": "新进展",
}

_cache_lock = threading.Lock()
_cache: dict = {"created_at": 0.0, "payload": None}


def _request_json(url: str, *, headers: dict | None = None) -> dict:
    request_headers = {**HEADERS, **(headers or {})}
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=request_headers, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])
    if last_error:
        raise last_error
    raise RuntimeError("热点接口请求失败。")


def _number(value: object, default: int = 0) -> int:
    try:
        return int(float(str(value or default)))
    except (TypeError, ValueError):
        return default


def _safe_url(value: object) -> str:
    url = str(value or "").strip()
    return url if url.startswith(("https://", "http://")) else ""


def _label(value: object) -> str:
    label = str(value or "").strip()
    if not label or label.isdigit():
        return ""
    return LABELS.get(label.lower(), label if len(label) <= 8 else "")


def parse_weibo(data: dict) -> list[dict]:
    items = []
    for position, entry in enumerate(data.get("data", {}).get("realtime", []), start=1):
        title = str(entry.get("note") or entry.get("word") or "").strip()
        if not title:
            continue
        items.append(
            {
                "title": title,
                "source": "微博",
                "hot": _number(entry.get("num")),
                "rank": _number(entry.get("realpos"), position) or position,
                "url": f"https://s.weibo.com/weibo?q={quote(f'#{title}#')}",
                "description": _label(entry.get("label_name")),
            }
        )
    return items


def parse_toutiao(data: dict) -> list[dict]:
    items = []
    for position, entry in enumerate(data.get("data", []), start=1):
        title = str(entry.get("Title") or entry.get("QueryWord") or "").strip()
        if not title:
            continue
        items.append(
            {
                "title": title,
                "source": "今日头条",
                "hot": _number(entry.get("HotValue")),
                "rank": position,
                "url": _safe_url(entry.get("Url")),
                "description": _label(entry.get("Label")),
            }
        )
    return items


def _baidu_entries(data: dict) -> list[dict]:
    entries = []
    for card in data.get("data", {}).get("cards", []):
        content = card.get("content", [])
        if not content:
            continue
        nested = content[0].get("content", []) if isinstance(content[0], dict) else content
        if isinstance(nested, list):
            entries.extend(item for item in nested if isinstance(item, dict))
    return entries


def parse_baidu(data: dict) -> list[dict]:
    items = []
    for position, entry in enumerate(_baidu_entries(data), start=1):
        title = str(entry.get("word") or "").strip()
        if not title:
            continue
        rank = _number(entry.get("index"), position) or position
        hot = _number(entry.get("hotScore"))
        items.append(
            {
                "title": title,
                "source": "百度",
                "hot": hot,
                "rank": rank,
                "url": _safe_url(entry.get("url")),
                "description": _label(entry.get("hotTag")),
            }
        )
    return items


def fetch_weibo() -> list[dict]:
    return parse_weibo(
        _request_json(
            "https://weibo.com/ajax/side/hotSearch",
            headers={"Referer": "https://weibo.com/"},
        )
    )


def fetch_toutiao() -> list[dict]:
    return parse_toutiao(
        _request_json("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
    )


def fetch_baidu() -> list[dict]:
    return parse_baidu(
        _request_json("https://top.baidu.com/api/board?platform=wise&tab=realtime")
    )


def _title_key(title: str) -> str:
    return re.sub(r"[\s\u3000，。！？、；：,.!?;:'\"“”‘’（）()【】\[\]《》<>#]+", "", title).lower()


def _rank_score(rank: int, total: int) -> float:
    if total <= 1:
        return 100.0
    return round(100 - ((max(rank, 1) - 1) * 99 / (total - 1)), 1)


def merge_hotspots(items: list[dict]) -> list[dict]:
    by_source: dict[str, list[dict]] = {}
    for item in items:
        by_source.setdefault(item["source"], []).append(item)

    for source_items in by_source.values():
        source_items.sort(key=lambda item: (item.get("rank", 9999), -item.get("hot", 0), item["title"]))
        total = len(source_items)
        for position, item in enumerate(source_items, start=1):
            item["rank"] = _number(item.get("rank"), position) or position
            item["hot_normalized"] = _rank_score(position, total)

    merged: dict[str, dict] = {}
    for item in items:
        key = _title_key(item["title"])
        if not key:
            continue
        source_detail = {
            "name": item["source"],
            "rank": item["rank"],
            "hot": item["hot"],
            "url": item.get("url", ""),
            "description": item.get("description", ""),
        }
        if key not in merged:
            merged[key] = {
                **item,
                "sources": [item["source"]],
                "source_details": [source_detail],
                "platform_count": 1,
            }
            continue
        current = merged[key]
        current["sources"].append(item["source"])
        current["source_details"].append(source_detail)
        current["platform_count"] = len(current["sources"])
        if item["hot_normalized"] > current["hot_normalized"]:
            current.update(
                {
                    "source": item["source"],
                    "hot": item["hot"],
                    "rank": item["rank"],
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "hot_normalized": item["hot_normalized"],
                }
            )

    result = list(merged.values())
    for item in result:
        item["hotspot_id"] = hashlib.sha1(_title_key(item["title"]).encode("utf-8")).hexdigest()[:12]
        item["score"] = min(100.0, round(item["hot_normalized"] + (item["platform_count"] - 1) * 3, 1))
    result.sort(key=lambda item: (-item["score"], -item["platform_count"], item["title"]))
    return result


def fetch_hotspots(*, limit: int = 60, force_refresh: bool = False) -> dict:
    limit = max(1, min(int(limit), 100))
    now = time.time()
    with _cache_lock:
        cached = _cache.get("payload")
        if cached and not force_refresh and now - float(_cache.get("created_at") or 0) < CACHE_SECONDS:
            return {**cached, "items": cached["items"][:limit], "cached": True}

    fetchers = {
        "weibo": fetch_weibo,
        "toutiao": fetch_toutiao,
        "baidu": fetch_baidu,
    }
    source_results: dict[str, list[dict]] = {}
    source_status = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetcher): key for key, fetcher in fetchers.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                source_items = future.result()
                source_results[key] = source_items
                source_status.append(
                    {"id": key, "name": SOURCE_NAMES[key], "ok": bool(source_items), "count": len(source_items)}
                )
            except Exception as exc:
                source_status.append(
                    {"id": key, "name": SOURCE_NAMES[key], "ok": False, "count": 0, "error": str(exc)[:240]}
                )

    source_status.sort(key=lambda item: list(SOURCE_NAMES).index(item["id"]))
    all_items = [item for key in fetchers for item in source_results.get(key, [])]
    merged_items = merge_hotspots(all_items)
    timestamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    payload = {
        "timestamp": timestamp,
        "count": len(merged_items),
        "items": merged_items,
        "source_status": source_status,
        "sources": [item["name"] for item in source_status if item["ok"]],
        "sources_failed": [item["name"] for item in source_status if not item["ok"]],
        "cached": False,
    }
    if not merged_items:
        payload["error"] = "暂时没有抓取到热点，请稍后刷新。"
    with _cache_lock:
        _cache["created_at"] = now
        _cache["payload"] = payload
    return {**payload, "items": merged_items[:limit]}
