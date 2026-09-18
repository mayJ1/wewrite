---
name: wechat-mp-writer
description: |
  微信公众号文章全流程助手：写作 → 报刊级 HTML 排版 → 一键推送到微信草稿箱。
  内置 8 套精美 HTML 模板、5 种写作人格、范文风格库、反 AI 检测写作规范、
  学习用户改稿风格等能力。
  触发关键词：公众号、推文、微信文章、微信推文、草稿箱、微信排版、写公众号、
  写一篇、报刊风格、AI日报、财经周报、深度分析。
  不应被通用的"写文章"、blog、邮件、PPT、抖音/短视频触发——
  需要有公众号/微信等明确上下文。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebSearch
  - WebFetch
---

# WeChat MP Writer — 公众号文章全流程

从写作到排版到发布，一站式公众号文章制作。核心亮点：**8 套报刊级 HTML 模板 + 程序化渲染引擎**，输出效果远超 Markdown 转换器。

## 路径约定

本文档中 `{skill_dir}` 指本 SKILL.md 所在的目录。执行内置脚本时，优先定位 `SKILL.md` 所在目录，再从该目录拼绝对路径访问 `scripts/`、`templates/`、`references/`、`personas/`。

---

## 核心能力

| 能力 | 来源 | 说明 |
|------|------|------|
| 🎨 8 套报刊级 HTML 模板 | wechat-mp-writer | 渐变报头、编号卡片、双语分区标题、专业排版 |
| 🖼️ 程序化渲染引擎 | wechat-mp-writer | JSON → HTML，支持 7 种 block 类型 |
| 📝 5 种写作人格 | wewrite-main | 深夜好友/温暖编辑/行业观察者/犀利记者/冷峻分析师 |
| 📚 范文风格库 | wewrite-main | 自动提取风格指纹，写作时注入风格片段 |
| 🔍 反 AI 检测写作规范 | wewrite-main | 句长方差、词汇温度混搭、破句、情绪极性 |
| ✅ 硬约束校验 | wechat-mp-writer | 标题≤32字、摘要≤128字、HTML<1MB |
| 📤 推送到草稿箱 | wewrite-main | 内置微信 API（token管理+图片上传+创建草稿） |
| 📖 学习用户改稿 | wewrite-main | diff 分析 → 提取修改模式 → 自动进化 |

---

## 快速入口

优先用仓库自带脚本：

```bash
# 渲染 HTML
python3 {skill_dir}/scripts/render_article.py article.json -o build/article.html --check

# 单独校验
python3 {skill_dir}/scripts/validate_article.py article.json --html build/article.html

# 规划封面图和正文配图
python3 {skill_dir}/scripts/plan_images.py article.json --write-article build/article.with-images.json

# 跑完整流水线（dry-run）
python3 {skill_dir}/scripts/run_pipeline.py article.json --output-dir build --dry-run

# 跑完整流水线（创建草稿）
python3 {skill_dir}/scripts/run_pipeline.py article.json --output-dir build --create-draft
```

---

## 主管道（Step 1-6）

### Step 1: 环境 + 风格加载

**1.1 检查 Python 依赖**（静默）：

```bash
python3 -c "import requests, yaml" 2>&1
```

不通过 → 提示 `pip install requests pyyaml`

**1.2 加载风格配置**：

检查 `{skill_dir}/style.yaml`：
- 存在 → 提取 `name`、`topics`、`tone`、`voice`、`writing_persona`、`blacklist`
- 不存在 → `读取: {skill_dir}/references/onboard.md`，引导用户创建 `style.yaml`

**1.3 加载 config.yaml**：

检查 `{skill_dir}/config.yaml`：
- 存在 → 提取 `wechat.appid`、`wechat.secret`
- 不存在 → 提示用户复制 `config.example.yaml` 为 `config.yaml` 并填入凭证。如不想发布，设 `skip_publish = true` 继续

---

### 素材目录导入模式

**触发**：用户说"素材在 {目录}" / "写一篇{主题}，素材在{目录}" / "{目录}里有素材"。

适用于学校活动报道等场景：活动方案文档(Word/PDF) + 活动照片 → 结构化素材数据。

