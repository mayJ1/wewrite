const setupSteps = [
  {
    id: "appid",
    title: "填写公众号 AppID",
    hint: "在微信公众平台：设置与开发 → 基本配置，可以找到 AppID。",
    placeholder: "例如 wx1234567890abcdef",
    required: true,
    type: "text",
  },
  {
    id: "secret",
    title: "填写公众号 AppSecret",
    hint: "AppSecret 只保存在本机 config.yaml。页面不会再把它明文显示出来。",
    placeholder: "粘贴 AppSecret",
    required: true,
    type: "password",
  },
  {
    id: "ai_api",
    title: "填写 AI 写稿 API Key",
    hint: "推荐使用 DeepSeek 开放平台。这里会按 deepseek-v4-flash 自动配置，后续自动写稿会用它生成文章 JSON。",
    placeholder: "粘贴 DeepSeek API Key",
    required: true,
    type: "password",
  },
  {
    id: "image_api",
    title: "填写 AI 生图 API",
    hint: "用于后续自动生成封面图。现在没有也没关系，可以直接跳过。",
    placeholder: "粘贴 API Key，可跳过",
    required: false,
    type: "password",
  },
  {
    id: "ip_whitelist",
    title: "设置 API IP 白名单",
    hint: "这一步需要你在微信公众平台手动设置。本地工具无法代替你操作。",
    required: false,
    manual: true,
  },
];

const articleSteps = [
  {
    id: "articleType",
    title: "选择文章类型",
    hint: "文章类型会影响结构、语气和素材重点。校园活动报道适合大多数日常推文。",
    options: [
      ["campus_activity", "校园活动报道", "推荐。适合公开课、健康讲座、节日活动、主题教育等。"],
      ["weekly_review", "工作周报/阶段回顾", "适合一周工作回顾、项目阶段总结、多板块复盘。"],
      ["notice", "通知公告", "适合家校通知、报名提醒、活动安排。"],
      ["profile", "师生风采", "适合教师宣传、学生作品、班级亮点。"],
      ["custom", "自定义", "保留更多自由度，后续由素材和主题决定结构。"],
    ],
  },
  {
    id: "persona",
    title: "选择写作人格",
    hint: "先用中文理解，不要求用户知道内部 persona 名称。",
    options: [
      ["warm-editor", "温暖编辑", "推荐。真实、克制、有温度，适合校园公众号。"],
      ["official-steady", "稳重公文", "更正式，适合党政活动、会议、通知类内容。"],
      ["campus-lively", "活泼校园", "更轻快，适合节日活动、学生作品展示。"],
      ["brief-notice", "简洁通知", "少抒情、重信息，适合通知公告。"],
      ["deep-report", "深度报道", "更完整，适合专题报道和阶段性成果。"],
    ],
  },
  {
    id: "exemplarMode",
    title: "参考范文风格",
    hint: "范文只作为写法参考，不会照抄内容。推荐先使用默认范文库，让文章更接近已沉淀的账号风格。",
    options: [
      ["default", "使用默认范文库", "推荐。参考风格库里已保存的优秀稿件，学习结构、节奏和收束方式。"],
      ["none", "不参考范文", "只根据素材、写作要求和基础规则生成，适合临时换一种写法时使用。"],
    ],
  },
  {
    id: "template",
    title: "选择模板",
    hint: "选择适合本篇文章的排版模板，可先预览再确认。",
    options: [
      ["studio-brief", "校园简报", "推荐。清爽克制，适合多数校园报道。"],
      ["neo-brutalism", "醒目活动风", "视觉更强，适合主题鲜明的活动或专题。"],
      ["campus-party", "党政活动风", "红金暖色，适合升旗、思政、党团队活动。"],
      ["daily-intelligence", "日报资讯", "信息密度较高，适合多条资讯汇总。"],
      ["weekly-financial", "周报深读", "报刊感版式，适合周报、复盘和长文。"],
      ["deep-analysis", "深度分析", "适合专题解读、观点分析和深度文章。"],
      ["breaking-watch", "快讯观察", "适合即时动态、事件跟进和简短说明。"],
      ["product-release", "成果发布", "适合项目、课程或阶段成果发布。"],
      ["industry-radar", "行业雷达", "适合趋势简报、行业观察和资料整理。"],
    ],
  },
  {
    id: "imageMode",
    title: "选择图片方式",
    hint: "后续导入素材时，会根据这里的选择决定是否使用照片和 AI 封面。",
    options: [
      ["photos", "使用素材照片", "推荐。用活动现场照片作为正文图片。"],
      ["ai_generated", "AI 生成正文插图", "根据文章章节自动生成并插入正文配图。"],
      ["none", "暂不使用图片", "先生成纯文字稿，之后再补图。"],
    ],
  },
];

const defaultArticleOptions = {
  articleType: "campus_activity",
  persona: "warm-editor",
  exemplarMode: "default",
  exemplarFile: "auto",
  template: "studio-brief",
  imageMode: "photos",
  rewriteEnabled: false,
};

const labels = Object.fromEntries(
  articleSteps.flatMap((step) => step.options.map(([value, label]) => [value, label]))
);

const templatePreviews = {
  "studio-brief": "/static/template-previews/studio-brief.png",
  "neo-brutalism": "/static/template-previews/neo-brutalism.png",
  "campus-party": "/static/template-previews/campus-party.png",
  "daily-intelligence": "/static/template-previews/daily-intelligence.png",
  "weekly-financial": "/static/template-previews/weekly-financial.png",
  "deep-analysis": "/static/template-previews/deep-analysis.png",
  "breaking-watch": "/static/template-previews/breaking-watch.png",
  "product-release": "/static/template-previews/product-release.png",
  "industry-radar": "/static/template-previews/industry-radar.png",
};

const isSettingsEmbed = new URLSearchParams(window.location.search).get("settings") === "1";
const restoredArticleSession = loadCurrentArticleSession();

const state = {
  phase: "setup",
  current: 0,
  config: null,
  style: null,
  publicIp: "",
  publicIpError: "",
  articleOptions: { ...loadArticleOptions(), ...(restoredArticleSession?.articleOptions || {}) },
  exemplars: [],
  exemplarsLoaded: false,
  previewTemplate: "",
  selectedFiles: [],
  materials: restoredArticleSession?.materials || null,
  writingRequest: restoredArticleSession?.writingRequest || loadWritingRequest(),
  generatedDraft: restoredArticleSession?.generatedDraft || null,
  revisionRequest: restoredArticleSession?.revisionRequest || "",
  generationTimer: null,
  sessionSaveTimer: null,
  useMaterials: Boolean(restoredArticleSession?.useMaterials && restoredArticleSession?.materials),
  articleWorkspacePhase: restoredArticleSession?.phase || "",
  firstVisit: localStorage.getItem("wewriteOnboardingComplete") !== "true",
  draftHistory: [],
  editLearning: { rules: [], sessions: [] },
};

const els = {
  mainTitle: document.querySelector("#mainTitle"),
  mainSubtitle: document.querySelector("#mainSubtitle"),
  panel: document.querySelector("#questionPanel"),
  backButton: document.querySelector("#backButton"),
  skipButton: document.querySelector("#skipButton"),
  nextButton: document.querySelector("#nextButton"),
  message: document.querySelector("#message"),
  progressBar: document.querySelector("#progressBar"),
  appidStatus: document.querySelector("#appidStatus"),
  secretStatus: document.querySelector("#secretStatus"),
  aiStatus: document.querySelector("#aiStatus"),
  imageStatus: document.querySelector("#imageStatus"),
  navButtons: document.querySelectorAll(".nav-button"),
  settingsButton: document.querySelector("#settingsButton"),
  newArticleButton: document.querySelector("#newArticleButton"),
  articleTypeStatus: document.querySelector("#articleTypeStatus"),
  personaStatus: document.querySelector("#personaStatus"),
  exemplarStatus: document.querySelector("#exemplarStatus"),
  templateStatus: document.querySelector("#templateStatus"),
  imageModeStatus: document.querySelector("#imageModeStatus"),
};

function loadCurrentArticleSession() {
  try {
    const data = JSON.parse(localStorage.getItem("wewriteCurrentArticle") || "null");
    return data && typeof data === "object" ? data : null;
  } catch {
    return null;
  }
}

function saveCurrentArticleSession() {
  if (isSettingsEmbed || state.firstVisit) return;
  const phase = state.articleWorkspacePhase || (
    ["articleForm", "materials", "requirements", "draftReady", "generated"].includes(state.phase)
      ? state.phase
      : ""
  );
  if (!phase) return;
  const payload = {
    version: 1,
    savedAt: new Date().toISOString(),
    phase,
    articleOptions: state.articleOptions,
    useMaterials: state.useMaterials,
    materials: state.useMaterials ? state.materials : null,
    writingRequest: state.writingRequest,
    generatedDraft: state.generatedDraft,
    revisionRequest: state.revisionRequest,
  };
  try {
    localStorage.setItem("wewriteCurrentArticle", JSON.stringify(payload));
  } catch {
    const compact = {
      ...payload,
      materials: null,
      useMaterials: false,
      generatedDraft: state.generatedDraft
        ? {
            ...state.generatedDraft,
            html: "",
          }
        : null,
    };
    try {
      localStorage.setItem("wewriteCurrentArticle", JSON.stringify(compact));
    } catch {
      // 草稿历史仍可恢复已生成文章，不让存储空间不足打断当前操作。
    }
  }
}

function scheduleCurrentArticleSessionSave() {
  if (state.sessionSaveTimer) window.clearTimeout(state.sessionSaveTimer);
  state.sessionSaveTimer = window.setTimeout(() => {
    state.sessionSaveTimer = null;
    saveCurrentArticleSession();
  }, 250);
}

function clearCurrentArticleSession() {
  if (state.sessionSaveTimer) window.clearTimeout(state.sessionSaveTimer);
  state.sessionSaveTimer = null;
  localStorage.removeItem("wewriteCurrentArticle");
}

function loadArticleOptions() {
  try {
    return { ...defaultArticleOptions, ...JSON.parse(localStorage.getItem("draftOptions") || "{}") };
  } catch {
    return { ...defaultArticleOptions };
  }
}

async function ensureExemplarsLoaded() {
  if (state.exemplarsLoaded) return state.exemplars;
  const data = await fetchJson("/api/exemplars");
  state.exemplars = Array.isArray(data.exemplars) ? data.exemplars : [];
  state.exemplarsLoaded = true;
  return state.exemplars;
}

function saveArticleOptions() {
  localStorage.setItem("draftOptions", JSON.stringify(state.articleOptions));
}

function loadWritingRequest() {
  try {
    return JSON.parse(localStorage.getItem("writingRequest") || "{}");
  } catch {
    return {};
  }
}

function saveWritingRequest() {
  localStorage.setItem("writingRequest", JSON.stringify(state.writingRequest));
}

function clearWritingRequest() {
  state.writingRequest = {};
  localStorage.removeItem("writingRequest");
}

function getMaterialsSignature(materials) {
  const docs = Array.isArray(materials?.documents) ? materials.documents : [];
  const photos = Array.isArray(materials?.photos) ? materials.photos : [];
  return JSON.stringify({
    docs: docs.map((doc) => [doc.filename || "", doc.char_count || 0, Boolean(doc.error)]),
    photos: photos.map((photo) => [photo.filename || "", photo.category || ""]),
  });
}

function inferWritingRequestFromMaterials(materials) {
  const docs = Array.isArray(materials?.documents) ? materials.documents : [];
  const text = docs
    .map((doc) => [doc.filename || "", doc.text || ""].join("\n"))
    .join("\n\n")
    .slice(0, 12000);
  const filenames = docs.map((doc) => doc.filename || "").join(" ");
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  return {
    topic: inferTopic(lines, filenames),
    activity_time: inferActivityTime(text),
    activity_location: inferActivityLocation(text),
  };
}

function inferTopic(lines, filenames) {
  const candidates = [
    ...lines.slice(0, 8),
    filenames.replace(/\.(docx|pdf|txt|md)$/gi, ""),
  ]
    .map((item) => cleanTopic(item))
    .filter((item) => item.length >= 4 && item.length <= 36);
  const best = candidates.find((item) => /活动|讲座|课堂|培训|会议|仪式|展|比赛|演练|教育|健康|安全|主题/.test(item)) || candidates[0] || "";
  if (!best) return "";
  if (/报道|推文|简讯|新闻稿/.test(best)) return best;
  if (/活动|讲座|课堂|培训|会议|仪式|展|比赛|演练|教育/.test(best)) return `${best}报道`;
  return best;
}

function cleanTopic(value) {
  return String(value || "")
    .replace(/^\uFEFF/, "")
    .replace(/\s+/g, "")
    .replace(/\.(docx|pdf|txt|md)$/gi, "")
    .replace(/^[一二三四五六七八九十\d]+[、.．]/, "")
    .replace(/^(关于|开展|举行|举办|示例学校|学校)/, "")
    .replace(/[：:][\s\S]*$/, "")
    .replace(/(方案|通知|安排|议程|记录|总结|材料|稿件)$/g, "")
    .slice(0, 40);
}

function inferActivityTime(text) {
  const patterns = [
    /(?:活动时间|时间|日期)[:：\s]*([0-9]{4}年\s*[0-9]{1,2}月\s*[0-9]{1,2}日(?:\s*(?:上午|下午|晚上)?\s*[0-9:：点分半]*)?)/,
    /(?:活动时间|时间|日期)[:：\s]*([0-9]{1,2}月\s*[0-9]{1,2}日(?:\s*(?:上午|下午|晚上)?\s*[0-9:：点分半]*)?)/,
    /([0-9]{4}[-/.年][0-9]{1,2}[-/.月][0-9]{1,2}日?)/,
    /([0-9]{1,2}月\s*[0-9]{1,2}日(?:\s*(?:上午|下午|晚上)?\s*[0-9:：点分半]*)?)/,
  ];
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return normalizeTextValue(match[1]);
  }
  return "";
}

function inferActivityLocation(text) {
  const patterns = [
    /(?:活动地点|地点|会议地点|上课地点)[:：\s]*([^\n\r，。；;]{2,30})/,
    /(?:在|于)([^，。；;\n\r]{2,30})(?:开展|举行|举办|进行|召开)/,
  ];
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return normalizeTextValue(match[1]);
  }
  return "";
}

function normalizeTextValue(value) {
  return String(value || "")
    .replace(/\s+/g, "")
    .replace(/[，。；;、]+$/g, "")
    .trim();
}

function mergeInferredWritingRequest() {
  const inferred = inferWritingRequestFromMaterials(state.materials);
  const current = state.writingRequest || {};
  const materialSignature = getMaterialsSignature(state.materials);
  const sameMaterials = current.material_signature && current.material_signature === materialSignature;
  const merged = sameMaterials ? { ...current } : { material_signature: materialSignature };
  let changed = false;
  for (const key of ["topic", "activity_time", "activity_location"]) {
    if (!merged[key] && inferred[key]) {
      merged[key] = inferred[key];
      changed = true;
    }
  }
  if (changed) {
    state.writingRequest = merged;
    saveWritingRequest();
  }
  return { inferred, changed };
}

function setMessage(text, type = "") {
  els.message.textContent = text;
  els.message.className = `message ${type}`.trim();
}

class ApiRequestError extends Error {
  constructor(payload, status) {
    const fallback = status ? `请求失败：${status}` : "请求失败。";
    super(payload?.error || payload?.message || fallback);
    this.name = "ApiRequestError";
    this.status = status;
    this.payload = payload || {};
    Object.assign(this, this.payload);
  }
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (!response.ok) {
    throw new ApiRequestError(data, response.status);
  }
  return data;
}

function isSetupReady() {
  const cfg = state.config || {};
  return Boolean(cfg.wechat?.appid && cfg.wechat?.secret && cfg.ai?.api_key);
}

function updateStatus() {
  const cfg = state.config || {};
  els.appidStatus.classList.toggle("done", Boolean(cfg.wechat?.appid));
  els.secretStatus.classList.toggle("done", Boolean(cfg.wechat?.secret));
  els.aiStatus.classList.toggle("done", Boolean(cfg.ai?.api_key));
  els.imageStatus.classList.toggle("done", Boolean(cfg.image?.api_key));

  if (els.articleTypeStatus) els.articleTypeStatus.textContent = labels[state.articleOptions.articleType] || "未选择";
  if (els.personaStatus) els.personaStatus.textContent = labels[state.articleOptions.persona] || "未选择";
  els.exemplarStatus.textContent = getExemplarStatusLabel();
  els.templateStatus.textContent = labels[state.articleOptions.template] || "未选择";
  els.imageModeStatus.textContent = {
    photos: "选择已有图片",
    ai_generated: "AI 生成",
    ai_cover: "AI 生成",
    none: "不使用",
  }[state.articleOptions.imageMode] || "未选择";
}

function getExemplarStatusLabel() {
  if (state.articleOptions.exemplarMode === "none") return "不参考范文";
  if (!state.articleOptions.exemplarFile || state.articleOptions.exemplarFile === "auto") return "自动匹配";
  const item = state.exemplars.find((exemplar) => exemplar.file === state.articleOptions.exemplarFile);
  return item ? formatExemplarLabel(item) : "已选择范文";
}

