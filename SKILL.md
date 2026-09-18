---
name: wechat-mp-writer
description: "End-to-end WeChat Official Account article workflow for drafting, editing, rendering, validating, importing materials, planning images, learning user edits, and creating WeChat drafts. Use when the user asks for 微信公众号, 公众号推文, 微信文章, 微信推文, 微信排版, 草稿箱, 校园活动报道, 素材目录写稿, 报刊风格 HTML, AI日报, 财经周报, 深度分析, or when continuing work migrated from the prior Claude Code wechat-mp-writer skill. Do not use for generic essays, blog posts, email, PPT, or short-video scripts unless WeChat/公众号 context is explicit."
---

# WeChat MP Writer

Use this skill to continue the user's WeChat Official Account workflow with no platform break from the previous Claude Code setup. The migrated skill keeps private state in place: `config.yaml`, `history.yaml`, `style.yaml`, `playbook.md`, `lessons/`, `references/exemplars/`, `output/`, templates, personas, and scripts.

## First Steps

1. Locate the skill directory from this `SKILL.md`; refer to it as `skill_dir`.
2. Load private writing state before drafting:
   - `playbook.md` first; it overrides all other writing rules.
   - `style.yaml` for account identity, default template, persona, audience, voice, and author.
   - `personas/{writing_persona}.yaml` for persona details.
   - `references/writing-guide.md` only when writing or revising long-form content.
   - `history.yaml` when avoiding repeated structure, title formulas, or recent stylistic patterns.
3. Treat all credentials and historical IDs as private local data. Use them for the workflow when needed, but do not print secrets in responses.
4. Prefer the bundled Python scripts over reimplementing rendering, validation, image planning, material import, WeChat API calls, or edit learning.

On Windows, use `python` if `python3` is not available.

## Core Workflow

For a new article:

1. Gather inputs.
   - If the user says materials are in a directory, run `scripts/import_materials.py <directory> --output <json> --pretty`.
   - If no local materials are provided and current facts are needed, browse/search for sources and cite them in the article data.
2. Draft article JSON under `output/{date}-{slug}.json`.
   - Use `style.yaml` defaults unless the user requests a different template or voice.
   - Use the JSON schema described in `references/claude-skill-original.md` only if the exact shape is needed.
3. Run the pipeline in dry-run mode:
   - `python scripts/run_pipeline.py output/{file}.json --output-dir output --dry-run`
4. Fix validation errors in the JSON and rerun until it passes.
5. If the user wants a WeChat draft, run:
   - `python scripts/run_pipeline.py output/{file}.json --output-dir output --create-draft`
6. Append a concise record to `history.yaml` with date, title, template, persona, draft media ID when available, output file, and image count when known.

## Writing Rules

For the current account, the strongest rules are in `playbook.md`. Apply these especially:

- Do not fabricate student stories, quotations, authority statements, or numeric details. If a source document does not support it, write a generalized description.
- For campus reporting, keep the tone warm but restrained; avoid over-literary emotion.
- Do not create a standalone Lead Story block in the body. Put introductory text into the first section intro.
- Keep section titles simple, such as `绘画篇` or `活动回顾`; let the intro expand the meaning.
- Do not insert long text between images in a photo group. Put explanation before or after the group.
- Remove template brand labels, redundant date/source/author rows, and visible boilerplate unless the user explicitly wants them.
- Put signature lines after the CTA, centered, using the format recorded in `playbook.md`.

When user-provided materials are sparse, be honest and restrained. Ask only if a missing fact is necessary; otherwise write around it without inventing.

## Article JSON Essentials

Minimum structure:

```json
{
  "template": "studio-brief",
  "meta": {
    "title": "标题≤32字",
    "digest": "摘要≤128字",
    "author": "署名",
    "date": "YYYY-MM-DD"
  },
  "headline": {
    "title": "头条标题",
    "body": ["引导段落"]
  },
  "sections": [
    {
      "en": "SECTION",
      "cn": "分区",
      "intro": "可选引导语",
      "blocks": [
        {
          "type": "paragraph",
          "text": "正文段落"
        }
      ]
    }
  ],
  "cta": "结尾互动或署名区"
}
```

Supported templates: `daily-intelligence`, `weekly-financial`, `deep-analysis`, `breaking-watch`, `product-release`, `industry-radar`, `studio-brief`, `neo-brutalism`.

Supported block types: `card`, `opinion`, `week-ahead`, `image`, `quote`, `takeaways`, `paragraph`.

## Script Map

- `scripts/import_materials.py`: scan a materials directory, extract `.docx/.pdf/.txt/.md`, classify image folders, optionally upload images to WeChat.
- `scripts/run_pipeline.py`: plan images, upload images when not dry-run, render HTML, validate constraints, optionally create WeChat draft.
- `scripts/render_article.py`: render article JSON to HTML.
- `scripts/validate_article.py`: validate article JSON and rendered HTML.
- `scripts/plan_images.py`: add cover/body image prompts and local paths.
- `scripts/learn_edits.py`: diff AI draft versus human-edited final, save lessons, summarize high-confidence editing patterns.
- `scripts/extract_exemplar.py`: add edited finals to the exemplar library.
- `scripts/publisher.py` and `scripts/wechat_api.py`: WeChat API helpers.

## Important References

- `playbook.md`: current highest-priority user editing preferences.
- `style.yaml`: account identity and defaults.
- `references/writing-guide.md`: anti-generic writing rules for broader editorial content.
- `references/frameworks.md`: article framing options.
- `references/title-formulas.md`: title patterns.
- `references/image-prompts.md`: visual prompt guidance.
- `references/exemplars/index.yaml`: available exemplar library.
- `references/claude-skill-original.md`: archived original Claude Code skill with the full previous workflow.

## Validation

Always run at least a dry-run render/validation before reporting that an article artifact is ready. Relay the created local HTML path and draft media ID if a draft was created. If validation or draft creation fails, fix what can be fixed locally and clearly report any remaining blocker.