```bash
python3 {skill_dir}/scripts/import_materials.py {目录} --output /tmp/wewrite_materials.json --pretty
```

**扫描内容**：
- 文档：`.docx` / `.pdf` / `.txt` / `.md`
- 图片：`.jpg` / `.jpeg` / `.png` / `.gif` / `.bmp` / `.webp`

**输出 JSON 结构**：
```json
{
  "documents": [{"filename": "...", "ext": ".docx", "text": "提取的文本", "char_count": 1200}],
  "photos": [{"filename": "...", "url": "微信CDN地址 或 本地路径", "local_only": false}],
  "stats": {"total_docs": 1, "total_photos": 15, "total_chars": 1200}
}
```

**处理逻辑**：
1. 扫描目录 → 分类文档和照片
2. 提取文档文本（Word 用 python-docx，PDF 用 pdfplumber/PyPDF2）
3. 上传照片到微信素材库获取 CDN URL（需要 `config.yaml` 中有微信凭证）
4. 输出结构化 JSON

**⚠️ 照片分类**（自动，基于文件夹结构）：

支持两种素材组织方式：

| 方式 | 目录结构 | 效果 |
|------|---------|------|
| **子文件夹分类**（推荐） | `素材/绘画/*.png` + `素材/书法/*.png` | 自动按文件夹名标注分类 |
| **平铺** | `素材/*.png`（所有图放根目录） | 不分类，全部图片统一处理 |

子文件夹分类示例：
```
demo-school/
├── 活动方案.docx          ← 文档（根目录）
├── 绘画/                  ← 子文件夹名 = 分类标签
│   ├── 作品01.png
│   └── 作品02.png
└── 书法/
    ├── 作品03.png
    └── 作品04.png
```

导入后的 JSON 自动带 `category` 字段：
```json
{
  "photos": [
    {"filename": "作品01.png", "category": "绘画", "url": "..."},
    {"filename": "作品03.png", "category": "书法", "url": "..."}
  ],
  "categories": ["绘画", "书法"]
}
```

Agent 根据 `category` 自动把照片放入文章中对应的 section（如"绘画篇"section 只放 category="绘画" 的图片）。

如果平铺（无子文件夹）且照片确实分类型 → Agent 会列出照片清单请你口头标注分类。

**数据注入**：
- 如果目录中有文档 → 提取的文本作为 **Step 2 的素材来源**（替代 WebSearch）
- 如果目录中有照片 → 写作时根据照片数量生成对应数量的照片标记 `<!-- 📷 照片位N：描述 -->`，标记描述从文档内容中提取
- 写作完成后，将照片 CDN URL 填入标记：`![描述](微信CDN_URL)`
- 照片多于标记 → 文末追加「更多照片」段落
- 标记多于照片 → 保留未填充的标记（HTML 注释，不影响发布）

**降级**：
- `python-docx` 未安装 → 提示 `pip install python-docx`，或请用户将 Word 另存为 .txt
- `pdfplumber` 未安装 → 提示 `pip install pdfplumber`，或请用户将 PDF 另存为 .txt
- 目录无文档 → 正常走 Step 2 选题 + WebSearch 素材，仅用目录中的照片
- 目录无照片 → 仅用文档写文章，跳过照片插入
- 微信凭证缺失 → 照片保留本地路径，发布时由 publisher 上传

---

### Step 2: 选题 + 素材

**2.1 选题**：

```
读取: {skill_dir}/references/frameworks.md  （11套框架）
```

- 如果用户已指定选题 → 直接用
- 如果用户未指定 → WebSearch 抓热点，生成 5-8 个选题供选择

**2.2 素材采集**：

- 用户指定数据源 → 用 `scripts/collect_sources.py` 归并
- 未指定 → WebSearch 采集 5-8 条真实素材（具名来源+具体数据）

**降级**：WebSearch 不可用 → 用 LLM 训练数据中可验证的公开信息

---

### Step 3: 写作

**3.0 加载写作偏好**（优先级最高）：

```
读取: {skill_dir}/playbook.md（如果存在）
```