function formatExemplarLabel(item) {
  const source = item.source ? `${item.source} · ` : "";
  return `${source}${item.file || "未命名范文"}`;
}

function setHeader(title, subtitle) {
  els.mainTitle.textContent = title;
  els.mainSubtitle.textContent = subtitle;
}

function updateNav(page) {
  els.navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.page === page);
  });
  els.settingsButton.classList.toggle("active", page === "settings");
}

function currentWorkspaceNavPage() {
  if (state.phase === "styles") return "styles";
  if (state.phase === "history") return "history";
  return "article";
}

function openSettingsOverlay() {
  if (isSettingsEmbed || document.querySelector(".settings-overlay-modal")) return;
  const modal = document.createElement("div");
  modal.className = "preview-modal settings-overlay-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-settings-close="true"></div>
    <section class="preview-dialog settings-overlay-dialog" role="dialog" aria-modal="true" aria-label="设置">
      <header class="settings-overlay-head">
        <strong>设置</strong>
        <button class="icon-close" type="button" data-settings-close="true" aria-label="关闭设置">&times;</button>
      </header>
      <iframe id="settingsFrame" src="/?settings=1" title="WeWrite 设置"></iframe>
    </section>
  `;
  document.body.appendChild(modal);
  els.settingsButton.classList.add("active");
  modal.addEventListener("click", (event) => {
    if (event.target.closest("[data-settings-close='true']")) closeSettingsOverlay();
  });
}

async function closeSettingsOverlay() {
  document.querySelector(".settings-overlay-modal")?.remove();
  els.settingsButton.classList.remove("active");
  try {
    const [configData, styleData] = await Promise.all([
      fetchJson("/api/config"),
      fetchJson("/api/style"),
    ]);
    state.config = configData.config;
    state.style = styleData.style;
    updateStatus();
  } catch (error) {
    setMessage(error.message, "error");
  }
  updateNav(currentWorkspaceNavPage());
}

async function loadPublicIp() {
  state.publicIp = "";
  state.publicIpError = "";
  const ipValue = document.querySelector("#ipValue");
  const ipHint = document.querySelector("#ipHint");
  if (ipValue) ipValue.textContent = "正在获取...";
  if (ipHint) ipHint.textContent = "正在检测这台电脑访问外网时使用的出口 IP。";
  try {
    const data = await fetchJson("/api/public-ip");
    state.publicIp = data.ip || "";
  } catch (error) {
    state.publicIpError = error.message;
  }
  if (state.phase === "settings") {
    renderSettingsPage();
  } else {
    renderSetupStep();
  }
}

function secretPlaceholder(hasValue, label) {
  return hasValue ? `已配置 ${label}，留空不修改` : `粘贴 ${label}`;
}

function listToText(value) {
  return Array.isArray(value) ? value.join("\n") : "";
}

const apiConfigItems = [
  { step: "appid", label: "公众号 AppID", inputId: "settingsAppid", placeholder: "粘贴 AppID", required: true, path: ["wechat", "appid"], type: "text" },
  { step: "secret", label: "公众号 AppSecret", inputId: "settingsSecret", placeholder: "粘贴 AppSecret", required: true, path: ["wechat", "secret"], type: "password" },
  { step: "ai_api", label: "AI 写稿 API Key", inputId: "settingsAiApi", placeholder: "粘贴 DeepSeek API Key", required: true, path: ["ai", "api_key"], type: "password" },
  { step: "image_api", label: "AI 生图 API Key", inputId: "settingsImageApi", placeholder: "粘贴生图 API Key", required: false, path: ["image", "api_key"], type: "password" },
];

const styleConfigItems = [
  { field: "name", label: "公众号名称", question: "你的公众号叫什么名字？", inputId: "styleName", placeholder: "例如：某某小学", required: true, type: "text" },
  { field: "full_name", label: "公众号全称", question: "公众号有没有更完整的机构名称？", inputId: "styleFullName", placeholder: "例如：某某县某某小学", required: false, type: "text" },
  { field: "industry", label: "行业/机构类型", question: "你属于什么行业或机构？", inputId: "styleIndustry", placeholder: "例如：学校、科技公司、社区机构", required: true, type: "text" },
  { field: "topics", label: "主要内容方向", question: "平时主要发布哪些内容？", inputId: "styleTopics", placeholder: "例如：校园活动报道、科普文章，一行一个", required: true, type: "textarea", rows: 4 },
  { field: "tone", label: "文章风格", question: "希望文章读起来是什么感觉？", inputId: "styleTone", placeholder: "例如：温暖真实、简洁自然，不过度抒情", required: true, type: "textarea", rows: 3 },
  { field: "target_audience", label: "目标读者", question: "这些文章主要写给谁看？", inputId: "styleAudience", placeholder: "例如：家长、教职工、关注学校的人", required: false, type: "text" },
  { field: "voice", label: "人称和语感", question: "更喜欢怎样的人称和说话方式？", inputId: "styleVoice", placeholder: "例如：第一人称复数，亲切得体", required: false, type: "text" },
  { field: "author", label: "署名", question: "文章默认使用什么署名？", inputId: "styleAuthor", placeholder: "例如：编辑部", required: false, type: "text" },
  { field: "writing_persona", label: "默认写作人格", question: "默认使用哪一种写作感觉？", inputId: "stylePersona", placeholder: "", required: false, type: "select", optionsStep: "persona" },
  { field: "template", label: "默认排版模板", question: "默认使用哪套排版模板？", inputId: "styleTemplate", placeholder: "", required: false, type: "select", optionsStep: "template" },
  { field: "cover_style", label: "封面风格偏好", question: "你喜欢什么样的封面画面？", inputId: "styleCover", placeholder: "例如：校园风光、温暖明亮的色调", required: false, type: "text" },
  { field: "blacklist_words", label: "禁忌词", question: "有哪些词尽量不要出现？", inputId: "styleBlacklistWords", placeholder: "一行一个，可留空", required: false, type: "textarea", rows: 3 },
  { field: "blacklist_topics", label: "禁忌话题", question: "有哪些话题不要涉及？", inputId: "styleBlacklistTopics", placeholder: "一行一个，可留空", required: false, type: "textarea", rows: 3 },
];

function hasConfigPath(path) {
  let value = state.config || {};
  for (const key of path) {
    value = value?.[key];
  }
  return Boolean(value);
}

function imageProviderLabel(provider = state.config?.image?.provider) {
  if (provider === "doubao") return "豆包";
  if (provider === "agnes") return "Agnes";
  return "未指定";
}

function getApiConfigLabel(item) {
  if (item.step === "image_api") {
    return `${item.label}（${imageProviderLabel()}）`;
  }
  return item.label;
}

function renderApiConfigRows() {
  return `
    <div class="config-status-list">
      ${apiConfigItems.map((item) => {
        const configured = hasConfigPath(item.path);
        return `
          <div class="config-status-row ${configured ? "done" : "missing"}">
            <div>
              <strong>${getApiConfigLabel(item)}</strong>
              <span>${configured ? "已配置" : item.required ? "未配置，必填" : "未配置，选填"}</span>
            </div>
            ${configured ? `
              <button class="mini ghost" type="button" data-config-edit="${item.step}">修改</button>
            ` : `
              <input id="${item.inputId}" type="${item.type}" autocomplete="off" placeholder="${item.placeholder}">
            `}
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function getStyleFieldValue(field) {
  const style = state.style || {};
  const blacklist = style.blacklist || {};
  if (field === "blacklist_words") return listToText(blacklist.words);
  if (field === "blacklist_topics") return listToText(blacklist.topics);
  const value = style[field];
  return Array.isArray(value) ? listToText(value) : String(value || "");
}

function isStyleItemConfigured(item) {
  return Boolean(getStyleFieldValue(item.field).trim());
}

function isStyleReady() {
  return styleConfigItems.every((item) => !item.required || isStyleItemConfigured(item));
}

function getStyleDisplayValue(item, value) {
  if (item.type === "select") {
    return labels[value] || value;
  }
  return String(value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .join(" / ");
}

function truncateDisplayValue(value, limit = 72) {
  const text = String(value || "").trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, limit).trim()}...`;
}

function renderStyleInput(item, value = "") {
  if (item.type === "textarea") {
    return `<textarea id="${item.inputId}" rows="${item.rows || 3}" placeholder="${item.placeholder}">${escapeHtml(value)}</textarea>`;
  }
  if (item.type === "select") {
    const step = articleSteps.find((entry) => entry.id === item.optionsStep);
    return `
      <select id="${item.inputId}">
        ${(step?.options || []).map(([optionValue, label]) => `
          <option value="${optionValue}" ${optionValue === value ? "selected" : ""}>${label}</option>
        `).join("")}
      </select>
    `;
  }
  return `<input id="${item.inputId}" type="${item.type}" autocomplete="off" value="${escapeAttr(value)}" placeholder="${item.placeholder}">`;
}

function renderStyleConfigRows() {
  return `
    <div class="config-status-list style-config-list questionnaire-list">
      ${styleConfigItems.map((item, index) => {
        const configured = isStyleItemConfigured(item);
        const value = getStyleFieldValue(item.field);
        const displayValue = getStyleDisplayValue(item, value);
        return `
          <div class="config-status-row questionnaire-row ${configured ? "done" : "missing"}">
            <div>
              <small>问题 ${String(index + 1).padStart(2, "0")}${item.required ? " · 必答" : " · 可选"}</small>
              <strong>${configured ? item.label : item.question}</strong>
              <span class="${configured ? "config-value" : ""}" title="${configured ? escapeAttr(displayValue) : ""}">${configured ? escapeHtml(truncateDisplayValue(displayValue)) : item.required ? "未配置，必填" : "未配置，选填"}</span>
            </div>
            ${configured ? `
              <button class="mini ghost" type="button" data-style-edit="${item.field}">修改</button>
            ` : renderStyleInput(item, value)}
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function renderSettingsPage() {
  state.phase = "settings";
  updateNav("settings");
  setHeader(
    state.firstVisit ? "欢迎使用 WeWrite" : "设置",
    state.firstVisit
      ? "先完成账号连接和风格问卷，之后就可以直接生成公众号文章。"
      : "集中配置公众号和 AI 接口。通常第一次使用配置一次，之后需要更换密钥时再回来。"
  );
  els.progressBar.style.width = "100%";
  els.backButton.disabled = true;
  els.skipButton.hidden = true;
  els.nextButton.hidden = false;
  els.nextButton.disabled = false;
  els.nextButton.textContent = state.firstVisit ? "完成设置，开始写文章" : "保存设置";
  const cfg = state.config || {};
  const style = state.style || {};
  const blacklist = style.blacklist || {};
  const ipMarkup = state.publicIp
    ? `<div id="ipValue" class="ip-value">${state.publicIp}</div>
       <p id="ipHint" class="ip-hint">把这个 IP 填到微信公众平台的 IP 白名单里。</p>`
    : `<div id="ipValue" class="ip-value muted">${state.publicIpError ? "获取失败" : "点击获取"}</div>
       <p id="ipHint" class="ip-hint">${state.publicIpError || "用于微信 API 的 IP 白名单设置。"}</p>`;
  els.panel.innerHTML = `
    ${state.firstVisit ? `
      <section class="onboarding-banner">
        <span>首次使用引导</span>
        <h2>先让 WeWrite 认识你的公众号</h2>
        <p>第一步连接公众号和 AI，第二步回答几个写作偏好问题。密钥只会保存在这台电脑上。</p>
        <ol>
          <li class="active">连接账号与 AI</li>
          <li>完成账号风格问卷</li>
          <li>开始生成第一篇文章</li>
        </ol>
      </section>
    ` : ""}
    <p class="step-count">账号与接口</p>
    <h2>接口配置</h2>
    <p class="hint">密钥只保存在本机 config.yaml。为安全起见，已经配置过的密钥不会在页面明文显示。</p>
    <div class="settings-form">
      <label>
        <span>公众号 AppID ${cfg.wechat?.appid ? "<em>已配置</em>" : "<strong>必填</strong>"}</span>
        <input id="settingsAppid" type="text" autocomplete="off" placeholder="${secretPlaceholder(cfg.wechat?.appid, "AppID")}">
      </label>
      <label>
        <span>公众号 AppSecret ${cfg.wechat?.secret ? "<em>已配置</em>" : "<strong>必填</strong>"}</span>
        <input id="settingsSecret" type="password" autocomplete="off" placeholder="${secretPlaceholder(cfg.wechat?.secret, "AppSecret")}">
      </label>
      <label>
        <span>AI 写稿 API Key ${cfg.ai?.api_key ? "<em>已配置</em>" : "<strong>必填</strong>"}</span>
        <input id="settingsAiApi" type="password" autocomplete="off" placeholder="${secretPlaceholder(cfg.ai?.api_key, "DeepSeek API Key")}">
      </label>
      <label>
        <span>AI 生图 API Key ${cfg.image?.api_key ? "<em>已配置</em>" : "<small>选填</small>"}</span>
        <input id="settingsImageApi" type="password" autocomplete="off" placeholder="${secretPlaceholder(cfg.image?.api_key, "生图 API Key")}">
      </label>
    </div>
    <div class="settings-section">
      <p class="step-count">公众号风格</p>
      <h2>用一组小问题认识你的账号</h2>
      <p class="hint">不用研究专业配置，按平时说话的方式回答即可。以后自动写稿会沿用这些偏好。</p>
      <div class="settings-form">
        <label>
          <span>公众号名称 <strong>必填</strong></span>
          <input id="styleName" type="text" value="${escapeAttr(style.name || "")}" placeholder="例如：某某小学">
        </label>
        <label>
          <span>公众号全称</span>
          <input id="styleFullName" type="text" value="${escapeAttr(style.full_name || "")}" placeholder="例如：某某县某某小学">
        </label>
        <label>
          <span>行业/机构类型 <strong>必填</strong></span>
          <input id="styleIndustry" type="text" value="${escapeAttr(style.industry || "")}" placeholder="例如：教育、科技、财经、生活方式">
        </label>
        <label>
          <span>主要内容方向 <strong>必填</strong></span>
          <textarea id="styleTopics" rows="4" placeholder="一行一个，例如：校园活动报道">${escapeHtml(listToText(style.topics))}</textarea>
        </label>
        <label>
          <span>希望文章是什么风格 <strong>必填</strong></span>
          <textarea id="styleTone" rows="3" placeholder="例如：温暖但不失正式，有温度的校园报道">${escapeHtml(style.tone || "")}</textarea>
        </label>
        <label>
          <span>目标读者</span>
          <input id="styleAudience" type="text" value="${escapeAttr(style.target_audience || "")}" placeholder="例如：家长、教职工、关注学校的社会人士">
        </label>
        <label>
          <span>人称和语感</span>
          <input id="styleVoice" type="text" value="${escapeAttr(style.voice || "")}" placeholder="例如：第一人称复数，温暖得体">
        </label>
        <label>
          <span>署名</span>
          <input id="styleAuthor" type="text" value="${escapeAttr(style.author || "")}" placeholder="例如：编辑部">
        </label>
        <label>
          <span>默认写作人格</span>
          <select id="stylePersona">
            ${articleSteps.find((step) => step.id === "persona").options.map(([value, label]) => `
              <option value="${value}" ${value === (style.writing_persona || "warm-editor") ? "selected" : ""}>${label}</option>
            `).join("")}
          </select>
        </label>
        <label>
          <span>默认排版模板</span>
          <select id="styleTemplate">
            ${articleSteps.find((step) => step.id === "template").options.map(([value, label]) => `
              <option value="${value}" ${value === (style.template || "studio-brief") ? "selected" : ""}>${label}</option>
            `).join("")}
          </select>
        </label>
        <label>
          <span>封面风格偏好</span>
          <input id="styleCover" type="text" value="${escapeAttr(style.cover_style || "")}" placeholder="例如：校园风光、温暖明亮的色调">
        </label>
        <label>
          <span>参考账号</span>
          <textarea id="styleReferences" rows="3" placeholder="一行一个，可留空">${escapeHtml(listToText(style.reference_accounts))}</textarea>
        </label>
        <label>
          <span>禁忌词</span>
          <textarea id="styleBlacklistWords" rows="3" placeholder="一行一个，可留空">${escapeHtml(listToText(blacklist.words))}</textarea>
        </label>
        <label>
          <span>禁忌话题</span>
          <textarea id="styleBlacklistTopics" rows="3" placeholder="一行一个，可留空">${escapeHtml(listToText(blacklist.topics))}</textarea>
        </label>
      </div>
    </div>
    <section class="ip-card">
      <span>API IP 白名单</span>
      ${ipMarkup}
      <div class="ip-actions">
        <button id="copyIpButton" type="button" class="mini" ${state.publicIp ? "" : "disabled"}>复制 IP</button>
        <button id="refreshIpButton" type="button" class="mini ghost">${state.publicIp ? "重新获取" : "获取当前 IP"}</button>
      </div>
      <ol class="guide-list compact-guide">
        <li>登录微信公众平台。</li>
        <li>进入「设置与开发」→「基本配置」。</li>
        <li>找到「IP 白名单」，把上方显示的 IP 加进去。</li>
      </ol>
    </section>
  `;
  const apiForm = els.panel.querySelector(".settings-form");
  if (apiForm) {
    apiForm.outerHTML = renderApiConfigRows();
  }
  const styleForm = els.panel.querySelector(".settings-section .settings-form");
  if (styleForm) {
    styleForm.outerHTML = renderStyleConfigRows();
  }
  document.querySelector("#refreshIpButton")?.addEventListener("click", () => loadPublicIp());
  document.querySelectorAll("[data-config-edit]").forEach((button) => {
    button.addEventListener("click", () => openConfigEditModal(button.dataset.configEdit));
  });
  document.querySelectorAll("[data-style-edit]").forEach((button) => {
    button.addEventListener("click", () => openStyleEditModal(button.dataset.styleEdit));
  });
  document.querySelector("#copyIpButton")?.addEventListener("click", async () => {
    if (!state.publicIp) return;
    try {
      await navigator.clipboard.writeText(state.publicIp);
      setMessage("IP 已复制。", "ok");
    } catch {
      setMessage(`请手动复制这个 IP：${state.publicIp}`, "ok");
    }
  });
  setMessage(isSetupReady() ? "设置已可用。留空的已配置项不会被覆盖。" : "请至少补齐 AppID、AppSecret 和 AI 写稿 API Key。");
}

function openConfigEditModal(step) {
  const item = apiConfigItems.find((entry) => entry.step === step);
  if (!item) return;
  const isImageConfig = item.step === "image_api";
  const currentImageProvider = state.config?.image?.provider || "doubao";
  const currentImageModel = state.config?.image?.model
    || (currentImageProvider === "doubao" ? "doubao-seedream-4-0-250828" : "agnes-image-2.1-flash");
  closeTemplatePreview();
  const modal = document.createElement("div");
  modal.className = "preview-modal config-edit-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-close="true"></div>
    <section class="preview-dialog config-edit-dialog">
      <div class="config-edit-head">
        <div>
          <span>修改配置</span>
          <h2>${getApiConfigLabel(item)}</h2>
        </div>
        <button type="button" class="icon-close" data-close="true" aria-label="关闭">&times;</button>
      </div>
      <div class="config-edit-body">
        <p class="config-edit-copy">为了安全，当前值不会明文显示。请输入新的内容，保存后会覆盖本机配置。</p>
        ${isImageConfig ? `
          <label class="answer-field">
            <span>生图服务</span>
            <select id="configImageProvider">
              <option value="doubao" ${currentImageProvider === "doubao" ? "selected" : ""}>豆包 Seedream</option>
              <option value="agnes" ${currentImageProvider === "agnes" ? "selected" : ""}>Agnes Image</option>
            </select>
          </label>
        ` : ""}
        <label class="answer-field">
          <span>${item.required ? "必填" : "选填"}</span>
          <input id="configEditInput" type="${item.type}" autocomplete="off" placeholder="${item.placeholder}">
        </label>
        ${isImageConfig ? `
          <label class="answer-field">
            <span>模型</span>
            <input id="configImageModel" type="text" autocomplete="off" value="${escapeAttr(currentImageModel)}">
          </label>
          <p class="config-edit-copy">豆包需要填写火山方舟控制台创建的 API Key；Agnes 需要填写 Agnes 平台的 API Key。两者不能混用。</p>
        ` : ""}
      </div>
      <div class="config-edit-actions">
        <button type="button" id="saveConfigEditButton">保存修改</button>
      </div>
    </section>
  `;
  document.body.appendChild(modal);
  modal.querySelectorAll("[data-close='true']").forEach((button) => {
    button.addEventListener("click", closeTemplatePreview);
  });
  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeTemplatePreview();
  });
  const input = modal.querySelector("#configEditInput");
  const saveButton = modal.querySelector("#saveConfigEditButton");
  const providerSelect = modal.querySelector("#configImageProvider");
  const modelInput = modal.querySelector("#configImageModel");
  providerSelect?.addEventListener("change", () => {
    if (!modelInput) return;
    modelInput.value = providerSelect.value === "doubao"
      ? "doubao-seedream-4-0-250828"
      : "agnes-image-2.1-flash";
  });
  input?.focus();
  input?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") saveButton?.click();
  });
  saveButton?.addEventListener("click", async () => {
    const value = input?.value.trim() || "";
    if (!value) {
      input?.focus();
      return;
    }
    try {
      saveButton.disabled = true;
      saveButton.textContent = "正在保存...";
      const data = await fetchJson("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step: item.step,
          value,
          ...(isImageConfig ? {
            provider: modal.querySelector("#configImageProvider")?.value || "doubao",
            model: modal.querySelector("#configImageModel")?.value.trim() || "",
          } : {}),
        }),
      });
      state.config = data.config;
      updateStatus();
      closeTemplatePreview();
      renderSettingsPage();
      setMessage(`${item.label} 已更新。`, "ok");
    } catch (error) {
      setMessage(error.message, "error");
      saveButton.disabled = false;
      saveButton.textContent = "保存修改";
    }
  });
}

function buildStylePayloadFromState() {
  const style = state.style || {};
  const blacklist = style.blacklist || {};
  return {
    name: style.name || "",
    full_name: style.full_name || "",
    industry: style.industry || "",
    topics: listToText(style.topics),
    tone: style.tone || "",
    target_audience: style.target_audience || "",
    voice: style.voice || "",
    author: style.author || "",
    writing_persona: style.writing_persona || "warm-editor",
    template: style.template || "studio-brief",
    cover_style: style.cover_style || "",
    reference_accounts: listToText(style.reference_accounts),
    blacklist_words: listToText(blacklist.words),
    blacklist_topics: listToText(blacklist.topics),
  };
}

function fillAbsentStylePayload(payload) {
  for (const item of styleConfigItems) {
    if (!document.querySelector(`#${item.inputId}`)) {
      payload[item.field] = getStyleFieldValue(item.field);
    }
  }
  payload.writing_persona = payload.writing_persona || "warm-editor";
  payload.template = payload.template || "studio-brief";
}

async function saveStylePayload(payload) {
  const styleData = await fetchJson("/api/style", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  state.style = styleData.style;
  state.articleOptions.persona = state.style.writing_persona || state.articleOptions.persona;
  state.articleOptions.template = state.style.template || state.articleOptions.template;
  saveArticleOptions();
  return styleData;
}

function openStyleEditModal(field) {
  const item = styleConfigItems.find((entry) => entry.field === field);
  if (!item) return;
  closeTemplatePreview();
  const currentValue = getStyleFieldValue(item.field);
  const modal = document.createElement("div");
  modal.className = "preview-modal config-edit-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-close="true"></div>
    <section class="preview-dialog config-edit-dialog">
      <div class="config-edit-head">
        <div>
          <span>修改公众号风格</span>
          <h2>${item.label}</h2>
        </div>
        <button type="button" class="icon-close" data-close="true" aria-label="关闭">&times;</button>
      </div>
      <div class="config-edit-body">
        <p class="config-edit-copy">这里会写入本机 style.yaml，后续自动写稿会按新的账号风格生成内容。</p>
        <label class="answer-field">
          <span>${item.required ? "必填" : "选填"}</span>
          ${renderStyleInput({ ...item, inputId: "styleEditInput" }, currentValue)}
        </label>
      </div>
      <div class="config-edit-actions">
        <button type="button" id="saveStyleEditButton">保存修改</button>
      </div>
    </section>
  `;
  document.body.appendChild(modal);
  modal.querySelectorAll("[data-close='true']").forEach((button) => {
    button.addEventListener("click", closeTemplatePreview);
  });
  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeTemplatePreview();
  });
  const input = modal.querySelector("#styleEditInput");
  const saveButton = modal.querySelector("#saveStyleEditButton");
  input?.focus();
  input?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && item.type !== "textarea") saveButton?.click();
  });
  saveButton?.addEventListener("click", async () => {
    const value = input?.value.trim() || "";
    if (item.required && !value) {
      input?.focus();
      return;
    }
    const payload = buildStylePayloadFromState();
    payload[item.field] = value;
    try {
      saveButton.disabled = true;
      saveButton.textContent = "正在保存...";
      await saveStylePayload(payload);
      updateStatus();
      closeTemplatePreview();
      renderSettingsPage();
      setMessage(`${item.label} 已更新。`, "ok");
    } catch (error) {
      setMessage(error.message, "error");
      saveButton.disabled = false;
      saveButton.textContent = "保存修改";
    }
  });
}

async function saveSettingsPage() {
  const stylePayload = {
    name: document.querySelector("#styleName")?.value.trim() || "",
    full_name: document.querySelector("#styleFullName")?.value.trim() || "",
    industry: document.querySelector("#styleIndustry")?.value.trim() || "",
    topics: document.querySelector("#styleTopics")?.value.trim() || "",
    tone: document.querySelector("#styleTone")?.value.trim() || "",
    target_audience: document.querySelector("#styleAudience")?.value.trim() || "",
    voice: document.querySelector("#styleVoice")?.value.trim() || "",
    author: document.querySelector("#styleAuthor")?.value.trim() || "",
    writing_persona: document.querySelector("#stylePersona")?.value || "warm-editor",
    template: document.querySelector("#styleTemplate")?.value || "studio-brief",
    cover_style: document.querySelector("#styleCover")?.value.trim() || "",
    reference_accounts: document.querySelector("#styleReferences")?.value.trim() || "",
    blacklist_words: document.querySelector("#styleBlacklistWords")?.value.trim() || "",
    blacklist_topics: document.querySelector("#styleBlacklistTopics")?.value.trim() || "",
  };
  fillAbsentStylePayload(stylePayload);
  if (!stylePayload.name) {
    setMessage("请填写公众号名称。", "error");
    document.querySelector("#styleName")?.focus();
    return;
  }
  if (!stylePayload.industry) {
    setMessage("请填写行业/机构类型。", "error");
    document.querySelector("#styleIndustry")?.focus();
    return;
  }
  if (!stylePayload.topics) {
    setMessage("请至少填写一个主要内容方向。", "error");
    document.querySelector("#styleTopics")?.focus();
    return;
  }
  if (!stylePayload.tone) {
    setMessage("请填写希望文章是什么风格。", "error");
    document.querySelector("#styleTone")?.focus();
    return;
  }

  let fields = [
    ["appid", "settingsAppid", "AppID", false, Boolean(state.config?.wechat?.appid)],
    ["secret", "settingsSecret", "AppSecret", false, Boolean(state.config?.wechat?.secret)],
    ["ai_api", "settingsAiApi", "AI 写稿 API Key", true, Boolean(state.config?.ai?.api_key)],
    ["image_api", "settingsImageApi", "AI 生图 API Key", false, Boolean(state.config?.image?.api_key)],
  ];
  fields = apiConfigItems.map((item) => [
    item.step,
    item.inputId,
    item.label,
    item.required,
    hasConfigPath(item.path),
  ]);
  const updates = [];
  for (const [step, inputId, label, required, alreadyConfigured] of fields) {
    const value = document.querySelector(`#${inputId}`)?.value.trim() || "";
    if (required && !alreadyConfigured && !value) {
      setMessage(`请填写${label}。`, "error");
      document.querySelector(`#${inputId}`)?.focus();
      return;
    }
    if (value) updates.push({ step, value });
  }
  try {
    els.nextButton.disabled = true;
    els.nextButton.textContent = "正在保存...";
    for (const item of updates) {
      const data = await fetchJson("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(item),
      });
      state.config = data.config;
    }
    await saveStylePayload(stylePayload);
    updateStatus();
    const wasFirstVisit = state.firstVisit;
    state.firstVisit = false;
    localStorage.setItem("wewriteOnboardingComplete", "true");
    if (wasFirstVisit) {
      startArticleWizard();
      setMessage("设置完成，现在可以创建第一篇文章了。", "ok");
    } else {
      renderSettingsPage();
      setMessage("设置已保存。", "ok");
    }
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    els.nextButton.disabled = false;
    els.nextButton.textContent = state.firstVisit ? "完成设置，开始写文章" : "保存设置";
  }
}

function renderSetupStep() {
  state.phase = "setup";
  updateNav("setup");
  setHeader("先把账号配置好", "像做填空题一样，一次只填一项。填完后点“下一项”。");

  const step = setupSteps[state.current];
  const percent = ((state.current + 1) / setupSteps.length) * 100;
  els.progressBar.style.width = `${percent}%`;
  els.backButton.disabled = state.current === 0;
  els.skipButton.hidden = step.required || step.manual;
  els.nextButton.hidden = false;
  els.nextButton.disabled = false;
  els.nextButton.textContent = state.current === setupSteps.length - 1 ? "完成配置" : "下一项";

  if (step.manual) {
    renderIpWhitelistStep(step);
    return;
  }

  els.panel.innerHTML = `
    <p class="step-count">第 ${state.current + 1} 项 / 共 ${setupSteps.length} 项</p>
    <h2>${step.title}</h2>
    <p class="hint">${step.hint}</p>
    <label class="answer-field">
      <span>${step.required ? "必填" : "选填"}</span>
      <input id="answerInput" type="${step.type}" placeholder="${step.placeholder}" autocomplete="off">
    </label>
  `;
  const input = document.querySelector("#answerInput");
  input.focus();
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") saveSetupAndNext(false);
  });
}

