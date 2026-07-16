from __future__ import annotations

import copy
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class RewriteServiceError(RuntimeError):
    pass


DEFAULT_BASE_URL = "http://127.0.0.1:8282"
DEFAULT_MODEL = "qwen3-merged-aigc_zhv3-Q4_K_M.gguf"
DEFAULT_SYSTEM_PROMPT = (
    "你是中文公众号文本的自然表达重写编辑。请在不改变原意、不增加事实、不删减关键信息的前提下，"
    "重组句式和表达顺序，让文本更像人工编辑后的成稿。减少模板化、机械重复、过度工整和空泛套话；"
    "可以合并或拆分句子，替换连接词，调整节奏，但不要加入素材外的新细节。"
    "严禁输出任务说明、提示词、标签或解释，只能输出改写后的正文。"
)
USER_PROMPT_PREFIX = (
    "任务：把 <article_text> 标签内的公众号正文改写得更自然。\n"
    "硬性规则：保留事实和原意；不要新增人名、时间、地点、数字或引语；"
    "不要复述本任务说明；不要输出 <article_text> 标签；只返回改写后的正文。\n\n"
    "<article_text>\n"
)
USER_PROMPT_SUFFIX = "\n</article_text>"

_SERVER_PROCESS: subprocess.Popen | None = None


def rewrite_status(config: dict, resource_root: Path) -> dict[str, Any]:
    rewrite_cfg = _rewrite_config(config)
    base_url = _base_url(rewrite_cfg)
    return {
        "enabled": bool(rewrite_cfg.get("enabled")),
        "auto_start": bool(rewrite_cfg.get("auto_start", True)),
        "base_url": base_url,
        "model": str(rewrite_cfg.get("model") or DEFAULT_MODEL),
        "available": _is_server_ready(base_url),
        "engine_found": _resolve_engine(rewrite_cfg, resource_root) is not None,
        "model_found": _resolve_model(rewrite_cfg, resource_root) is not None,
    }


def rewrite_article_text_fields(article: dict, *, config: dict, resource_root: Path) -> tuple[dict, dict[str, Any]]:
    rewrite_cfg = _rewrite_config(config)
    if not bool(rewrite_cfg.get("enabled", True)):
        return article, {"enabled": False, "changed_count": 0, "errors": []}

    base_url = _ensure_server(rewrite_cfg, resource_root)
    targets = _collect_text_targets(article)
    original_text = _article_plain_text(article, targets)
    rewritten = copy.deepcopy(article)
    errors: list[str] = []
    changed_count = 0
    protected_count = 0
    unchanged_count = 0

    for index, path in enumerate(targets, start=1):
        original = str(_get_path(rewritten, path) or "").strip()
        if not _should_rewrite(original):
            protected_count += 1
            continue
        try:
            updated = _rewrite_text(original, rewrite_cfg=rewrite_cfg, base_url=base_url)
        except RewriteServiceError as exc:
            errors.append(f"第 {index} 段润色失败：{exc}")
            continue
        if not updated or updated == original:
            unchanged_count += 1
        else:
            _set_path(rewritten, path, updated)
            changed_count += 1

    return rewritten, {
        "enabled": True,
        "base_url": base_url,
        "model": str(rewrite_cfg.get("model") or DEFAULT_MODEL),
        "target_count": len(targets),
        "eligible_count": len(targets) - protected_count,
        "changed_count": changed_count,
        "skipped_count": protected_count + unchanged_count,
        "protected_count": protected_count,
        "unchanged_count": unchanged_count,
        "original_text": original_text,
        "errors": errors,
    }


def _rewrite_config(config: dict) -> dict:
    raw = config.get("rewrite") if isinstance(config.get("rewrite"), dict) else {}
    return {
        "enabled": bool(raw.get("enabled", True)),
        "auto_start": bool(raw.get("auto_start", True)),
        "base_url": str(raw.get("base_url") or DEFAULT_BASE_URL).strip(),
        "model": str(raw.get("model") or DEFAULT_MODEL).strip(),
        "engine_dir": str(raw.get("engine_dir") or "").strip(),
        "timeout": int(raw.get("timeout") or 120),
        "temperature": float(raw.get("temperature") or 0.72),
        "top_p": float(raw.get("top_p") or 0.9),
        "max_tokens": int(raw.get("max_tokens") or 1024),
        "frequency_penalty": float(raw.get("frequency_penalty") or 0.35),
        "system_prompt": str(raw.get("system_prompt") or DEFAULT_SYSTEM_PROMPT).strip(),
    }


def _base_url(rewrite_cfg: dict) -> str:
    return str(rewrite_cfg.get("base_url") or DEFAULT_BASE_URL).rstrip("/")


def _chat_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/v1/chat/completions"


def _models_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/v1/models"