playbook.md 是从用户草稿箱编辑中学习到的个性化规则。**优先级：playbook > persona > writing-guide**。

**3.1 加载写作人格**：

```
读取: {skill_dir}/personas/{writing_persona}.yaml
默认: midnight-friend（深夜好友）
```

5 种人格：

| 人格 | 适合 | 一句话描述 |
|------|------|----------|
| `midnight-friend` | 个人号/自媒体 | 像深夜给朋友发微信，极度口语化 |
| `warm-editor` | 生活/文化/情感 | 故事驱动，温暖共鸣 |
| `industry-observer` | 行业媒体/分析 | 克制的专业分析，偶尔锐利 |
| `sharp-journalist` | 新闻/评论 | 短句利落，观点鲜明 |
| `cold-analyst` | 财经/投研 | 严谨数据，专业措辞 |

**3.2 加载范文风格**（有范文库时）：

```
读取: {skill_dir}/references/exemplars/index.yaml
```

按文章框架类型匹配范文（tech-opinion/story-emotional/list-practical/hot-take/general），取 top 3，提取片段注入写作 prompt。

**Fallback**：范文库为空 → 跳过，仅用 persona + writing-guide

**3.3 写作规范**：

```
读取: {skill_dir}/references/writing-guide.md
```

核心规则：
- 句长方差 ≥ 15 字
- 词汇温度：冷/温/热/野 四带混搭
- 禁用 AI 惯用词（首先/其次/总而言之/值得注意的是/综上所述）
- 每 500 字至少 1 个单句段落
- 负面情绪 ≥ 20%
- 每个 H2 至少 1 条真实素材锚定

**3.4 输出 article JSON**：

按以下最小结构生成：

```json
{
  "template": "daily-intelligence",
  "meta": {
    "title": "标题≤32字",
    "digest": "摘要≤128字",
    "author": "署名",
    "date": "2026-06-02"
  },
  "headline": {
    "title": "头条标题",
    "body": ["第一段", "第二段"],
    "source": "来源"
  },
  "sections": [
    {
      "en": "BRIEFING",
      "cn": "要闻",
      "blocks": [
        {
          "type": "card",
          "style": "highlight",
          "number": 1,
          "title": "卡片标题",
          "body": ["正文段落"],
          "source": "来源"
        }
      ]
    }
  ],
  "cta": "你最关注哪一点？欢迎留言。"
}
```

支持的 `template`：`daily-intelligence` / `weekly-financial` / `deep-analysis` / `breaking-watch` / `product-release` / `industry-radar` / `studio-brief` / `neo-brutalism`

支持的 `block.type`：`card` / `opinion` / `week-ahead` / `image` / `quote` / `takeaways` / `paragraph`

保存到 `{skill_dir}/output/{date}-{slug}.json`

**3.5 快速自检**（写完后立即执行）：

- [ ] 标题 ≤ 32 字
- [ ] 摘要 ≤ 128 字
- [ ] 禁用词扫描（writing-guide.md 2.1）
- [ ] 每个 section 有至少 1 个 block
- [ ] 头条 headline 有 title + body

---

### Step 4: 渲染 + 校验

```bash
python3 {skill_dir}/scripts/run_pipeline.py {article_json} --output-dir {skill_dir}/output --dry-run
```

这会执行：配图规划 → HTML 渲染 → 硬约束校验

如果校验不通过 → 根据错误信息修复 article JSON → 重新渲染

---

### Step 5: 推送到草稿箱

**如果 `skip_publish = true`** → 跳到 Step 6，只保存本地 HTML。

```bash
python3 {skill_dir}/scripts/run_pipeline.py {article_json} --output-dir {skill_dir}/output --create-draft
```

流程：获取 access_token → 上传封面图 → 上传正文配图 → 创建草稿

**如果返回 `48001`** → 通知用户改为手动去草稿箱发布。

---

### Step 6: 收尾

**6.1 写入历史**：

在 `{skill_dir}/history.yaml` 追加记录：

```yaml
- date: "{日期}"
  title: "{标题}"
  template: "{模板名}"
  persona: "{人格名}"
  draft_media_id: "{id}"  # 降级时 null
  output_file: "{output 文件路径}"
```