function renderIpWhitelistStep(step) {
  const ipMarkup = state.publicIp
    ? `<div id="ipValue" class="ip-value">${state.publicIp}</div>
       <p id="ipHint" class="ip-hint">把上面这个 IP 填到微信公众平台的 IP 白名单里。</p>`
    : `<div id="ipValue" class="ip-value muted">${state.publicIpError ? "获取失败" : "正在获取..."}</div>
       <p id="ipHint" class="ip-hint">${state.publicIpError || "正在检测这台电脑访问外网时使用的出口 IP。"}</p>`;
  els.panel.innerHTML = `
    <p class="step-count">第 ${state.current + 1} 项 / 共 ${setupSteps.length} 项</p>
    <h2>${step.title}</h2>
    <p class="hint">${step.hint}</p>
    <section class="ip-card">
      <span>当前出口 IP</span>
      ${ipMarkup}
      <div class="ip-actions">
        <button id="copyIpButton" type="button" class="mini" ${state.publicIp ? "" : "disabled"}>复制 IP</button>
        <button id="refreshIpButton" type="button" class="mini ghost">重新获取</button>
      </div>
    </section>
    <ol class="guide-list">
      <li>登录微信公众平台。</li>
      <li>进入「设置与开发」→「基本配置」。</li>
      <li>找到「IP 白名单」，把上方显示的 IP 加进去。</li>
      <li>保存后回到这里，点击完成配置。</li>
    </ol>
    <div class="note">提示：如果后续创建草稿时报 IP 白名单错误，通常就是这一步还没设置好。</div>
  `;
  document.querySelector("#refreshIpButton")?.addEventListener("click", () => loadPublicIp());
  document.querySelector("#copyIpButton")?.addEventListener("click", async () => {
    if (!state.publicIp) return;
    try {
      await navigator.clipboard.writeText(state.publicIp);
      setMessage("IP 已复制，可以粘贴到微信公众平台。", "ok");
    } catch {
      setMessage(`请手动复制这个 IP：${state.publicIp}`, "ok");
    }
  });
  if (!state.publicIp && !state.publicIpError) {
    loadPublicIp();
  }
}

async function saveSetupAndNext(skip = false) {
  const step = setupSteps[state.current];
  setMessage("");

  if (!step.manual) {
    const input = document.querySelector("#answerInput");
    const value = input ? input.value.trim() : "";
    if (step.required && !value) {
      setMessage("这一项需要填写后才能继续。", "error");
      input?.focus();
      return;
    }
    if (!step.required && !value) {
      skip = true;
    }
    if (!skip) {
      try {
        els.nextButton.disabled = true;
        const data = await fetchJson("/api/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ step: step.id, value }),
        });
        state.config = data.config;
        updateStatus();
      } catch (error) {
        setMessage(error.message, "error");
        return;
      } finally {
        els.nextButton.disabled = false;
      }
    }
  }

  if (state.current < setupSteps.length - 1) {
    state.current += 1;
    renderSetupStep();
    setMessage(skip ? "已跳过这一项，之后可以再补。" : "已保存，继续下一项。", "ok");
  } else {
    startArticleWizard();
    setMessage("配置完成。现在开始新建文章。", "ok");
  }
}

function resetArticleDraftState() {
  stopGenerationProgress();
  state.current = 0;
  state.selectedFiles = [];
  state.materials = null;
  state.generatedDraft = null;
  state.revisionRequest = "";
  state.previewTemplate = "";
  state.useMaterials = false;
  clearWritingRequest();
  clearCurrentArticleSession();
}

function startArticleWizard() {
  resetArticleDraftState();
  state.articleOptions.persona = state.style?.writing_persona || state.articleOptions.persona || "warm-editor";
  state.articleOptions.articleType = "custom";
  if (state.articleOptions.imageMode === "ai_cover") {
    state.articleOptions.imageMode = "ai_generated";
  }
  if (!["photos", "ai_generated", "none"].includes(state.articleOptions.imageMode)) {
    state.articleOptions.imageMode = state.articleOptions.imageMode === "both" ? "photos" : "none";
  }
  saveArticleOptions();
  state.phase = "articleForm";
  state.articleWorkspacePhase = "articleForm";
  setMessage("");
  renderArticleForm();
}