def _is_server_ready(base_url: str) -> bool:
    try:
        request = Request(_models_url(base_url), headers={"User-Agent": "WeWrite/Rewrite"})
        with urlopen(request, timeout=2) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def _ensure_server(rewrite_cfg: dict, resource_root: Path) -> str:
    base_url = _base_url(rewrite_cfg)
    if _is_server_ready(base_url):
        return base_url
    if not bool(rewrite_cfg.get("auto_start", True)):
        raise RewriteServiceError(f"本地改写服务未启动：{base_url}")

    engine = _resolve_engine(rewrite_cfg, resource_root)
    model = _resolve_model(rewrite_cfg, resource_root)
    if not engine:
        raise RewriteServiceError("找不到 llama-server.exe。请把格式工坊运行文件放入 rewrite-engine 目录。")
    if not model:
        raise RewriteServiceError(f"找不到改写模型 {rewrite_cfg.get('model') or DEFAULT_MODEL}。")

    host, port = _parse_host_port(base_url)
    _start_server(engine, model, host=host, port=port)
    deadline = time.time() + 45
    while time.time() < deadline:
        if _is_server_ready(base_url):
            return base_url
        time.sleep(1)
    raise RewriteServiceError("本地改写服务启动超时，请稍后重试或手动检查模型文件。")


