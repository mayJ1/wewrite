from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from image_service import generate_image


def _plain_text(value: Any, limit: int = 220) -> str:
    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)
    text = " ".join(str(value or "").split())
    return text[:limit]


def _first_block_text(section: dict[str, Any]) -> str:
    for block in section.get("blocks") or []:
        if not isinstance(block, dict) or block.get("type") == "image":
            continue
        for key in ("text", "body", "title", "items"):
            text = _plain_text(block.get(key))
            if text:
                return text
    return ""


def _candidate_sections(article: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    candidates = []
    for index, section in enumerate(article.get("sections") or []):
        if not isinstance(section, dict) or section.get("image"):
            continue
        detail = (
            _plain_text(section.get("intro"))
            or _first_block_text(section)
            or _plain_text(section.get("cn") or section.get("title"))
        )
        if detail:
            candidates.append((index, section))
    return candidates


def _spread_candidates(
    candidates: list[tuple[int, dict[str, Any]]],
    limit: int,
) -> list[tuple[int, dict[str, Any]]]:
    if len(candidates) <= limit:
        return candidates
    if limit <= 1:
        return [candidates[len(candidates) // 2]]
    indexes = {
        round(position * (len(candidates) - 1) / (limit - 1))
        for position in range(limit)
    }
    return [candidates[index] for index in sorted(indexes)]


def build_content_image_prompt(
    article: dict[str, Any],
    section: dict[str, Any],
    *,
    style: dict[str, Any],
) -> str:
    meta = article.get("meta") if isinstance(article.get("meta"), dict) else {}
    article_title = _plain_text(meta.get("title") or "校园活动")
    section_title = _plain_text(section.get("cn") or section.get("title") or "活动现场")
    detail = _plain_text(section.get("intro")) or _first_block_text(section)
    visual_style = _plain_text(
        style.get("cover_style") or "清爽、温暖、真实的校园纪实摄影与编辑插画风格",
        120,
    )
    return " ".join(
        [
            f"为微信公众号文章《{article_title}》的“{section_title}”章节生成一张正文横版插图。",
            f"章节内容：{detail}。" if detail else "",
            f"视觉风格：{visual_style}。",
            "画面比例 16:9，主体明确，构图自然，适合插入微信公众号正文。",
            "只表现当前章节已经明确的信息，不添加活动中没有出现的设备、人物身份、标语或数据。",
            "不要出现文字、标题、水印、品牌标志；避免可辨认的未成年人正脸特写。",
        ]
    ).strip()


def generate_ai_article_images(
    article: dict[str, Any],
    *,
    config: dict[str, Any],
    style: dict[str, Any],
    output_dir: Path,
    max_images: int = 3,
    generate_func: Callable[..., dict[str, str]] = generate_image,
) -> tuple[list[dict[str, Any]], list[str]]:
    image_config = config.get("image") if isinstance(config.get("image"), dict) else {}
    api_key = str(image_config.get("api_key") or "").strip()
    if not api_key:
        raise ValueError("已选择 AI 生成插图，请先在设置中配置 AI 生图 API Key。")

    provider = str(image_config.get("provider") or "doubao").strip()
    model = str(image_config.get("model") or "").strip()
    base_url = str(image_config.get("base_url") or "").strip()
    selected = _spread_candidates(_candidate_sections(article), max(0, max_images))
    if not selected:
        return [], []

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, Any]] = []
    errors: list[str] = []
    for sequence, (section_index, section) in enumerate(selected, start=1):
        section_title = _plain_text(section.get("cn") or section.get("title") or f"章节{sequence}", 60)
        prompt = build_content_image_prompt(article, section, style=style)
        target = (output_dir / f"section-{sequence:02d}.png").resolve()
        try:
            result = generate_func(
                provider=provider,
                api_key=api_key,
                prompt=prompt,
                output_path=target,
                model=model,
                base_url=base_url,
            )
        except Exception as exc:
            errors.append(f"“{section_title}”插图生成失败：{exc}")
            continue
        image = {
            "url": str(target),
            "local_path": str(target),
            "caption": section_title,
            "prompt": prompt,
            "source": "ai",
            "provider": result.get("provider") or provider,
            "model": result.get("model") or model,
        }
        section["image"] = image
        generated.append({"section_index": section_index, **image})
    return generated, errors