function hasCurrentArticleWorkspace() {
  return Boolean(
    state.generatedDraft
    || state.materials
    || state.writingRequest?.prompt
    || state.selectedFiles.length
  );
}

function requestNewArticle() {
  if (
    hasCurrentArticleWorkspace()
    && !confirm("新建文章会结束当前工作区。\n\n已生成的文章仍可从“草稿历史”找回；尚未生成的填写内容将被清空。确定继续吗？")
  ) {
    return;
  }
  startArticleWizard();
  setMessage("已创建一个新的文章工作区。", "ok");
}

function restoreArticleWorkspace() {
  const phase = state.articleWorkspacePhase;
  if (phase === "generated" && state.generatedDraft?.article) {
    renderGeneratedDraft(state.generatedDraft);
    return;
  }
  if (phase === "draftReady" && state.writingRequest?.prompt) {
    renderDraftReadySummary();
    return;
  }
  if (phase === "requirements") {
    renderWritingRequestForm();
    return;
  }
  if (phase === "materials" && state.materials) {
    renderMaterialsSummary({ saved_count: 0, materials: state.materials });
    return;
  }
  renderArticleForm();
}

function renderArticleForm() {
  state.phase = "articleForm";
  state.articleWorkspacePhase = "articleForm";
  updateNav("article");
  setHeader("新建公众号文章", "一次完成范文、模板、插图和素材设置，再填写写作要求。");
  els.progressBar.style.width = "35%";
  els.backButton.hidden = true;
  els.skipButton.hidden = true;
  els.nextButton.hidden = false;
  els.nextButton.disabled = false;
  els.nextButton.textContent = "下一步：填写写作要求";

  const templateStep = articleSteps.find((step) => step.id === "template");
  const exemplarEnabled = state.articleOptions.exemplarMode !== "none";
  els.panel.innerHTML = `
    <div class="article-form">
      <section class="form-section">
        <div class="form-section-head form-section-head-toggle">
          <div>
            <span class="section-number">01</span>
            <div class="toggle-title-row">
              <h2>参考范文</h2>
              <label class="switch-control">
                <input id="exemplarToggle" type="checkbox" ${exemplarEnabled ? "checked" : ""}>
                <span class="switch-track"></span>
              </label>
            </div>
            <p>开启后，生成文章时会学习所选范文的结构、语气和节奏。</p>
          </div>
        </div>
        <div id="exemplarPickerWrap" class="conditional-field" ${exemplarEnabled ? "" : "hidden"}>
          <label class="select-field">
            <span>选择参考范文</span>
            <select id="articleExemplarSelect">
              <option value="auto">自动匹配（推荐）</option>
            </select>
          </label>
        </div>
      </section>

      <section class="form-section">
        <div class="form-section-head">
          <div>
            <span class="section-number">02</span>
            <h2>选择模板</h2>
            <p>当前共 ${templateStep.options.length} 套模板，点击按钮进入模板库滑动浏览。</p>
          </div>
        </div>
        <div class="selected-template-summary">
          ${renderSelectedTemplateSummary(templateStep)}
        </div>
      </section>

      <section class="form-section form-section-compact">
        <div class="form-section-head">
          <div>
            <span class="section-number">03</span>
            <h2>选择文章插图</h2>
            <p>决定正文是否使用图片。封面图可在文章生成后单独确认。</p>
          </div>
        </div>
        <label class="select-field">
          <span>插图方式</span>
          <select id="articleImageMode">
            <option value="photos" ${state.articleOptions.imageMode === "photos" ? "selected" : ""}>选择已有图片（在下方导入）</option>
            <option value="ai_generated" ${state.articleOptions.imageMode === "ai_generated" ? "selected" : ""}>AI 生成</option>
            <option value="none" ${state.articleOptions.imageMode === "none" ? "selected" : ""}>不使用</option>
          </select>
        </label>
      </section>

      <section class="form-section">
        <div class="form-section-head form-section-head-toggle">
          <div>
            <span class="section-number">04</span>
            <div class="toggle-title-row">
              <h2>自然润色</h2>
              <label class="switch-control">
                <input id="rewriteToggle" type="checkbox" ${state.articleOptions.rewriteEnabled ? "checked" : ""}>
                <span class="switch-track"></span>
              </label>
            </div>
            <p>开启后，生成初稿会再交给本地改写模型分段润色，减少模板腔，同时保留图片、封面和文章结构。</p>
          </div>
        </div>
      </section>

      <section class="form-section">
        <div class="form-section-head form-section-head-toggle">
          <div>
            <span class="section-number">05</span>
            <div class="toggle-title-row">
              <h2>导入素材</h2>
              <label class="switch-control">
                <input id="materialsToggle" type="checkbox" ${state.useMaterials ? "checked" : ""}>
                <span class="switch-track"></span>
              </label>
            </div>
            <p>可导入 Word、PDF、TXT、Markdown 和图片文件夹。没有素材也可以继续。</p>
          </div>
        </div>
        <div id="materialsUploadWrap" class="conditional-field" ${state.useMaterials ? "" : "hidden"}>
          <label class="upload-card article-upload-card">
            <input id="articleMaterialsInput" type="file" webkitdirectory directory multiple>
            <strong>${state.materials ? "重新选择素材文件夹" : "选择素材文件夹"}</strong>
            <span>${state.materials ? `已导入 ${state.materials.stats?.total_docs || 0} 个文档、${state.materials.stats?.total_photos || 0} 张图片` : "选择后点击下方按钮上传并识别"}</span>
          </label>
          <button id="articleMaterialsUploadButton" class="wide" type="button" ${state.selectedFiles.length ? "" : "disabled"}>
            ${state.materials ? "重新上传素材" : "上传并识别素材"}
          </button>
        </div>
      </section>
    </div>
  `;

  bindArticleFormEvents();
  loadArticleFormExemplars();
  updateStatus();
  saveCurrentArticleSession();
}

function bindArticleFormEvents() {
  document.querySelector("#exemplarToggle")?.addEventListener("change", (event) => {
    state.articleOptions.exemplarMode = event.target.checked ? "default" : "none";
    if (!event.target.checked) state.articleOptions.exemplarFile = "auto";
    saveArticleOptions();
    document.querySelector("#exemplarPickerWrap").hidden = !event.target.checked;
    updateStatus();
    scheduleCurrentArticleSessionSave();
  });
  document.querySelector("#articleImageMode")?.addEventListener("change", (event) => {
    state.articleOptions.imageMode = event.target.value;
    saveArticleOptions();
    updateStatus();
    scheduleCurrentArticleSessionSave();
  });
  document.querySelector("#rewriteToggle")?.addEventListener("change", (event) => {
    state.articleOptions.rewriteEnabled = event.target.checked;
    saveArticleOptions();
    updateStatus();
    scheduleCurrentArticleSessionSave();
  });
  document.querySelector("#materialsToggle")?.addEventListener("change", (event) => {
    state.useMaterials = event.target.checked;
    document.querySelector("#materialsUploadWrap").hidden = !event.target.checked;
    scheduleCurrentArticleSessionSave();
  });
  document.querySelector("#articleMaterialsInput")?.addEventListener("change", (event) => {
    state.selectedFiles = Array.from(event.target.files || []);
    const button = document.querySelector("#articleMaterialsUploadButton");
    if (button) button.disabled = state.selectedFiles.length === 0;
    const text = document.querySelector(".article-upload-card span");
    if (text) text.textContent = state.selectedFiles.length
      ? `已选择 ${state.selectedFiles.length} 个文件，等待上传`
      : "选择后点击下方按钮上传并识别";
  });
  document.querySelector("#articleMaterialsUploadButton")?.addEventListener("click", uploadArticleFormMaterials);
  document.querySelector("#browseTemplatesButton")?.addEventListener("click", openTemplateBrowserModal);
}

function renderSelectedTemplateSummary(templateStep) {
  const option = templateStep.options.find(([value]) => value === state.articleOptions.template)
    || templateStep.options[0];
  const [value, title, description] = option;
  return `
    <img src="${templatePreviews[value]}" alt="${title}模板缩略图">
    <div>
      <span>当前模板</span>
      <strong>${title}</strong>
      <p>${description}</p>
    </div>
    <button id="browseTemplatesButton" type="button">浏览模板</button>
  `;
}

function openTemplateBrowserModal() {
  closeTemplatePreview();
  const templateStep = articleSteps.find((step) => step.id === "template");
  const modal = document.createElement("div");
  modal.className = "preview-modal template-browser-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-close="true"></div>
    <section class="preview-dialog template-browser-dialog" role="dialog" aria-modal="true" aria-label="选择模板">
      <header class="preview-header">
        <div>
          <p class="eyebrow">模板库</p>
          <h2>选择模板</h2>
          <span>左右滑动浏览，预览不会改变当前选择。</span>
        </div>
        <button class="icon-close" type="button" data-close="true" aria-label="关闭">&times;</button>
      </header>
      <div class="template-browser-track">
        ${templateStep.options.map(([value, title, description]) => `
          <article class="template-browser-card ${state.articleOptions.template === value ? "selected" : ""}">
            <div class="template-browser-image">
              <img src="${templatePreviews[value]}" alt="${title}模板预览">
              ${state.articleOptions.template === value ? `<span class="selected-badge">当前模板</span>` : ""}
            </div>
            <div class="template-browser-copy">
              <strong>${title}</strong>
              <span>${description}</span>
            </div>
            <div class="template-browser-actions">
              <button class="mini ghost" type="button" data-gallery-preview="${value}">放大预览</button>
              <button class="mini" type="button" data-gallery-select="${value}" ${state.articleOptions.template === value ? "disabled" : ""}>
                ${state.articleOptions.template === value ? "已选择" : "选择此模板"}
              </button>
            </div>
          </article>
        `).join("")}
      </div>
      <p class="template-browser-hint">可使用鼠标滚轮、触控板或手指左右滑动查看更多模板。</p>
    </section>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", (event) => {
    const target = event.target.closest("[data-close], [data-gallery-preview], [data-gallery-select]");
    if (!target) return;
    if (target.dataset.close) {
      modal.remove();
      return;
    }
    if (target.dataset.galleryPreview) {
      const templateId = target.dataset.galleryPreview;
      modal.remove();
      openTemplatePreview(templateId);
      return;
    }
    if (target.dataset.gallerySelect) {
      state.articleOptions.template = target.dataset.gallerySelect;
      saveArticleOptions();
      saveCurrentArticleSession();
      modal.remove();
      renderArticleForm();
      setMessage("模板已选择。", "ok");
    }
  });
}

async function loadArticleFormExemplars() {
  const select = document.querySelector("#articleExemplarSelect");
  if (!select) return;
  try {
    const exemplars = await ensureExemplarsLoaded();
    select.innerHTML = `
      <option value="auto">自动匹配（推荐）</option>
      ${exemplars.map((item) => `<option value="${escapeAttr(item.file || "")}">${escapeHtml(formatExemplarLabel(item))}</option>`).join("")}
    `;
    select.value = state.articleOptions.exemplarFile || "auto";
    if (!select.value) select.value = "auto";
    select.addEventListener("change", () => {
      state.articleOptions.exemplarFile = select.value || "auto";
      saveArticleOptions();
      updateStatus();
      scheduleCurrentArticleSessionSave();
    });
  } catch (error) {
    select.innerHTML = `<option value="auto">范文列表读取失败，暂用自动匹配</option>`;
  }
}

async function uploadArticleFormMaterials() {
  if (!state.selectedFiles.length) {
    setMessage("请先选择素材文件夹。", "error");
    return;
  }
  const button = document.querySelector("#articleMaterialsUploadButton");
  const formData = new FormData();
  state.selectedFiles.forEach((file) => {
    formData.append("files", file, file.webkitRelativePath || file.name);
  });
  try {
    button.disabled = true;
    button.textContent = "正在上传并识别...";
    setMessage("正在识别素材，请稍等。");
    const response = await fetch("/api/materials/upload", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "素材导入失败。");
    clearWritingRequest();
    state.materials = data.materials;
    renderArticleForm();
    openMaterialsSuccessModal(data);
    setMessage("素材上传并识别完成。", "ok");
  } catch (error) {
    button.disabled = false;
    button.textContent = "重新上传素材";
    setMessage(error.message, "error");
  }
}

function materialFileType(filename) {
  const ext = String(filename || "").split(".").pop().toLowerCase();
  if (["jpg", "jpeg", "png", "gif", "bmp", "webp"].includes(ext)) return "图片";
  if (ext === "docx") return "Word 文档";
  if (ext === "pdf") return "PDF 文档";
  if (ext === "md") return "Markdown";
  if (ext === "txt") return "文本";
  return ext ? ext.toUpperCase() : "文件";
}