def _start_server(engine: Path, model: Path, *, host: str, port: int) -> None:
    global _SERVER_PROCESS
    if _SERVER_PROCESS and _SERVER_PROCESS.poll() is None:
        return
    args = [
        str(engine),
        "-m",
        str(model),
        "--host",
        host,
        "--port",
        str(port),
        "--reasoning",
        "off",
        "--reasoning-format",
        "none",
    ]
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    _SERVER_PROCESS = subprocess.Popen(
        args,
        cwd=str(model.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def _resolve_engine(rewrite_cfg: dict, resource_root: Path) -> Path | None:
    engine_dir = _engine_dir(rewrite_cfg, resource_root)
    preferred = engine_dir / "llama-server.exe"
    if preferred.exists():
        return preferred
    if engine_dir.exists():
        for path in engine_dir.rglob("llama-server.exe"):
            return path
    return None


def _resolve_model(rewrite_cfg: dict, resource_root: Path) -> Path | None:
    model_name = str(rewrite_cfg.get("model") or DEFAULT_MODEL)
    model_path = Path(model_name)
    if model_path.is_absolute() and model_path.exists():
        return model_path
    engine_dir = _engine_dir(rewrite_cfg, resource_root)
    candidate = engine_dir / model_name
    if candidate.exists():
        return candidate
    if engine_dir.exists():
        for path in engine_dir.rglob(model_name):
            return path
    return None


def _engine_dir(rewrite_cfg: dict, resource_root: Path) -> Path:
    configured = str(rewrite_cfg.get("engine_dir") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (resource_root / "rewrite-engine").resolve()


def _parse_host_port(base_url: str) -> tuple[str, int]:
    without_scheme = base_url.split("://", 1)[-1].split("/", 1)[0]
    if ":" not in without_scheme:
        return without_scheme or "127.0.0.1", 80
    host, raw_port = without_scheme.rsplit(":", 1)
    try:
        return host or "127.0.0.1", int(raw_port)
    except ValueError as exc:
        raise RewriteServiceError(f"本地改写服务地址端口无效：{base_url}") from exc


def _rewrite_text(text: str, *, rewrite_cfg: dict, base_url: str) -> str:
    payload = {
        "model": str(rewrite_cfg.get("model") or DEFAULT_MODEL),
        "messages": [
            {"role": "system", "content": rewrite_cfg.get("system_prompt") or DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": f"{USER_PROMPT_PREFIX}{text}{USER_PROMPT_SUFFIX}"},
        ],
        "temperature": rewrite_cfg.get("temperature", 0.72),
        "top_p": rewrite_cfg.get("top_p", 0.9),
        "max_tokens": rewrite_cfg.get("max_tokens", 1024),
        "frequency_penalty": rewrite_cfg.get("frequency_penalty", 0.35),
        "reasoning": "off",
        "reasoning_format": "none",
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    request = Request(
        _chat_url(base_url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "WeWrite/Rewrite"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=int(rewrite_cfg.get("timeout") or 120)) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RewriteServiceError(f"HTTP {exc.code} {body[:200]}") from exc
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise RewriteServiceError(f"无法连接本地改写服务：{exc}") from exc
    except json.JSONDecodeError as exc:
        raise RewriteServiceError("本地改写服务返回格式异常。") from exc

    message = (data.get("choices") or [{}])[0].get("message") or {}
    content = _pick_text(message.get("content")) or _pick_text(message.get("reasoning_content"))
    content = _clean_rewrite_output(_strip_think_tags(content))
    if not content:
        return text
    return content


def _pick_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "".join(_pick_text(item.get("text") if isinstance(item, dict) else item) for item in value).strip()
    return ""


def _strip_think_tags(text: str) -> str:
    import re

    return re.sub(r"</?think>", "", re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.I), flags=re.I).strip()


def _clean_rewrite_output(text: str) -> str:
    import re

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    cleaned = re.sub(r"^```(?:\w+)?\s*|\s*```$", "", cleaned).strip()
    cleaned = re.sub(r"<\s*/?\s*article_text\s*>", "", cleaned, flags=re.I).strip()

    instruction_prefix_patterns = (
        r"^\s*任务[是就：:\s]*把[\s\S]{0,700}?(?:只|仅)(?:能|需|要)?(?:返回|输出)[^。！？\n]{0,80}改写后的正文[。！？；;，,\s]*",
        r"^\s*请对下面这段[\s\S]{0,700}?(?:只|仅)(?:能|需|要)?(?:返回|输出)[^。！？\n]{0,80}改写后的正文[。！？；;，,\s]*",
        r"^\s*硬性规则[：:\s][\s\S]{0,500}?(?:只|仅)(?:能|需|要)?(?:返回|输出)[^。！？\n]{0,80}改写后的正文[。！？；;，,\s]*",
        r"^\s*要求[：:\s][\s\S]{0,500}?(?:只|仅)(?:能|需|要)?(?:返回|输出)[^。！？\n]{0,80}改写后的正文[。！？；;，,\s]*",
    )
    for pattern in instruction_prefix_patterns:
        cleaned = re.sub(pattern, "", cleaned, count=1, flags=re.I).strip()

    for marker in (
        "只能返回改写后的正文。",
        "只返回改写后的正文。",
        "只输出改写后的正文，不要解释。",
        "只输出改写后的正文。",
        "不要解释。",
        "自然文本：",
    ):
        marker_index = cleaned.find(marker)
        if 0 <= marker_index < 320:
            cleaned = cleaned[marker_index + len(marker) :].strip()

    prompt_markers = (
        "请对下面这段公众号正文",
        "请对下面这段",
        "任务：把",
        "任务是把",
        "任务就是把",
        "硬性规则：",
        "硬性规则是",
        "要求：保留事实",
        "保留事实和原意",
        "不能添加人名",
        "不能加入人名",
        "不能重复本任务说明",
        "不能复述本任务说明",
        "不能输出标签",
        "不能输出 <article_text>",
        "不能输出<article_text>",
        "不要新增人名",
        "明显改变机械句式",
        "只输出改写后的正文",
        "只返回改写后的正文",
        "只能返回改写后的正文",
        "不要复述本任务说明",
        "自然表达重写",
        "改写提示词",
    )
    lines = []
    for line in cleaned.split("\n"):
        stripped = line.strip()
        if not stripped:
            lines.append(line)
            continue
        if any(marker in stripped for marker in prompt_markers):
            continue
        lines.append(line)
    cleaned = "\n".join(lines).strip()

    cleaned = re.sub(r"^(?:改写后的正文|正文|输出)[:：]\s*", "", cleaned).strip()
    return cleaned


def _should_rewrite(text: str) -> bool:
    cleaned = text.strip()
    return len(cleaned) >= 18 and not cleaned.startswith(("http://", "https://", "!["))


def _article_plain_text(article: dict, targets: list[list[Any]]) -> str:
    parts: list[str] = []
    title = article.get("meta", {}).get("title") if isinstance(article.get("meta"), dict) else ""
    if isinstance(title, str) and title.strip():
        parts.append(title.strip())
    for path in targets:
        value = _get_path(article, path)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return "\n\n".join(parts).strip()


def _collect_text_targets(article: dict) -> list[list[Any]]:
    targets: list[list[Any]] = []
    headline_body = article.get("headline", {}).get("body") if isinstance(article.get("headline"), dict) else None
    if isinstance(headline_body, list):
        for index, item in enumerate(headline_body):
            if isinstance(item, str):
                targets.append(["headline", "body", index])

    sections = article.get("sections") if isinstance(article.get("sections"), list) else []
    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        if isinstance(section.get("intro"), str):
            targets.append(["sections", section_index, "intro"])
        blocks = section.get("blocks") if isinstance(section.get("blocks"), list) else []
        for block_index, block in enumerate(blocks):
            if not isinstance(block, dict) or block.get("type") == "image":
                continue
            for field in ("text", "body"):
                value = block.get(field)
                if isinstance(value, str):
                    targets.append(["sections", section_index, "blocks", block_index, field])
                elif isinstance(value, list):
                    for item_index, item in enumerate(value):
                        if isinstance(item, str):
                            targets.append(["sections", section_index, "blocks", block_index, field, item_index])
            items = block.get("items")
            if isinstance(items, list):
                for item_index, item in enumerate(items):
                    if isinstance(item, str):
                        targets.append(["sections", section_index, "blocks", block_index, "items", item_index])
    return targets


def _get_path(root: dict, path: list[Any]) -> Any:
    value: Any = root
    for part in path:
        value = value[part]
    return value


def _set_path(root: dict, path: list[Any], new_value: Any) -> None:
    value: Any = root
    for part in path[:-1]:
        value = value[part]
    value[path[-1]] = new_value