**6.2 回复用户**：

- 最终标题 + 摘要 + 模板名 + draft_media_id
- 编辑建议："文章已推送到草稿箱。你可以在微信后台修改，改完后说「学习我的修改」，我能学到你的风格。"

**6.3 后续操作**：

| 用户说 | 动作 |
|--------|------|
| 润色/缩写/扩写/换语气 | 编辑 article JSON，重新渲染 |
| 换一个模板 | 改 `template` 字段，重新渲染 |
| 换写作人格 | 改 `style.yaml` 的 `writing_persona`，重新写作 |
| 学习我的修改 | `读取: {skill_dir}/references/learn-edits.md` → 运行 `learn_edits.py` |
| 导入范文 | `python3 {skill_dir}/scripts/extract_exemplar.py article.md` |
| 查看范文库 | `python3 {skill_dir}/scripts/extract_exemplar.py --list` |
| 重新设置风格 | `读取: {skill_dir}/references/onboard.md` |
| 预览模板 | `读取: {skill_dir}/templates/` 下的 HTML 文件 |

---

## 8 套模板速览

| 模板 | 配色 | 适用场景 |
|------|------|---------|
| `daily-intelligence` | 深海蓝 + 信号红 | AI 日报、每日资讯精选 |
| `weekly-financial` | 深红黑渐变 | 财经周报、市场回顾 |
| `deep-analysis` | 深蓝紫渐变 | 单主题深度分析、行业复盘 |
| `breaking-watch` | 紧凑新闻风 | 快讯追踪、突发新闻 |
| `product-release` | 产品发布风 | 新品发布、功能介绍 |
| `industry-radar` | 行业雷达风 | 行业趋势扫描 |
| `studio-brief` | 暖白 + 陶土色 | 极简编辑风、生活方式 |
| `neo-brutalism` | 高对比粗边框 | 个性表达、创意内容 |

## 7 种 Block 类型

| type | 说明 | 特殊字段 |
|------|------|---------|
| `card` | 编号卡片（支持 `style: highlight` 红底重点） | `number`, `title`, `body`, `source` |
| `opinion` | 编辑观点卡（自动加"编辑观点："前缀） | `title`, `body` |
| `week-ahead` | 周前瞻日历卡 | `days: [{label, events}]` |
| `image` | 配图 | `url`, `caption` |
| `quote` | 引述块（左侧红竖线） | `text`, `attribution` |
| `takeaways` | 核心结论框（暖灰底圆角） | `title`, `items: []` |
| `paragraph` | 纯段落 | `text` 或 `body` |

## 排版核心规范

| 项目 | 设置 |
|------|------|
| 字体 | -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC' |
| 正文字号 | 14-15px |
| 正文颜色 | #555 或 #3f3f3f |
| 标题颜色 | #1a1a2e |
| 行高 | 1.9-2.0 |
| 强调数据 | `<strong style="color: #e94560;">数据</strong>` |

## 标题公式

参考 `{skill_dir}/references/title-formulas.md`：
- 关键词法：带核心关键词，利于搜索推荐
- 反差法：制造认知冲突
- 问号式：激发好奇心
- 数据法：用具体数字吸引眼球
- 禁止"震惊体"，会被判标题党限流

## 发布时段

- 最佳：17:00-23:00
- 通勤：8:00-9:00
- 午休：12:00-13:00
- 分享朋友圈最佳：21:00后

## 错误处理

| 步骤 | 降级 |
|------|------|
| Python 依赖缺失 | 引导安装 |
| config.yaml 不存在 | 提示复制 example，设 `skip_publish = true` |
| 微信凭证缺失 | 设 `skip_publish = true`，仅本地渲染 |
| style.yaml 不存在 | 引导 onboard |
| 范文库为空 | 跳过范文注入，仅用 persona + writing-guide |
| 素材采集失败 | LLM 训练数据中的可验证公开信息 |
| 渲染/校验失败 | 根据错误信息修复 JSON，重试 |
| 创建草稿失败 | 输出本地 HTML，提示手动处理 |