function openMaterialsSuccessModal(data) {
  const files = state.selectedFiles.map((file) => ({
    name: file.webkitRelativePath || file.name,
    type: materialFileType(file.name),
  }));
  const modal = document.createElement("div");
  modal.className = "preview-modal materials-success-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-close="true"></div>
    <section class="preview-dialog materials-success-dialog" role="dialog" aria-modal="true" aria-label="素材上传成功">
      <header class="preview-header">
        <div>
          <p class="eyebrow">上传成功</p>
          <h2>素材已经准备好了</h2>
        </div>
        <button class="icon-close" type="button" data-close="true" aria-label="关闭">&times;</button>
      </header>
      <div class="materials-success-body">
        <div class="summary-box">
          <p><span>文档</span><strong>${data.materials?.stats?.total_docs || 0} 个</strong></p>
          <p><span>图片</span><strong>${data.materials?.stats?.total_photos || 0} 张</strong></p>
          <p><span>提取文字</span><strong>${data.materials?.stats?.total_chars || 0} 字</strong></p>
        </div>
        <div class="uploaded-file-list">
          ${files.map((file) => `
            <div>
              <strong>${escapeHtml(file.name)}</strong>
              <span>${escapeHtml(file.type)}</span>
            </div>
          `).join("")}
        </div>
      </div>
      <div class="config-edit-actions">
        <button type="button" data-close="true">知道了</button>
      </div>
    </section>
  `;
  document.body.appendChild(modal);
  modal.querySelectorAll("[data-close='true']").forEach((button) => {
    button.addEventListener("click", () => modal.remove());
  });
}

function renderArticleStep() {
  state.phase = "article";
  updateNav("article");
  setHeader("新建一篇公众号文章", "先选好文章方向和生成方式，下一步再导入素材。");

  const step = articleSteps[state.current];
  const percent = ((state.current + 1) / articleSteps.length) * 100;
  els.progressBar.style.width = `${percent}%`;
  els.backButton.disabled = state.current === 0;
  els.skipButton.hidden = true;
  els.nextButton.disabled = false;
  els.nextButton.textContent = state.current === articleSteps.length - 1 ? "下一步：导入素材" : "下一项";

  const selectedValue = state.articleOptions[step.id];
  if (step.id === "template") {
    renderTemplateStep(step, selectedValue);
    return;
  }
  if (step.id === "exemplarMode") {
    renderExemplarStep(step, selectedValue);
    return;
  }
  els.panel.innerHTML = `
    <p class="step-count">第 ${state.current + 1} 项 / 共 ${articleSteps.length} 项</p>
    <h2>${step.title}</h2>
    <p class="hint">${step.hint}</p>
    <div class="choice-grid">
      ${step.options
        .map(([value, title, description]) => `
          <button class="choice-card ${value === selectedValue ? "selected" : ""}" type="button" data-value="${value}">
            <strong>${title}</strong>
            <span>${description}</span>
          </button>
        `)
        .join("")}
    </div>
  `;

  document.querySelectorAll(".choice-card").forEach((button) => {
    button.addEventListener("click", () => {
      state.articleOptions[step.id] = button.dataset.value;
      saveArticleOptions();
      updateStatus();
      renderArticleStep();
    });
  });
}

async function renderExemplarStep(step, selectedValue) {
  els.panel.innerHTML = `
    <p class="step-count">第 ${state.current + 1} 项 / 共 ${articleSteps.length} 项</p>
    <h2>${step.title}</h2>
    <p class="hint">${step.hint}</p>
    <div class="choice-grid">
      ${step.options
        .map(([value, title, description]) => `
          <button class="choice-card ${value === selectedValue ? "selected" : ""}" type="button" data-value="${value}">
            <strong>${title}</strong>
            <span>${description}</span>
          </button>
        `)
        .join("")}
    </div>
    <label class="select-field">
      <span>选择需要参考的范文</span>
      <select id="exemplarSelect" ${selectedValue === "none" ? "disabled" : ""}>
        <option value="auto">自动匹配（推荐）</option>
      </select>
    </label>
    <div class="note">选择具体范文后，生成时会优先参考这一篇的写法；不会照抄旧文章内容。</div>
  `;

  document.querySelectorAll(".choice-card").forEach((button) => {
    button.addEventListener("click", () => {
      state.articleOptions.exemplarMode = button.dataset.value;
      if (state.articleOptions.exemplarMode === "none") {
        state.articleOptions.exemplarFile = "auto";
      }
      saveArticleOptions();
      updateStatus();
      renderExemplarStep(step, state.articleOptions.exemplarMode);
    });
  });

  const select = document.querySelector("#exemplarSelect");
  try {
    const exemplars = await ensureExemplarsLoaded();
    select.innerHTML = `
      <option value="auto">自动匹配（推荐）</option>
      ${exemplars
        .map((item) => `<option value="${escapeAttr(item.file || "")}">${escapeHtml(formatExemplarLabel(item))}</option>`)
        .join("")}
    `;
    select.value = state.articleOptions.exemplarFile || "auto";
    if (!select.value) select.value = "auto";
    updateStatus();
  } catch (error) {
    select.innerHTML = `<option value="auto">范文列表读取失败，暂用自动匹配</option>`;
    setMessage(error.message, "error");
  }
  select.addEventListener("change", () => {
    state.articleOptions.exemplarFile = select.value || "auto";
    saveArticleOptions();
    updateStatus();
  });
}

function renderTemplateStep(step, selectedValue) {
  els.panel.innerHTML = `
    <p class="step-count">第 ${state.current + 1} 项 / 共 ${articleSteps.length} 项</p>
    <h2>${step.title}</h2>
    <p class="hint">${step.hint}</p>
    <div class="template-strip" aria-label="模板预览">
      ${step.options
        .map(([value, title, description]) => `
          <article class="template-card ${value === selectedValue ? "selected" : ""}" data-value="${value}">
            <button class="template-shot" type="button" data-preview="${value}" aria-label="放大预览 ${title}">
              <img src="${templatePreviews[value]}" alt="${title}模板预览">
            </button>
            <div class="template-copy">
              <strong>${title}</strong>
              <span>${description}</span>
            </div>
          </article>
        `)
        .join("")}
    </div>
  `;

  document.querySelectorAll(".template-card").forEach((card) => {
    card.addEventListener("click", () => {
      state.articleOptions.template = card.dataset.value;
      saveArticleOptions();
      updateStatus();
      renderTemplateStep(step, state.articleOptions.template);
    });
  });
  document.querySelectorAll(".template-shot").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      state.articleOptions.template = button.dataset.preview;
      saveArticleOptions();
      updateStatus();
      openTemplatePreview(button.dataset.preview);
    });
  });
}

function openTemplatePreview(templateId) {
  state.previewTemplate = templateId;
  const option = articleSteps.find((step) => step.id === "template").options.find(([value]) => value === templateId);
  const title = option ? option[1] : labels[templateId];
  const modal = document.createElement("div");
  modal.className = "preview-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-close="true"></div>
    <section class="preview-dialog" role="dialog" aria-modal="true" aria-label="${title}模板大图预览">
      <header class="preview-header">
        <div>
          <p class="eyebrow">Template Preview</p>
          <h2>${title}</h2>
        </div>
        <button class="mini ghost" type="button" data-close="true">关闭</button>
      </header>
      <div class="preview-large-wrap">
        <button class="preview-nav left" type="button" data-shift="-1" aria-label="上一张">‹</button>
        <img class="preview-large" src="${templatePreviews[templateId]}" alt="${title}模板大图预览">
        <button class="preview-nav right" type="button" data-shift="1" aria-label="下一张">›</button>
      </div>
      <div class="preview-thumbs">
        ${articleSteps
          .find((step) => step.id === "template")
          .options.map(([value, label]) => `
            <button class="preview-thumb ${value === templateId ? "selected" : ""}" type="button" data-template="${value}">
              <img src="${templatePreviews[value]}" alt="${label}">
              <span>${label}</span>
            </button>
          `)
          .join("")}
      </div>
    </section>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", (event) => {
    const target = event.target.closest("[data-close], [data-shift], [data-template]");
    if (!target) return;
    if (target.dataset.close) {
      modal.remove();
      return;
    }
    if (target.dataset.shift) {
      shiftTemplatePreview(Number(target.dataset.shift), modal);
      return;
    }
    if (target.dataset.template) {
      state.previewTemplate = target.dataset.template;
      updatePreviewModal(modal);
    }
  });
  document.addEventListener("keydown", handlePreviewKeys);
}

function handlePreviewKeys(event) {
  const modal = document.querySelector(".preview-modal");
  if (!modal) {
    document.removeEventListener("keydown", handlePreviewKeys);
    return;
  }
  if (event.key === "Escape") {
    modal.remove();
    document.removeEventListener("keydown", handlePreviewKeys);
  } else if (event.key === "ArrowLeft") {
    shiftTemplatePreview(-1, modal);
  } else if (event.key === "ArrowRight") {
    shiftTemplatePreview(1, modal);
  }
}

function closeTemplatePreview() {
  document.querySelector(".preview-modal")?.remove();
  document.removeEventListener("keydown", handlePreviewKeys);
}

function shiftTemplatePreview(delta, modal) {
  const options = articleSteps.find((step) => step.id === "template").options;
  const currentIndex = options.findIndex(([value]) => value === state.previewTemplate);
  const nextIndex = (currentIndex + delta + options.length) % options.length;
  state.previewTemplate = options[nextIndex][0];
  updatePreviewModal(modal);
}

function updatePreviewModal(modal) {
  const option = articleSteps.find((step) => step.id === "template").options.find(([value]) => value === state.previewTemplate);
  const title = option ? option[1] : labels[state.previewTemplate];
  modal.querySelector(".preview-header h2").textContent = title;
  const image = modal.querySelector(".preview-large");
  image.src = templatePreviews[state.previewTemplate];
  image.alt = `${title}模板大图预览`;
  modal.querySelectorAll(".preview-thumb").forEach((thumb) => {
    thumb.classList.toggle("selected", thumb.dataset.template === state.previewTemplate);
  });
}

function saveArticleAndNext() {
  const step = articleSteps[state.current];
  if (!state.articleOptions[step.id]) {
    setMessage("请先选择一个选项。", "error");
    return;
  }
  saveArticleOptions();
  updateStatus();

  if (state.current < articleSteps.length - 1) {
    state.current += 1;
    renderArticleStep();
    setMessage("已保存，继续下一项。", "ok");
    return;
  }
  renderMaterialsPlaceholder();
}

function renderMaterialsPlaceholder() {
  state.phase = "materials";
  updateNav("article");
  setHeader("导入素材", "下一阶段会在这里选择素材文件夹，识别文档和图片。");
  els.progressBar.style.width = "100%";
  els.backButton.disabled = false;
  els.skipButton.hidden = true;
  els.nextButton.disabled = true;
  els.nextButton.textContent = "上传并识别";
  els.panel.innerHTML = `
    <p class="step-count">素材导入</p>
    <h2>选择素材文件夹</h2>
    <p class="hint">支持 Word、PDF、TXT、Markdown 和图片。图片放在子文件夹里时，文件夹名会作为分类。</p>
    <div class="summary-box">
      <p><span>文章类型</span><strong>${labels[state.articleOptions.articleType]}</strong></p>
      <p><span>写作人格</span><strong>${labels[state.articleOptions.persona]}</strong></p>
      <p><span>参考范文</span><strong>${getExemplarStatusLabel()}</strong></p>
      <p><span>排版模板</span><strong>${labels[state.articleOptions.template]}</strong></p>
      <p><span>图片方式</span><strong>${labels[state.articleOptions.imageMode]}</strong></p>
    </div>
    <label class="upload-card">
      <input id="materialsInput" type="file" webkitdirectory directory multiple>
      <strong>点击选择素材文件夹</strong>
      <span id="selectedFileCount">尚未选择文件</span>
    </label>
    <div class="note">推荐目录结构：根目录放活动方案 Word/PDF，图片可按“活动现场”“作品展示”等子文件夹分类。</div>
  `;
  const input = document.querySelector("#materialsInput");
  input.addEventListener("change", () => {
    state.selectedFiles = Array.from(input.files || []);
    document.querySelector("#selectedFileCount").textContent = state.selectedFiles.length
      ? `已选择 ${state.selectedFiles.length} 个文件`
      : "尚未选择文件";
    els.nextButton.disabled = state.selectedFiles.length === 0;
    setMessage(state.selectedFiles.length ? "素材文件夹已选择，可以开始上传识别。" : "", state.selectedFiles.length ? "ok" : "");
  });
  setMessage("请选择素材文件夹。", "");
}

async function uploadMaterials() {
  if (!state.selectedFiles.length) {
    setMessage("请先选择素材文件夹。", "error");
    return;
  }
  const formData = new FormData();
  state.selectedFiles.forEach((file) => {
    formData.append("files", file, file.webkitRelativePath || file.name);
  });
  try {
    els.nextButton.disabled = true;
    els.nextButton.textContent = "正在识别...";
    setMessage("正在上传并识别素材，请稍候。");
    const response = await fetch("/api/materials/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "素材导入失败。");
    }
    clearWritingRequest();
    state.materials = data.materials;
    renderMaterialsSummary(data);
  } catch (error) {
    setMessage(error.message, "error");
    els.nextButton.disabled = false;
    els.nextButton.textContent = "上传并识别";
  }
}

function renderMaterialsSummary(data) {
  state.phase = "materials";
  state.articleWorkspacePhase = "materials";
  updateNav("article");
  const stats = data.materials.stats || {};
  const categories = data.materials.categories || [];
  const docs = data.materials.documents || [];
  const errors = docs.filter((doc) => doc.error);
  els.nextButton.disabled = false;
  els.nextButton.textContent = "下一步：填写要求";
  els.panel.innerHTML = `
    <p class="step-count">素材导入完成</p>
    <h2>素材识别摘要</h2>
    <div class="summary-box">
      <p><span>已保存文件</span><strong>${data.saved_count || 0} 个</strong></p>
      <p><span>文档</span><strong>${stats.total_docs || 0} 个</strong></p>
      <p><span>图片</span><strong>${stats.total_photos || 0} 张</strong></p>
      <p><span>提取文字</span><strong>${stats.total_chars || 0} 字</strong></p>
      <p><span>图片分类</span><strong>${categories.length ? categories.join("、") : "未分类"}</strong></p>
    </div>
    <div class="material-list">
      ${docs.length ? `<h3>文档</h3>${docs.map((doc) => `
        <p>
          <strong>${doc.filename}</strong>
          <span>${doc.error ? doc.error : `${doc.char_count || 0} 字`}</span>
        </p>
      `).join("")}` : ""}
      ${(data.materials.photos || []).length ? `<h3>图片</h3>${(data.materials.photos || []).slice(0, 8).map((photo) => `
        <p>
          <strong>${photo.filename}</strong>
          <span>${photo.category || "未分类"}</span>
        </p>
      `).join("")}` : ""}
    </div>
    ${errors.length ? `<div class="note error-note">有 ${errors.length} 个文档未能提取文字，可以稍后改存为 TXT 再导入。</div>` : `<div class="note">素材已准备好。下一步会把这些素材送入自动写稿流程。</div>`}
  `;
  setMessage("素材识别完成。", "ok");
  saveCurrentArticleSession();
}

function renderWritingRequestForm() {
  state.phase = "requirements";
  state.articleWorkspacePhase = "requirements";
  updateNav("article");
  mergeInferredWritingRequest();
  setHeader("填写写作要求", "像和 AI 对话一样，用一句话告诉它你想写什么。");
  els.progressBar.style.width = "100%";
  els.backButton.hidden = false;
  els.backButton.disabled = false;
  els.skipButton.hidden = true;
  els.nextButton.disabled = false;
  els.nextButton.textContent = "保存要求";
  const prompt = getWritingPrompt();
  els.panel.innerHTML = `
    <p class="step-count">生成前最后一步</p>
    <h2>提示词</h2>
    <p class="hint">不用写得很完整，像发消息一样说清楚主题和特别要求即可。已上传的素材会自动参与写作。</p>
    <div class="prompt-compose">
      <textarea id="writingPromptInput" rows="8" placeholder="例如：帮我写一篇 AI 科技进校园活动报道，重点突出学生的互动体验，语气活泼一点，不要编造学生原话。">${escapeHtml(prompt)}</textarea>
      <div class="prompt-suggestions">
        <strong>可以这样说：</strong>
        <span>“写一篇校园活动报道，温暖但不要太抒情。”</span>
        <span>“重点写活动过程和学生体验，不要写具体人数。”</span>
        <span>“标题活泼一点，正文简洁，适合家长阅读。”</span>
      </div>
    </div>
  `;
  const promptInput = document.querySelector("#writingPromptInput");
  promptInput.focus();
  promptInput.addEventListener("input", () => {
    state.writingRequest = {
      ...state.writingRequest,
      prompt: promptInput.value,
      topic: deriveTopicFromPrompt(promptInput.value),
    };
    saveWritingRequest();
    scheduleCurrentArticleSessionSave();
  });
  saveCurrentArticleSession();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll('"', "&quot;");
}

function collectWritingRequest() {
  const prompt = document.querySelector("#writingPromptInput")?.value.trim() || "";
  if (!prompt) {
    setMessage("请用一句话告诉 AI 你想写什么。", "error");
    document.querySelector("#writingPromptInput")?.focus();
    return null;
  }
  state.writingRequest = {
    prompt,
    topic: deriveTopicFromPrompt(prompt),
    activity_time: "",
    activity_location: "",
    focus: prompt,
    avoid: "",
    material_signature: getMaterialsSignature(state.materials),
  };
  saveWritingRequest();
  saveCurrentArticleSession();
  return state.writingRequest;
}

function getWritingPrompt() {
  const req = state.writingRequest || {};
  if (req.prompt) return String(req.prompt);
  return [
    req.topic,
    req.activity_time ? `活动时间是${req.activity_time}` : "",
    req.activity_location ? `活动地点是${req.activity_location}` : "",
    req.focus,
    req.avoid ? `不要写：${req.avoid}` : "",
  ].filter(Boolean).join("，");
}

function deriveTopicFromPrompt(prompt) {
  const firstSentence = String(prompt || "").split(/[。！？!?\n]/)[0].trim();
  return (firstSentence || String(prompt || "").trim()).slice(0, 100);
}

function buildDraftPayload() {
  const activeMaterials = state.useMaterials ? state.materials : null;
  const requirements = {
    article_type: state.articleOptions.articleType,
    persona: state.articleOptions.persona,
    exemplar_mode: state.articleOptions.exemplarMode,
    exemplar_file: state.articleOptions.exemplarFile || "auto",
    image_mode: state.articleOptions.imageMode,
    rewrite_enabled: Boolean(state.articleOptions.rewriteEnabled),
    user_prompt: state.writingRequest.prompt || state.writingRequest.focus,
    activity_time: state.writingRequest.activity_time,
    activity_location: state.writingRequest.activity_location,
    focus: state.writingRequest.focus,
    avoid: state.writingRequest.avoid,
  };
  if (state.revisionRequest) {
    requirements.revision_request = state.revisionRequest;
  }
  const payload = {
    topic: state.writingRequest.topic,
    materials: activeMaterials,
    materials_text: [
      state.writingRequest.prompt,
      state.writingRequest.topic,
    ].filter(Boolean).join("\n"),
    template: state.articleOptions.template,
    requirements,
  };
  if (state.revisionRequest && state.generatedDraft?.article) {
    payload.previous_article = state.generatedDraft.article;
  }
  return payload;
}

function renderDraftReadySummary() {
  const payload = buildDraftPayload();
  const stats = payload.materials?.stats || {};
  state.phase = "draftReady";
  state.articleWorkspacePhase = "draftReady";
  updateNav("article");
  setHeader("准备生成文章", "写作要求已保存，下一步将调用 AI 生成初稿。");
  els.progressBar.style.width = "100%";
  els.backButton.disabled = false;
  els.skipButton.hidden = true;
  els.nextButton.disabled = false;
  els.nextButton.textContent = "生成文章并预览";
  els.panel.innerHTML = `
    <p class="step-count">生成前确认</p>
    <h2>${escapeHtml(state.writingRequest.topic)}</h2>
    <div class="summary-box">
      <p><span>文章类型</span><strong>${labels[state.articleOptions.articleType]}</strong></p>
      <p><span>写作人格</span><strong>${labels[state.articleOptions.persona]}</strong></p>
      <p><span>参考范文</span><strong>${getExemplarStatusLabel()}</strong></p>
      <p><span>排版模板</span><strong>${labels[state.articleOptions.template]}</strong></p>
      <p><span>图片方式</span><strong>${labels[state.articleOptions.imageMode]}</strong></p>
      <p><span>自然润色</span><strong>${state.articleOptions.rewriteEnabled ? "开启" : "关闭"}</strong></p>
      <p><span>素材文字</span><strong>${stats.total_chars || 0} 字</strong></p>
      <p><span>素材图片</span><strong>${stats.total_photos || 0} 张</strong></p>
    </div>
    <div class="material-list">
      <p class="prompt-summary"><strong>提示词</strong><span>${escapeHtml(state.writingRequest.prompt || state.writingRequest.focus || "")}</span></p>
    </div>
    <div class="note">点击生成后会调用 AI 写稿，并用本地模板自动排版成预览页面。真实生成可能需要几十秒。</div>
  `;
  console.debug("Draft payload ready", payload);
  setMessage("写作要求已保存。", "ok");
  saveCurrentArticleSession();
}

function getGenerationSteps() {
  const steps = [
    ["正在读取素材和写作要求", 18],
  ];
  if (state.articleOptions.exemplarMode !== "none") {
    steps.push(["正在参考范文风格", 34]);
  }
  steps.push(["正在撰写文章初稿", 60]);
  if (state.articleOptions.rewriteEnabled) {
    steps.push(["正在分段自然润色", 72]);
  }
  steps.push(["正在检查事实与文章结构", 80]);
  if (state.articleOptions.imageMode === "ai_generated") {
    steps.push(["正在生成正文插图", 92]);
  }
  steps.push(["正在套用模板排版", 97]);
  return steps;
}

function stopGenerationProgress() {
  if (state.generationTimer) {
    window.clearInterval(state.generationTimer);
    state.generationTimer = null;
  }
}

function updateGenerationProgress(percent, label) {
  const bar = document.querySelector("#generationProgressBar");
  const percentText = document.querySelector("#generationProgressPercent");
  const labelText = document.querySelector("#generationProgressLabel");
  if (bar) bar.style.width = `${percent}%`;
  if (percentText) percentText.textContent = `${percent}%`;
  if (labelText && label) labelText.textContent = label;
  document.querySelectorAll(".generation-steps li").forEach((item) => {
    const target = Number(item.dataset.target || 0);
    item.classList.toggle("done", percent >= target);
    item.classList.toggle("active", percent < target && target - percent <= 20);
  });
}

function startGenerationProgress() {
  stopGenerationProgress();
  const generationSteps = getGenerationSteps();
  let stepIndex = 0;
  let percent = 8;
  updateGenerationProgress(percent, generationSteps[0][0]);
  state.generationTimer = window.setInterval(() => {
    const [label, target] = generationSteps[Math.min(stepIndex, generationSteps.length - 1)];
    if (percent < target) {
      percent = Math.min(target, percent + 2 + Math.floor(Math.random() * 3));
      updateGenerationProgress(percent, label);
      return;
    }
    if (stepIndex < generationSteps.length - 1) {
      stepIndex += 1;
      updateGenerationProgress(percent, generationSteps[stepIndex][0]);
    }
  }, 900);
}

async function generateDraftPreview() {
  const revisionInput = document.querySelector("#revisionRequestInput");
  if (revisionInput) {
    state.revisionRequest = revisionInput.value.trim();
  }
  const payload = buildDraftPayload();
  const generatingAiImages = state.articleOptions.imageMode === "ai_generated";
  const progressSteps = getGenerationSteps();
  state.phase = "generating";
  updateNav("article");
  els.backButton.disabled = true;
  els.skipButton.hidden = true;
  els.nextButton.disabled = true;
  els.nextButton.textContent = "正在生成...";
  els.panel.innerHTML = `
    <p class="step-count">AI 写稿中</p>
    <h2>正在生成并排版</h2>
    <p class="hint">系统会按顺序处理素材、风格、正文${generatingAiImages ? "、插图" : ""}和排版。你可以直接看下方当前正在进行哪一步。</p>
    <div class="generation-progress" aria-label="生成进度">
      <div class="generation-progress-top">
        <strong id="generationProgressLabel">整理素材与要求</strong>
        <span id="generationProgressPercent">8%</span>
      </div>
      <div class="generation-progress-track">
        <div id="generationProgressBar" class="generation-progress-bar" style="width: 8%;"></div>
      </div>
      <ol class="generation-steps">
        ${progressSteps.map(([label, target]) => `<li data-target="${target}">${escapeHtml(label.replace(/^正在/, ""))}</li>`).join("")}
      </ol>
    </div>
    <div class="generation-card">
      <strong>请稍等，不要关闭这个页面。</strong>
      <span>真实生成通常需要几十秒${generatingAiImages ? "，正文插图会逐张生成，耗时可能更长" : ""}；如果文章格式不合格，后端会自动尝试修复一次。</span>
    </div>
  `;
  setMessage("正在生成文章，请稍等。");
  startGenerationProgress();

  try {
    const response = await fetch("/api/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok && !data.html) {
      throw new Error(data.error || `生成失败：${response.status}`);
    }
    updateGenerationProgress(100, "生成完成");
    stopGenerationProgress();
    state.generatedDraft = data;
    chooseDefaultMaterialCover(data.article);
    renderGeneratedDraft(data);
  } catch (error) {
    stopGenerationProgress();
    state.phase = "draftReady";
    els.backButton.disabled = false;
    els.nextButton.disabled = false;
    els.nextButton.textContent = "重新生成";
    setMessage(error.message, "error");
    els.panel.innerHTML += `<div class="note error-note">${escapeHtml(error.message)}</div>`;
  }
}

function getMaterialCoverCandidates() {
  if (!state.useMaterials) return [];
  const photos = Array.isArray(state.materials?.photos) ? state.materials.photos : [];
  return photos
    .filter((photo) => photo && (photo.preview_url || photo.url))
    .map((photo) => ({
      filename: photo.filename || "素材图片",
      local_path: photo.url || "",
      url: photo.url || "",
      preview_url: photo.preview_url || photo.url || "",
      category: photo.category || "",
      source: "material",
    }));
}

function getAiImageCoverCandidates(article = state.generatedDraft?.article) {
  const candidates = [];
  for (const section of article?.sections || []) {
    const image = section?.image;
    if (!image || image.source !== "ai" || !(image.preview_url || image.url)) continue;
    candidates.push({
      filename: image.caption || "AI 正文插图",
      local_path: image.local_path || image.url || "",
      url: image.url || image.local_path || "",
      preview_url: image.preview_url || image.url || "",
      category: image.caption || "AI 正文插图",
      source: "ai-content",
    });
  }
  return candidates;
}

function getArticleImageCoverCandidates(article = state.generatedDraft?.article) {
  const images = [];
  if (article?.headline?.image) images.push(article.headline.image);
  for (const section of article?.sections || []) {
    if (section?.image) images.push(section.image);
    for (const block of section?.blocks || []) {
      if (block?.type === "image") images.push(block);
    }
  }
  return images
    .filter((image) => image && (image.preview_url || String(image.url || "").startsWith("http")))
    .map((image, index) => ({
      filename: image.filename || image.caption || `正文图片 ${index + 1}`,
      local_path: image.local_path || image.url || "",
      url: image.url || image.local_path || "",
      preview_url: image.preview_url || image.url || "",
      category: image.caption || image.category || image.filename || `正文图片 ${index + 1}`,
      source: image.source || "article",
    }));
}

function getCoverCandidates(article = state.generatedDraft?.article) {
  const candidates = [
    ...getMaterialCoverCandidates(),
    ...getArticleImageCoverCandidates(article),
    ...getAiImageCoverCandidates(article),
  ];
  const seen = new Set();
  return candidates.filter((item) => {
    const key = item.local_path || item.url || item.preview_url;
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function getArticleCover(article = state.generatedDraft?.article) {
  const meta = article?.meta && typeof article.meta === "object" ? article.meta : {};
  return meta.cover_image && typeof meta.cover_image === "object" ? meta.cover_image : null;
}

function coverPreviewUrl(cover) {
  if (!cover) return "";
  return cover.preview_url || (String(cover.url || "").startsWith("http") ? cover.url : "");
}

function chooseDefaultMaterialCover(article) {
  if (!article || getArticleCover(article)) return;
  if (!["photos"].includes(state.articleOptions.imageMode)) return;
  const first = getMaterialCoverCandidates()[0];
  if (first) setArticleCover(first, article);
}

function setArticleCover(cover, article = state.generatedDraft?.article) {
  if (!article || !cover) return;
  if (!article.meta || typeof article.meta !== "object") article.meta = {};
  article.meta.cover_image = {
    filename: cover.filename || "cover",
    local_path: cover.local_path || cover.url || "",
    url: cover.url || cover.local_path || "",
    preview_url: cover.preview_url || "",
    source: cover.source || "material",
    prompt: cover.prompt || "",
    custom_prompt: cover.custom_prompt || "",
  };
  delete article.meta.thumb_media_id;
}

function countArticleImages(article) {
  let count = 0;
  if (article?.headline?.image) count += 1;
  for (const section of article?.sections || []) {
    if (section?.image) count += 1;
    for (const block of section?.blocks || []) {
      if (block?.type === "image") count += 1;
    }
  }
  return count;
}

function renderImageWorkflow(article) {
  const candidates = getCoverCandidates(article);
  const cover = getArticleCover(article);
  const selectedPath = cover?.local_path || cover?.url || "";
  const previewUrl = coverPreviewUrl(cover);
  const canGenerate = Boolean(state.config?.image?.api_key);
  const aiImageCount = getAiImageCoverCandidates(article).length;
  return `
    <section class="image-workflow">
      <div class="image-workflow-head">
        <div>
          <p class="eyebrow">图片处理</p>
          <h3>确认正文图片和封面图</h3>
          <span>正文中的本地图片会在推送时自动上传到微信。这里只需要确认封面。</span>
        </div>
        <div class="image-status-pills">
          <span>${countArticleImages(article)} 张正文图</span>
          ${aiImageCount ? `<span class="ready">AI 已生成 ${aiImageCount} 张</span>` : ""}
          <span class="${cover ? "ready" : "missing"}">${cover ? "封面已就绪" : "还需选择封面"}</span>
        </div>
      </div>
      <div class="cover-stage">
        <div class="cover-preview ${previewUrl ? "has-image" : ""}">
          ${previewUrl
            ? `<img src="${escapeAttr(previewUrl)}" alt="当前封面图">`
            : `<div><strong>尚未设置封面</strong><span>从素材中选择、上传图片或使用 AI 生成。</span></div>`}
        </div>
        <div class="cover-actions">
          <label for="coverPromptInput">封面补充要求 <span>选填</span></label>
          <textarea id="coverPromptInput" rows="3" placeholder="例如：突出科技感，蓝白色调，画面不要出现文字。">${escapeHtml(cover?.source === "ai" ? cover?.custom_prompt || "" : "")}</textarea>
          <div class="cover-action-row">
            <button id="generateCoverButton" class="primary" type="button" ${canGenerate ? "" : "disabled"}>
              ${cover?.source === "ai" ? "重新生成 AI 封面" : "生成 AI 封面"}
            </button>
            <label class="button-like" for="coverUploadInput">上传自定义封面</label>
            <input id="coverUploadInput" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" hidden>
          </div>
          ${!canGenerate ? `<small>AI 生图 API 尚未配置，仍可使用素材图片或上传自定义封面。</small>` : ""}
          <div id="coverActionStatus" class="cover-action-status" aria-live="polite"></div>
        </div>
      </div>
      ${candidates.length ? `
        <div class="cover-library">
          <strong>从正文图片中选择封面</strong>
          <div class="cover-candidate-strip">
            ${candidates.map((photo) => `
              <button class="cover-candidate ${selectedPath === (photo.local_path || photo.url) ? "selected" : ""}" type="button" data-cover-path="${escapeAttr(photo.local_path || photo.url)}">
                <img src="${escapeAttr(photo.preview_url)}" alt="${escapeAttr(photo.filename)}">
                <span>${escapeHtml(photo.category || photo.filename)}</span>
              </button>
            `).join("")}
          </div>
        </div>
      ` : `<div class="note compact-note">当前没有可用的正文图片，可以上传一张封面，或使用 AI 生成封面。</div>`}
    </section>
  `;
}

function bindImageWorkflow() {
  document.querySelectorAll("[data-cover-path]").forEach((button) => {
    button.addEventListener("click", () => {
      const previousScrollLeft = button.closest(".cover-candidate-strip")?.scrollLeft || 0;
      const candidate = getCoverCandidates().find(
        (item) => (item.local_path || item.url) === button.dataset.coverPath
      );
      if (!candidate) return;
      state.revisionRequest = document.querySelector("#revisionRequestInput")?.value.trim() || "";
      setArticleCover(candidate);
      renderGeneratedDraft(state.generatedDraft);
      const nextStrip = document.querySelector(".cover-candidate-strip");
      if (nextStrip) nextStrip.scrollLeft = previousScrollLeft;
      setMessage("封面图已选择。", "ok");
    });
  });
  document.querySelector("#generateCoverButton")?.addEventListener("click", generateAiCover);
  document.querySelector("#coverUploadInput")?.addEventListener("change", uploadCustomCover);
}

async function generateAiCover() {
  const button = document.querySelector("#generateCoverButton");
  const status = document.querySelector("#coverActionStatus");
  const prompt = document.querySelector("#coverPromptInput")?.value.trim() || "";
  try {
    button.disabled = true;
    button.textContent = "正在生成封面...";
    status.className = "cover-action-status";
    status.textContent = "AI 正在生成横版封面，通常需要几十秒。";
    const response = await fetch("/api/images/cover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ article: state.generatedDraft?.article, prompt }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw data;
    state.revisionRequest = document.querySelector("#revisionRequestInput")?.value.trim() || "";
    setArticleCover(data.cover);
    renderGeneratedDraft(state.generatedDraft);
    setMessage("AI 封面已生成并选中。", "ok");
  } catch (error) {
    button.disabled = false;
    button.textContent = "重新生成 AI 封面";
    status.className = "cover-action-status error";
    status.textContent = formatUserError(error, "AI 封面生成失败。");
    setMessage(status.textContent, "error");
  }
}

async function uploadCustomCover(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const status = document.querySelector("#coverActionStatus");
  const formData = new FormData();
  formData.append("file", file, file.name);
  try {
    status.className = "cover-action-status";
    status.textContent = "正在保存封面图...";
    const response = await fetch("/api/images/cover-upload", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok || !data.ok) throw data;
    state.revisionRequest = document.querySelector("#revisionRequestInput")?.value.trim() || "";
    setArticleCover(data.cover);
    renderGeneratedDraft(state.generatedDraft);
    setMessage("自定义封面已上传并选中。", "ok");
  } catch (error) {
    status.className = "cover-action-status error";
    status.textContent = formatUserError(error, "封面上传失败。");
    setMessage(status.textContent, "error");
  } finally {
    event.target.value = "";
  }
}

function renderGeneratedDraft(data) {
  state.phase = "generated";
  state.articleWorkspacePhase = "generated";
  updateNav("article");
  const errors = Array.isArray(data.errors) ? data.errors : [];
  const warnings = Array.isArray(data.warnings) ? data.warnings : [];
  const userIssues = data.user_issues || {};
  const userErrors = Array.isArray(userIssues.errors) ? userIssues.errors : errors.map(formatIssue);
  const userWarnings = Array.isArray(userIssues.warnings) ? userIssues.warnings : warnings.map(formatIssue);
  const imageGenerationErrors = Array.isArray(data.image_generation?.errors) ? data.image_generation.errors : [];
  const rewriteInfo = data.rewrite || null;
  const title = data.article?.meta?.title || state.writingRequest.topic || "生成文章";
  setHeader("文章已生成", "下面是本地模板排版后的预览。请先检查事实、措辞和图片位置，再进入后续编辑/发布步骤。");
  els.progressBar.style.width = "100%";
  els.backButton.disabled = false;
  els.skipButton.hidden = true;
  els.nextButton.disabled = false;
  els.nextButton.textContent = "按修改要求重新生成";
  els.panel.innerHTML = `
    <p class="step-count">${data.ok ? "生成完成" : "已生成，但需要检查"}</p>
    <h2>${escapeHtml(title)}</h2>
    <div class="summary-box">
      <p><span>预览状态</span><strong>${errors.length ? "需要调整" : "可预览"}</strong></p>
      <p><span>必须修改</span><strong>${userErrors.length} 项</strong></p>
      <p><span>发布前事项</span><strong>${userWarnings.length} 项</strong></p>
      <p><span>自动修复</span><strong>${data.repaired ? "已尝试" : "未触发"}</strong></p>
      ${rewriteInfo ? `<p><span>自然润色</span><strong>${rewriteInfo.errors?.length ? "未完成" : `${rewriteInfo.changed_count || 0} 段`}</strong></p>` : ""}
      ${data.image_generation ? `<p><span>AI 正文插图</span><strong>${data.image_generation.generated_count || 0} 张</strong></p>` : ""}
    </div>
    ${userErrors.length ? renderIssueList("必须修改", userErrors, "error-note") : ""}
    ${userWarnings.length ? renderIssueList("发布前待处理", userWarnings, "") : ""}
    ${imageGenerationErrors.length ? renderIssueList("部分 AI 插图未完成", imageGenerationErrors, "error-note") : ""}
    ${renderImageWorkflow(data.article)}
    <div class="preview-frame-wrap">
      <iframe id="draftPreviewFrame" title="文章排版预览"></iframe>
    </div>
    <div class="revision-box">
      <label for="revisionRequestInput">想让文章怎么改？</label>
      <textarea id="revisionRequestInput" rows="4" placeholder="例如：标题再活泼一点；第二部分写短一点；不要写领导致辞；把图片更多放在活动现场部分。">${escapeHtml(state.revisionRequest || "")}</textarea>
      <p>填写后点击下方“按修改要求重新生成”，系统会参考当前预览重新写一版。</p>
    </div>
    <div class="publish-box">
      <strong>预览满意了吗？</strong>
      <span>点击后会自动上传文章图片和封面图，并把文章创建到微信公众号草稿箱。</span>
      <button id="pushDraftButton" class="primary wide" type="button" ${getArticleCover(data.article) ? "" : "disabled"}>推送到微信草稿箱</button>
      ${getArticleCover(data.article) ? "" : `<small>请先在上方确认一张封面图，才能推送到微信草稿箱。</small>`}
      <div id="publishStatus" class="publish-status" aria-live="polite"></div>
    </div>
  `;
  const frame = document.querySelector("#draftPreviewFrame");
  frame.srcdoc = data.html || "<p>没有可预览的 HTML。</p>";
  bindImageWorkflow();
  document.querySelector("#pushDraftButton")?.addEventListener("click", pushToWeChatDraft);
  document.querySelector("#revisionRequestInput")?.addEventListener("input", (event) => {
    state.revisionRequest = event.target.value;
    scheduleCurrentArticleSessionSave();
  });
  setMessage(data.ok ? "文章生成并通过本地校验。" : "文章已生成，但有校验问题，请先检查。", data.ok ? "ok" : "error");
  saveCurrentArticleSession();
}

async function pushToWeChatDraft() {
  const article = state.generatedDraft?.article;
  const button = document.querySelector("#pushDraftButton");
  const status = document.querySelector("#publishStatus");
  if (!article) {
    setMessage("请先生成文章预览。", "error");
    return;
  }
  if (!getArticleCover(article)) {
    setMessage("请先确认一张封面图，再推送到微信草稿箱。", "error");
    document.querySelector(".image-workflow")?.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  try {
    button.disabled = true;
    button.textContent = "正在推送...";
    status.className = "publish-status";
    status.textContent = "正在上传图片并创建微信草稿，请稍等。";
    const response = await fetch("/api/wechat-draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ article, history_id: state.generatedDraft?.history_id || "" }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw data;
    }
    state.generatedDraft = { ...state.generatedDraft, ...data };
    status.className = "publish-status ok";
    status.innerHTML = `
      <strong>已成功推送到微信公众号草稿箱</strong>
      <ol class="publish-next-steps">
        <li><span>1</span><div><b>打开微信公众号后台</b><small>登录 mp.weixin.qq.com</small></div></li>
        <li><span>2</span><div><b>进入草稿箱</b><small>找到刚刚推送的《${escapeHtml(article.meta?.title || "公众号文章")}》</small></div></li>
        <li><span>3</span><div><b>检查并发布</b><small>确认正文、图片和封面后，再预览或群发</small></div></li>
      </ol>
      <small>已上传正文图片 ${data.uploaded_images || 0} 张，本地草稿历史也已标记为“已推送”。</small>
    `;
    button.textContent = "已推送到草稿箱";
    setMessage("微信草稿创建成功。", "ok");
    saveCurrentArticleSession();
  } catch (error) {
    const message = formatUserError(error, "创建微信草稿失败。");
    button.disabled = false;
    button.textContent = "重新推送到微信草稿箱";
    status.className = "publish-status error";
    status.innerHTML = renderUserError(message, error);
    setMessage(message, "error");
  }
}

function formatUserError(error, fallback = "操作失败。") {
  if (!error) return fallback;
  if (typeof error === "string") return error;
  return error.error || error.message || fallback;
}

function renderUserError(message, error) {
  const steps = Array.isArray(error?.action_steps) ? error.action_steps : [];
  const detail = error?.error_detail || error?.raw_error || "";
  return `
    <strong>${escapeHtml(message)}</strong>
    ${steps.length ? `<ol>${steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol>` : ""}
    ${detail ? `<details><summary>技术信息</summary><code>${escapeHtml(detail)}</code></details>` : ""}
  `;
}

function showInlineUserError(container, error, fallback) {
  const message = formatUserError(error, fallback);
  if (!container) {
    setMessage(message, "error");
    return;
  }
  container.querySelector(".inline-user-error")?.remove();
  const panel = document.createElement("div");
  panel.className = "inline-user-error";
  panel.innerHTML = renderUserError(message, error);
  container.appendChild(panel);
  setMessage(message, "error");
}

function renderIssueList(title, items, extraClass) {
  return `
    <div class="note ${extraClass}">
      <strong>${title}</strong>
      <ul class="issue-list">
        ${items.map((item) => `<li>${escapeHtml(formatIssue(item))}</li>`).join("")}
      </ul>
    </div>
  `;
}

function formatIssue(item) {
  if (typeof item === "string") return item;
  try {
    return JSON.stringify(item);
  } catch {
    return String(item);
  }
}

async function renderStyleLibraryPage(message = "") {
  state.phase = "styles";
  updateNav("styles");
  setHeader("范文学习", "管理可供写作参考的范文。生成文章时，可以选择是否学习其中一篇的结构、语气和节奏。");
  els.progressBar.style.width = "100%";
  els.backButton.disabled = true;
  els.skipButton.hidden = true;
  els.nextButton.hidden = true;
  els.nextButton.disabled = true;
  els.panel.innerHTML = `
    <p class="step-count">范文库</p>
    <h2>正在读取风格库...</h2>
    <p class="hint">范文只用于学习结构、语气和段落节奏，不会把旧文章事实带进新文章。</p>
  `;
  setMessage("");
  try {
    const data = await fetchJson("/api/exemplars");
    const exemplars = Array.isArray(data.exemplars) ? data.exemplars : [];
    state.exemplars = exemplars;
    state.exemplarsLoaded = true;
    els.panel.innerHTML = `
      <p class="step-count">共 ${exemplars.length} 篇范文</p>
      <h2>已沉淀的参考风格</h2>
      <p class="hint">范文用于学习结构、语气和段落节奏。需要新增时，点击下方按钮导入 Word 或公众号文章链接。</p>
      <div class="style-toolbar">
        <span>生成时可以自动匹配范文，也可以在新建文章向导中指定某一篇。</span>
        <button id="openExemplarImportButton" class="mini" type="button">添加范文</button>
      </div>
      <div class="style-library">
        ${exemplars.length ? exemplars.map(renderExemplarCard).join("") : `
          <section class="empty-state">
            <strong>还没有参考范文</strong>
            <p>可以先导入一篇公众号文章作为参考风格。WeWrite 会学习它的结构、语气和段落节奏，不会照抄原文内容。</p>
            <button id="emptyAddExemplarButton" type="button">导入第一篇范文</button>
          </section>
        `}
      </div>
    `;
    bindStyleLibraryEvents();
    if (message) {
      showImportStatus(message, "ok");
      setMessage(message, "ok");
    } else {
      setMessage("风格库读取完成。", "ok");
    }
  } catch (error) {
    els.panel.innerHTML = `
      <p class="step-count">范文库</p>
      <h2>风格库读取失败</h2>
      <div class="note error-note">${escapeHtml(error.message)}</div>
    `;
    setMessage(error.message, "error");
  }
}

function showImportStatus(message, type = "") {
  const status = document.querySelector("#exemplarImportStatus");
  if (!status) {
    setMessage(message, type);
    return;
  }
  status.hidden = false;
  status.textContent = message;
  status.className = `import-status ${type}`.trim();
}

function renderExemplarCategorySelect(id) {
  const categories = [
    ["general", "通用"],
    ["story-emotional", "故事/情感"],
    ["list-practical", "清单/实用"],
    ["tech-opinion", "科技/观点"],
    ["hot-take", "热点/锐评"],
  ];
  return `
    <select id="${id}">
      ${categories.map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}
    </select>
  `;
}

function renderExemplarImportChoice() {
  return `
    <p class="hint">请选择一种导入方式。导入后，系统会自动学习这篇文章的结构、语气和风格。</p>
    <div class="import-choice-grid">
      <button class="choice-card" type="button" data-import-mode="word">
        <strong>Word 导入</strong>
        <span>适合已经保存好的 .docx 范文，也支持 .txt/.md。</span>
      </button>
      <button class="choice-card" type="button" data-import-mode="url">
        <strong>公众号链接导入</strong>
        <span>粘贴公开可访问的公众号文章链接，自动抓取正文。</span>
      </button>
    </div>
  `;
}

function renderWordExemplarImportForm() {
  return `
    <div id="exemplarImportStatus" class="import-status" hidden></div>
    <button class="mini ghost import-back-button" type="button" data-import-back="true">返回选择方式</button>
    <section class="import-panel single">
      <h3>Word 导入</h3>
      <p>支持 .docx，也支持 .txt/.md。老式 .doc 请先另存为 .docx。</p>
      <label>
        <span>范文来源/名称</span>
        <input id="wordExemplarSource" type="text" placeholder="例如：某某小学六一活动推文">
      </label>
      <label>
        <span>分类</span>
        ${renderExemplarCategorySelect("wordExemplarCategory")}
      </label>
      <label class="upload-card compact-upload">
        <input id="wordExemplarFile" type="file" accept=".docx,.txt,.md">
        <strong>选择 Word 范文</strong>
        <span id="wordExemplarFileName">尚未选择文件</span>
      </label>
      <button id="wordImportButton" type="button">导入 Word 范文</button>
    </section>
  `;
}

function renderUrlExemplarImportForm() {
  return `
    <div id="exemplarImportStatus" class="import-status" hidden></div>
    <button class="mini ghost import-back-button" type="button" data-import-back="true">返回选择方式</button>
    <section class="import-panel single">
      <h3>公众号链接导入</h3>
      <p>粘贴公开可访问的公众号文章链接，系统会抓取正文并加入范文库。</p>
      <label>
        <span>公众号文章链接</span>
        <input id="urlExemplarInput" type="url" placeholder="https://mp.weixin.qq.com/s/...">
      </label>
      <label>
        <span>范文来源/名称</span>
        <input id="urlExemplarSource" type="text" placeholder="留空则使用文章标题">
      </label>
      <label>
        <span>分类</span>
        ${renderExemplarCategorySelect("urlExemplarCategory")}
      </label>
      <button id="urlImportButton" type="button">导入公众号链接</button>
    </section>
  `;
}

function setExemplarImportModalBody(mode = "choice") {
  const body = document.querySelector(".exemplar-import-modal .import-dialog-body");
  if (!body) return;
  if (mode === "word") {
    body.innerHTML = renderWordExemplarImportForm();
    bindExemplarImportEvents();
    document.querySelector("#wordExemplarSource")?.focus();
    return;
  }
  if (mode === "url") {
    body.innerHTML = renderUrlExemplarImportForm();
    bindExemplarImportEvents();
    document.querySelector("#urlExemplarInput")?.focus();
    return;
  }
  body.innerHTML = renderExemplarImportChoice();
  bindExemplarImportChoiceEvents();
}

function openExemplarImportModal() {
  closeTemplatePreview();
  const modal = document.createElement("div");
  modal.className = "preview-modal exemplar-import-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-close="true"></div>
    <section class="preview-dialog import-dialog" role="dialog" aria-modal="true" aria-label="添加范文">
      <header class="preview-header">
        <div>
          <p class="step-count">添加范文</p>
          <h2>导入参考范文</h2>
        </div>
        <button class="mini ghost" type="button" data-close="true">关闭</button>
      </header>
      <div class="import-dialog-body"></div>
    </section>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", (event) => {
    if (event.target.dataset.close) {
      closeTemplatePreview();
    }
  });
  setExemplarImportModalBody("choice");
}

function bindExemplarImportChoiceEvents() {
  document.querySelectorAll("[data-import-mode]").forEach((button) => {
    button.addEventListener("click", () => setExemplarImportModalBody(button.dataset.importMode));
  });
}

function bindExemplarImportEvents() {
  document.querySelector("[data-import-back]")?.addEventListener("click", () => setExemplarImportModalBody("choice"));
  const fileInput = document.querySelector("#wordExemplarFile");
  fileInput?.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    document.querySelector("#wordExemplarFileName").textContent = file ? file.name : "尚未选择文件";
    if (file && !document.querySelector("#wordExemplarSource").value.trim()) {
      document.querySelector("#wordExemplarSource").value = file.name.replace(/\.(docx|txt|md)$/i, "");
    }
  });
  document.querySelector("#wordImportButton")?.addEventListener("click", importWordExemplar);
  document.querySelector("#urlImportButton")?.addEventListener("click", importUrlExemplar);
}

function bindStyleLibraryEvents() {
  document.querySelector("#openExemplarImportButton")?.addEventListener("click", openExemplarImportModal);
  document.querySelector("#emptyAddExemplarButton")?.addEventListener("click", openExemplarImportModal);
  document.querySelectorAll("[data-exemplar-detail]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openExemplarDetail(button.dataset.exemplarDetail);
    });
  });
  document.querySelectorAll("[data-exemplar-delete]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteExemplar(button.dataset.exemplarDelete);
    });
  });
  document.querySelectorAll("[data-exemplar-card]").forEach((card) => {
    card.addEventListener("click", () => openExemplarDetail(card.dataset.exemplarCard));
  });
}

async function importWordExemplar() {
  const file = document.querySelector("#wordExemplarFile")?.files?.[0];
  if (!file) {
    setMessage("请先选择一篇 Word 范文。", "error");
    return;
  }
  const formData = new FormData();
  formData.append("file", file, file.name);
  formData.append("source", document.querySelector("#wordExemplarSource")?.value.trim() || file.name);
  formData.append("category", document.querySelector("#wordExemplarCategory")?.value || "general");
  await submitExemplarImport("/api/exemplars/upload", { method: "POST", body: formData }, "正在导入 Word 范文...");
}

async function importUrlExemplar() {
  const url = document.querySelector("#urlExemplarInput")?.value.trim() || "";
  if (!url) {
    setMessage("请填写公众号文章链接。", "error");
    document.querySelector("#urlExemplarInput")?.focus();
    return;
  }
  const payload = {
    url,
    source: document.querySelector("#urlExemplarSource")?.value.trim() || "",
    category: document.querySelector("#urlExemplarCategory")?.value || "general",
  };
  await submitExemplarImport(
    "/api/exemplars/from-url",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "正在抓取公众号文章..."
  );
}

async function submitExemplarImport(url, options, loadingText) {
  const buttons = [
    document.querySelector("#wordImportButton"),
    document.querySelector("#urlImportButton"),
  ].filter(Boolean);
  try {
    buttons.forEach((button) => {
      button.disabled = true;
    });
    showImportStatus(loadingText);
    setMessage(loadingText);
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "范文导入失败。");
    }
    state.exemplars = Array.isArray(data.exemplars) ? data.exemplars : [];
    state.exemplarsLoaded = true;
    closeTemplatePreview();
    await renderStyleLibraryPage(`范文已导入：${data.imported?.source || data.imported?.file || "已加入范文库"}`);
  } catch (error) {
    showImportStatus(error.message, "error");
    setMessage(error.message, "error");
  } finally {
    buttons.forEach((button) => {
      button.disabled = false;
    });
  }
}

async function openExemplarDetail(filename) {
  if (!filename) return;
  try {
    setMessage("正在读取范文详情...");
    const data = await fetchJson(`/api/exemplars/detail?file=${encodeURIComponent(filename)}`);
    renderExemplarDetailModal(data.exemplar);
    setMessage("范文详情已打开。", "ok");
  } catch (error) {
    setMessage(error.message, "error");
  }
}

function renderExemplarDetailModal(item) {
  const metrics = item.metrics || {};
  const learned = item.learned || {};
  const vocab = metrics.vocab_temperature || {};
  const modal = document.createElement("div");
  modal.className = "preview-modal exemplar-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-close="true"></div>
    <section class="preview-dialog exemplar-dialog" role="dialog" aria-modal="true" aria-label="范文详情">
      <header class="preview-header">
        <div>
          <p class="eyebrow">Exemplar Detail</p>
          <h2>${escapeHtml(item.source || item.file || "范文详情")}</h2>
        </div>
        <button class="mini ghost" type="button" data-close="true">关闭</button>
      </header>
      <div class="exemplar-detail-body">
        <section class="detail-section">
          <h3>基本信息</h3>
          <div class="summary-box">
            <p><span>文件</span><strong>${escapeHtml(item.file || "")}</strong></p>
            <p><span>分类</span><strong>${escapeHtml(item.category || "general")}</strong></p>
            <p><span>提取日期</span><strong>${escapeHtml(item.extracted_at || "未记录")}</strong></p>
            <p><span>风格分数</span><strong>${escapeHtml(item.humanness_score ?? "未评分")}</strong></p>
          </div>
        </section>
        <section class="detail-section">
          <h3>已学习到的写作倾向</h3>
          <div class="learned-grid">
            <p><span>人格倾向</span><strong>${escapeHtml(learned.persona || "通用编辑")}</strong></p>
            <p><span>写作语气</span><strong>${escapeHtml(learned.tone || "语气较均衡")}</strong></p>
            <p><span>风格特征</span><strong>${escapeHtml((learned.style || []).join("、") || "保留基础表达节奏")}</strong></p>
          </div>
        </section>
        <section class="detail-section">
          <h3>风格指纹</h3>
          <div class="metric-grid">
            <p><span>句长波动</span><strong>${escapeHtml(metrics.sentence_stddev ?? "未记录")}</strong></p>
            <p><span>段落变化</span><strong>${escapeHtml(metrics.paragraph_cv ?? "未记录")}</strong></p>
            <p><span>短段落数</span><strong>${escapeHtml(metrics.short_paragraphs ?? "未记录")}</strong></p>
            <p><span>负向情绪占比</span><strong>${escapeHtml(metrics.negative_ratio ?? "未记录")}</strong></p>
            <p><span>词汇温度</span><strong>${escapeHtml(formatVocabTemperature(vocab))}</strong></p>
          </div>
        </section>
        <section class="detail-section">
          <h3>范文内容</h3>
          <pre class="exemplar-content">${escapeHtml(item.content || "暂无内容")}</pre>
        </section>
      </div>
    </section>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", (event) => {
    if (event.target.closest("[data-close]")) {
      modal.remove();
    }
  });
}

function formatVocabTemperature(vocab) {
  const entries = Object.entries(vocab || {});
  if (!entries.length) return "未记录";
  return entries.map(([key, value]) => `${key}: ${value}`).join(" / ");
}

async function deleteExemplar(filename) {
  if (!filename) return;
  const item = state.exemplars.find((exemplar) => exemplar.file === filename);
  const label = item ? `${item.source || item.file}` : filename;
  if (!confirm(`确定删除这篇范文吗？\n\n${label}\n\n删除后，新建文章时将不能再参考它。`)) {
    return;
  }
  try {
    showImportStatus("正在删除范文...");
    const data = await fetchJson("/api/exemplars/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file: filename }),
    });
    state.exemplars = Array.isArray(data.exemplars) ? data.exemplars : [];
    state.exemplarsLoaded = true;
    if (state.articleOptions.exemplarFile === filename) {
      state.articleOptions.exemplarFile = "auto";
      saveArticleOptions();
    }
    await renderStyleLibraryPage(`已删除范文：${label}`);
  } catch (error) {
    showImportStatus(error.message, "error");
    setMessage(error.message, "error");
  }
}

function renderExemplarCard(item) {
  const score = item.humanness_score === null || item.humanness_score === undefined ? "未评分" : item.humanness_score;
  return `
    <article class="style-card" data-exemplar-card="${escapeAttr(item.file || "")}">
      <div class="style-card-head">
        <strong>${escapeHtml(item.file || "未命名范文")}</strong>
        <span>${escapeHtml(item.category || "general")}</span>
      </div>
      <p class="style-meta">
        <span>来源：${escapeHtml(item.source || "未记录")}</span>
        <span>日期：${escapeHtml(item.extracted_at || "未记录")}</span>
        <span>分数：${escapeHtml(score)}</span>
      </p>
      <p class="style-snippet">${escapeHtml(item.snippet || "暂无片段")}</p>
      <div class="style-card-actions">
        <button class="mini ghost" type="button" data-exemplar-detail="${escapeAttr(item.file || "")}">查看详情</button>
        <button class="mini danger" type="button" data-exemplar-delete="${escapeAttr(item.file || "")}">删除</button>
      </div>
    </article>
  `;
}

function formatHistoryTime(value) {
  const dateValue = new Date(value);
  if (Number.isNaN(dateValue.getTime())) return value || "时间未记录";
  return dateValue.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

const editRuleTypeLabels = {
  title: "标题",
  tone: "语气",
  structure: "结构",
  length: "篇幅",
  wording: "措辞",
  opening: "开头",
  ending: "结尾",
  format: "格式",
};

function renderLearnedEditRules(rules) {
  return `
    <section class="history-learning-panel">
      <div class="history-learning-head">
        <div>
          <p class="step-count">持续学习</p>
          <h2>已学习的写作偏好</h2>
          <p class="hint">同步你在微信草稿箱中的修改后，这些偏好会自动用于以后写稿。</p>
        </div>
        <strong>${rules.length} 条规则</strong>
      </div>
      ${rules.length ? `
        <div class="learning-rule-list">
          ${rules.map((item) => `
            <div class="learning-rule-row">
              <div>
                <span>${escapeHtml(editRuleTypeLabels[item.type] || "写作")}</span>
                <strong>${escapeHtml(item.rule || "")}</strong>
                <small>已观察 ${Number(item.occurrences || 1)} 次 · 可信度 ${Math.round(Number(item.confidence || 0) * 100)}%</small>
              </div>
              <button class="mini danger" type="button" data-learning-rule-delete="${escapeAttr(item.id || "")}">删除</button>
            </div>
          `).join("")}
        </div>
      ` : `
        <div class="learning-empty">
          <strong>还没有学习记录</strong>
          <span>把文章推送到微信并完成修改后，回到下方文章记录点击“同步修改并学习”。</span>
        </div>
      `}
    </section>
  `;
}

async function renderDraftHistoryPage() {
  state.phase = "history";
  updateNav("history");
  setHeader("草稿历史", "生成过的文章会自动保存在这台电脑上，刷新页面后也可以回来继续查看。");
  els.progressBar.style.width = "100%";
  els.backButton.disabled = true;
  els.skipButton.hidden = true;
  els.nextButton.hidden = true;
  els.nextButton.disabled = true;
  els.panel.innerHTML = `
    <p class="step-count">本地记录</p>
    <h2>正在读取草稿历史...</h2>
  `;
  setMessage("");
  try {
    const [data, learning] = await Promise.all([
      fetchJson("/api/draft-history"),
      fetchJson("/api/edit-learning"),
    ]);
    const history = Array.isArray(data.history) ? data.history : [];
    const rules = Array.isArray(learning.rules) ? learning.rules : [];
    state.draftHistory = history;
    state.editLearning = learning;
    els.panel.innerHTML = `
      <div class="history-head">
        <div>
          <p class="step-count">共 ${history.length} 篇</p>
          <h2>最近生成的文章</h2>
          <p class="hint">这里保存的是本机草稿。已推送到微信的文章仍需在公众号后台完成最终发布。</p>
        </div>
        <button id="historyNewArticleButton" type="button">新建文章</button>
      </div>
      ${renderLearnedEditRules(rules)}
      <div class="draft-history-list">
        ${history.length ? history.map((item) => `
          <article class="draft-history-card">
            <div>
              <span class="history-status ${item.status === "wechat" ? "pushed" : ""}">
                ${item.status === "wechat" ? "已推送到微信" : "本地草稿"}
              </span>
              <h3>${escapeHtml(item.title || "未命名文章")}</h3>
              <p>${escapeHtml(item.digest || "暂无摘要")}</p>
              <small>${escapeHtml(formatHistoryTime(item.created_at))}</small>
            </div>
            <div class="history-card-actions">
              <button class="mini ghost" type="button" data-history-open="${escapeAttr(item.id || "")}">打开预览</button>
              ${item.status === "wechat" && item.media_id ? `
                <button class="mini primary" type="button" data-history-learn="${escapeAttr(item.id || "")}">
                  ${item.learning_status === "learned" ? "再次同步修改" : item.learning_status === "unchanged" ? "再次检查修改" : "同步修改并学习"}
                </button>
              ` : ""}
              <button class="mini danger" type="button" data-history-delete="${escapeAttr(item.id || "")}">删除</button>
            </div>
          </article>
        `).join("") : `
          <section class="empty-state">
            <strong>还没有生成过文章</strong>
            <p>完成第一篇文章后，它会自动出现在这里。即使刷新网页，也不会再找不到刚才的草稿。</p>
            <button id="emptyHistoryNewButton" type="button">创建第一篇文章</button>
          </section>
        `}
      </div>
    `;
    document.querySelector("#historyNewArticleButton")?.addEventListener("click", requestNewArticle);
    document.querySelector("#emptyHistoryNewButton")?.addEventListener("click", requestNewArticle);
    document.querySelectorAll("[data-history-open]").forEach((button) => {
      button.addEventListener("click", () => openDraftHistory(button.dataset.historyOpen));
    });
    document.querySelectorAll("[data-history-learn]").forEach((button) => {
      button.addEventListener("click", () => learnWechatDraftEdits(button.dataset.historyLearn, button));
    });
    document.querySelectorAll("[data-history-delete]").forEach((button) => {
      button.addEventListener("click", () => deleteDraftHistoryRecord(button.dataset.historyDelete));
    });
    document.querySelectorAll("[data-learning-rule-delete]").forEach((button) => {
      button.addEventListener("click", () => deleteLearnedEditRule(button.dataset.learningRuleDelete));
    });
    setMessage(history.length ? "草稿历史读取完成。" : "");
  } catch (error) {
    els.panel.innerHTML = `<div class="note error-note">${escapeHtml(error.message)}</div>`;
    setMessage(error.message, "error");
  }
}

async function deleteDraftHistoryRecord(recordId) {
  if (!recordId) return;
  const record = state.draftHistory.find((item) => item.id === recordId);
  const remoteNote = record?.status === "wechat"
    ? "\n\n这只会删除本机记录，不会删除微信公众号后台中的草稿。"
    : "";
  if (!confirm(`确定删除这篇本地草稿吗？\n\n${record?.title || "未命名文章"}${remoteNote}`)) return;
  try {
    const data = await fetchJson("/api/draft-history/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history_id: recordId }),
    });
    if (state.generatedDraft?.history_id === recordId) {
      state.generatedDraft = null;
      state.articleWorkspacePhase = "";
      clearCurrentArticleSession();
    }
    await renderDraftHistoryPage();
    setMessage(`已删除草稿：${data.title || record?.title || "未命名文章"}`, "ok");
  } catch (error) {
    setMessage(error.message, "error");
  }
}

async function learnWechatDraftEdits(recordId, button) {
  if (!recordId || !button) return;
  const originalText = button.textContent;
  try {
    button.disabled = true;
    button.textContent = "正在同步...";
    setMessage("正在读取微信草稿并分析你的修改，通常需要几十秒。");
    const data = await fetchJson("/api/draft-history/learn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history_id: recordId }),
    });
    await renderDraftHistoryPage();
    showEditLearningResult(data);
    setMessage(data.changed ? "已学习本次草稿修改。" : "微信草稿与本地初稿一致，没有新增规则。", "ok");
  } catch (error) {
    button.disabled = false;
    button.textContent = originalText;
    showInlineUserError(button.closest(".draft-history-card"), error, "同步微信修改失败。");
  }
}

function showEditLearningResult(data) {
  const rules = Array.isArray(data.rules) ? data.rules : [];
  const diff = data.diff || {};
  const modal = document.createElement("div");
  modal.className = "preview-modal edit-learning-modal";
  modal.innerHTML = `
    <div class="preview-backdrop" data-close="true"></div>
    <section class="preview-dialog learning-result-dialog" role="dialog" aria-modal="true" aria-label="编辑学习结果">
      <header class="learning-result-head">
        <p class="step-count">${data.already_synced ? "已同步过" : data.changed ? "学习完成" : "没有发现修改"}</p>
        <h2>${data.changed ? "已读懂这次修改" : "当前版本没有新变化"}</h2>
        <p>${escapeHtml(data.summary || "")}</p>
      </header>
      <div class="learning-diff-summary">
        <p><span>标题</span><strong>${diff.title_changed ? "有修改" : "未修改"}</strong></p>
        <p><span>正文增减</span><strong>${Number(diff.char_delta || 0) > 0 ? "+" : ""}${Number(diff.char_delta || 0)} 字</strong></p>
        <p><span>新增内容</span><strong>${Number(diff.lines_added || 0)} 处</strong></p>
        <p><span>删除内容</span><strong>${Number(diff.lines_deleted || 0)} 处</strong></p>
      </div>
      <div class="learning-result-rules">
        <h3>${rules.length ? `学到 ${rules.length} 条可复用偏好` : "没有形成长期偏好"}</h3>
        ${rules.length ? rules.map((item) => `
          <div>
            <span>${escapeHtml(editRuleTypeLabels[item.type] || "写作")}</span>
            <strong>${escapeHtml(item.rule || "")}</strong>
            ${item.evidence ? `<small>${escapeHtml(item.evidence)}</small>` : ""}
          </div>
        `).join("") : `<p>本次变化更像是针对这篇文章的内容调整，因此不会影响以后写稿。</p>`}
      </div>
      <footer class="learning-result-actions">
        <button class="primary" type="button" data-close="true">完成</button>
      </footer>
    </section>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", (event) => {
    if (event.target.closest("[data-close='true']") || event.target === modal) modal.remove();
  });
}

async function deleteLearnedEditRule(ruleId) {
  if (!ruleId) return;
  const item = (state.editLearning?.rules || []).find((rule) => rule.id === ruleId);
  if (!confirm(`删除这条写作偏好吗？\n\n${item?.rule || ""}\n\n删除后，后续生成文章将不再使用它。`)) return;
  try {
    await fetchJson("/api/edit-learning/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rule_id: ruleId }),
    });
    await renderDraftHistoryPage();
    setMessage("已删除这条学习规则。", "ok");
  } catch (error) {
    setMessage(error.message, "error");
  }
}

async function openDraftHistory(recordId) {
  if (!recordId) return;
  try {
    setMessage("正在打开本地草稿...");
    const data = await fetchJson(`/api/draft-history/detail?id=${encodeURIComponent(recordId)}`);
    state.generatedDraft = {
      ...data,
      history_id: data.record?.id || recordId,
    };
    state.articleOptions.template = data.article?.template || state.articleOptions.template;
    saveArticleOptions();
    renderGeneratedDraft(state.generatedDraft);
    setMessage("已从本地草稿历史恢复文章。", "ok");
  } catch (error) {
    setMessage(error.message, "error");
  }
}

function goBack() {
  if (state.phase === "settings") {
    return;
  }
  if (state.phase === "styles") {
    return;
  }
  if (state.phase === "history") {
    return;
  }
  if (state.phase === "setup") {
    if (state.current === 0) return;
    state.current -= 1;
    renderSetupStep();
    setMessage("");
    return;
  }
  if (state.phase === "materials") {
    if (state.materials) {
      renderMaterialsSummary({ saved_count: state.selectedFiles.length, materials: state.materials });
    } else {
      state.phase = "article";
      state.current = articleSteps.length - 1;
      renderArticleStep();
      setMessage("");
    }
    return;
  }
  if (state.phase === "requirements") {
    renderArticleForm();
    setMessage("");
    return;
  }
  if (state.phase === "draftReady") {
    renderWritingRequestForm();
    setMessage("");
    return;
  }
  if (state.phase === "generating") {
    return;
  }
  if (state.phase === "generated") {
    renderDraftReadySummary();
    setMessage("");
    return;
  }
  if (state.phase === "article") {
    if (state.current === 0) return;
    state.current -= 1;
    renderArticleStep();
    setMessage("");
  }
}

function bindEvents() {
  els.navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (state.firstVisit) {
        renderSettingsPage();
        setMessage("请先完成首次设置，再开始使用其他功能。", "error");
        return;
      }
      if (!isSetupReady()) {
        renderSettingsPage();
        setMessage("请先补齐 AppID、AppSecret 和 AI 写稿 API Key，完成后才能使用这个功能。", "error");
        return;
      }
      if (!isStyleReady()) {
        renderSettingsPage();
        setMessage("请先补齐公众号名称、行业/机构类型、主要内容方向和文章风格，完成后才能使用这个功能。", "error");
        return;
      }
      if (button.dataset.page === "styles") {
        renderStyleLibraryPage();
      } else if (button.dataset.page === "article") {
        restoreArticleWorkspace();
      } else if (button.dataset.page === "history") {
        renderDraftHistoryPage();
      }
    });
  });
  els.settingsButton.addEventListener("click", () => {
    if (state.firstVisit) renderSettingsPage();
    else openSettingsOverlay();
  });
  els.newArticleButton?.addEventListener("click", () => {
    if (state.firstVisit || !isSetupReady() || !isStyleReady()) {
      renderSettingsPage();
      setMessage("请先完成设置，再新建文章。", "error");
      return;
    }
    requestNewArticle();
  });
  els.backButton.addEventListener("click", goBack);
  els.skipButton.addEventListener("click", () => saveSetupAndNext(true));
  els.nextButton.addEventListener("click", () => {
    if (state.phase === "settings") {
      saveSettingsPage();
    } else if (state.phase === "setup") {
      saveSetupAndNext(false);
    } else if (state.phase === "article") {
      saveArticleAndNext();
    } else if (state.phase === "articleForm") {
      if (state.useMaterials && !state.materials) {
        setMessage("你开启了素材导入，请先上传并识别素材，或关闭素材导入开关。", "error");
        document.querySelector("#materialsUploadWrap")?.scrollIntoView({ behavior: "smooth", block: "center" });
        return;
      }
      renderWritingRequestForm();
    } else if (state.phase === "materials") {
      if (state.materials) {
        renderWritingRequestForm();
      } else {
        uploadMaterials();
      }
    } else if (state.phase === "requirements") {
      if (collectWritingRequest()) {
        renderDraftReadySummary();
      }
    } else if (state.phase === "draftReady" || state.phase === "generated") {
      generateDraftPreview();
    }
  });
}

async function init() {
  try {
    const [configData, styleData] = await Promise.all([
      fetchJson("/api/config"),
      fetchJson("/api/style"),
    ]);
    state.config = configData.config;
    state.style = styleData.style;
    updateStatus();
    bindEvents();
    if (isSettingsEmbed) {
      document.body.classList.add("settings-embed");
      renderSettingsPage();
    } else if (state.firstVisit || !isSetupReady() || !isStyleReady()) {
      renderSettingsPage();
    } else if (restoredArticleSession?.phase) {
      restoreArticleWorkspace();
    } else {
      startArticleWizard();
    }
  } catch (error) {
    setMessage(error.message, "error");
  }
}

init();
