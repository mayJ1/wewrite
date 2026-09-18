import { chromium } from "playwright";

const chromePath = process.env.CHROME_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const appUrl = process.env.APP_URL || "http://127.0.0.1:8770/";

const browser = await chromium.launch({
  headless: true,
  executablePath: chromePath,
});

try {
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
  await page.goto(appUrl, { waitUntil: "networkidle" });

  await page.waitForSelector(".onboarding-banner");
  const onboardingTitle = await page.locator("#mainTitle").textContent();
  if (onboardingTitle !== "欢迎使用 WeWrite") {
    throw new Error("First visit should open the guided settings experience.");
  }
  await page.evaluate(() => localStorage.setItem("wewriteOnboardingComplete", "true"));
  await page.reload({ waitUntil: "networkidle" });

  const brand = await page.locator(".top-nav-inner strong").textContent();
  if (brand !== "WeWrite") {
    throw new Error(`Unexpected product name: ${brand}`);
  }

  const navTexts = await page.locator(".nav-button").allTextContents();
  if (navTexts.includes("配置账号")) {
    throw new Error("Configuration should be behind the settings button, not a main nav item.");
  }
  if (!navTexts.includes("范文学习") || !navTexts.includes("文章工作台") || !navTexts.includes("草稿历史")) {
    throw new Error("Missing style-library navigation item.");
  }
  if ((await page.locator("#newArticleButton").count()) !== 1) {
    throw new Error("Top navigation should expose a separate explicit new-article action.");
  }

  await page.locator("#settingsButton").click();
  await page.waitForSelector("#settingsFrame");
  const settingsFrame = page.frameLocator("#settingsFrame");
  await settingsFrame.locator(".config-status-list").first().waitFor();
  const configRowCount = await settingsFrame.locator(".config-status-list").first().locator(".config-status-row").count();
  const configModifyCount = await settingsFrame.locator("[data-config-edit]").count();
  const configInputCount = await settingsFrame.locator(".config-status-list").first().locator(".config-status-row input").count();
  const styleRowCount = await settingsFrame.locator(".style-config-list .config-status-row").count();
  const styleModifyCount = await settingsFrame.locator("[data-style-edit]").count();
  const styleInputCount = await settingsFrame.locator(".style-config-list input, .style-config-list textarea, .style-config-list select").count();
  if (configRowCount !== 4 || configModifyCount + configInputCount !== 4 || styleRowCount < 13 || styleModifyCount + styleInputCount !== styleRowCount) {
    throw new Error("Settings page should show API config and style initialization fields.");
  }
  if ((await settingsFrame.locator(".questionnaire-list").count()) !== 1) {
    throw new Error("Account style initialization should use the questionnaire UI.");
  }
  if (configModifyCount > 0) {
    await settingsFrame.locator("[data-config-edit]").first().click();
    await settingsFrame.locator(".config-edit-modal #configEditInput").waitFor();
    await settingsFrame.locator(".config-edit-modal button[data-close='true']").first().click();
  }
  const imageConfigButton = settingsFrame.locator("[data-config-edit='image_api']");
  if (await imageConfigButton.count()) {
    await imageConfigButton.click();
    await settingsFrame.locator(".config-edit-modal #configImageProvider").waitFor();
    const providerValue = await settingsFrame.locator("#configImageProvider").inputValue();
    const modelValue = await settingsFrame.locator("#configImageModel").inputValue();
    if (!["doubao", "agnes"].includes(providerValue) || !modelValue) {
      throw new Error("Image API settings should include provider and model.");
    }
    await settingsFrame.locator(".config-edit-modal button[data-close='true']").first().click();
  }
  if (styleModifyCount > 0) {
    await settingsFrame.locator("[data-style-edit]").first().click();
    await settingsFrame.locator(".config-edit-modal #styleEditInput").waitFor();
    await settingsFrame.locator(".config-edit-modal button[data-close='true']").first().click();
  }
  await page.locator(".settings-overlay-head [data-settings-close='true']").click();
  await page.waitForSelector(".settings-overlay-modal", { state: "detached" });

  await page.getByRole("button", { name: "范文学习" }).click();
  await page.waitForSelector("#openExemplarImportButton");
  if (await page.locator("#nextButton").isVisible()) {
    throw new Error("Style learning page should not show the unused bottom action button.");
  }

  const title = await page.locator("#mainTitle").textContent();
  const cardCount = await page.locator(".style-card").count();
  const inlineImportGridCount = await page.locator("#questionPanel .exemplar-import-grid").count();
  if (inlineImportGridCount !== 0) {
    throw new Error("Style library should keep exemplar import forms inside the Add Exemplar modal.");
  }
  await page.locator("#openExemplarImportButton").click();
  await page.waitForSelector(".exemplar-import-modal .import-choice-grid");
  const importChoiceCount = await page.locator(".exemplar-import-modal [data-import-mode]").count();
  if (importChoiceCount !== 2) {
    throw new Error("Add Exemplar modal should first ask the user to choose an import mode.");
  }
  await page.locator(".exemplar-import-modal [data-import-mode='word']").click();
  await page.waitForSelector(".exemplar-import-modal #wordImportButton");
  const importPanelCount = await page.locator(".exemplar-import-modal .import-panel").count();
  if (importPanelCount !== 1) {
    throw new Error("Add Exemplar modal should show only the selected import panel.");
  }
  await page.locator(".exemplar-import-modal button[data-close='true']").click();
  const draftHistoryPattern = /\/api\/draft-history$/;
  const draftHistoryDetailPattern = /\/api\/draft-history\/detail\?id=history-test-1$/;
  const deleteDraftPattern = /\/api\/draft-history\/delete$/;
  const editLearningPattern = /\/api\/edit-learning$/;
  const learnDraftPattern = /\/api\/draft-history\/learn$/;
  const mockRule = {
    id: "rule-test-1",
    key: "shorter_paragraphs",
    type: "length",
    rule: "正文每段尽量控制在三句话以内。",
    evidence: "用户拆分并删减了长段落。",
    confidence: 0.72,
    occurrences: 1,
  };
  let mockHistory = [{
    id: "history-test-1",
    title: "编辑学习测试",
    digest: "验证微信草稿修改学习入口。",
    created_at: "2026-06-30T12:00:00",
    status: "wechat",
    media_id: "media-test-1",
  }];
  await page.route(draftHistoryPattern, (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ history: mockHistory }),
  }));
  await page.route(editLearningPattern, (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ rules: [mockRule], sessions: [], rule_count: 1, session_count: 1 }),
  }));
  await page.route(draftHistoryDetailPattern, (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      ok: true,
      record: { id: "history-test-1", status: "wechat", media_id: "media-test-1" },
      article: {
        template: "studio-brief",
        meta: { title: "历史草稿图片恢复测试", digest: "验证正文图片可以重新选择为封面。" },
        headline: { title: "历史草稿图片恢复测试", body: ["测试正文。"] },
        sections: [{
          cn: "活动现场",
          blocks: [
            {
              type: "image",
              url: "C:\\fake\\history-photo-1.jpg",
              local_path: "C:\\fake\\history-photo-1.jpg",
              preview_url: "/static/template-previews/studio-brief.png",
              caption: "历史正文图片一",
            },
            {
              type: "image",
              url: "C:\\fake\\history-photo-2.jpg",
              local_path: "C:\\fake\\history-photo-2.jpg",
              preview_url: "/static/template-previews/neo-brutalism.png",
              caption: "历史正文图片二",
            },
          ],
        }],
      },
      html: "<main><h1>历史草稿图片恢复测试</h1><p>测试正文。</p></main>",
      errors: [],
      warnings: [],
      user_issues: { errors: [], warnings: [] },
    }),
  }));
  await page.route(learnDraftPattern, (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      ok: true,
      changed: true,
      already_synced: false,
      summary: "用户缩短了段落，并把标题改得更直接。",
      rules: [mockRule],
      diff: {
        title_changed: true,
        char_delta: -86,
        lines_added: 2,
        lines_deleted: 4,
      },
    }),
  }));
  await page.route(deleteDraftPattern, async (route) => {
    const payload = route.request().postDataJSON();
    const deleted = mockHistory.find((item) => item.id === payload.history_id);
    mockHistory = mockHistory.filter((item) => item.id !== payload.history_id);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        record_id: payload.history_id,
        title: deleted?.title || "未命名文章",
        deleted_files: ["draft.json", "draft.html"],
      }),
    });
  });
  await page.getByRole("button", { name: "草稿历史" }).click();
  await page.waitForSelector("#historyNewArticleButton");
  if ((await page.locator(".draft-history-list").count()) !== 1) {
    throw new Error("Draft history page should render a local history list.");
  }
  const learnedRuleCount = await page.locator(".learning-rule-row").count();
  const learnButtonCount = await page.locator("[data-history-learn]").count();
  if (learnedRuleCount !== 1 || learnButtonCount !== 1) {
    throw new Error("Draft history should show learned preferences and a WeChat sync action.");
  }
  await page.locator("[data-history-learn]").click();
  await page.waitForSelector(".learning-result-dialog");
  const learningResultRuleCount = await page.locator(".learning-result-rules > div").count();
  if (learningResultRuleCount !== 1) {
    throw new Error("Edit learning result should explain the reusable rules it learned.");
  }
  await page.locator(".learning-result-actions [data-close='true']").click();
  await page.locator("[data-history-open='history-test-1']").click();
  await page.waitForSelector(".image-workflow");
  const restoredHistoryCoverCandidateCount = await page.locator(".cover-candidate").count();
  if (restoredHistoryCoverCandidateCount !== 2) {
    throw new Error("Opening a draft from history should rebuild cover candidates from article body images.");
  }
  await page.locator("#settingsButton").click();
  await page.waitForSelector("#settingsFrame");
  await page.locator(".settings-overlay-head [data-settings-close='true']").click();
  await page.waitForSelector(".settings-overlay-modal", { state: "detached" });
  if ((await page.locator(".cover-candidate").count()) !== 2) {
    throw new Error("Closing settings should preserve the exact generated article workspace.");
  }
  await page.getByRole("button", { name: "范文学习" }).click();
  await page.waitForSelector("#openExemplarImportButton");
  await page.getByRole("button", { name: "文章工作台" }).click();
  await page.waitForSelector(".image-workflow");
  if ((await page.locator(".cover-candidate").count()) !== 2) {
    throw new Error("Returning to the article workspace should restore the current generated draft.");
  }
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector(".image-workflow");
  const restoredAfterReload = (await page.locator(".cover-candidate").count()) === 2;
  if (!restoredAfterReload) {
    throw new Error("The current generated article should survive a page reload.");
  }
  await page.getByRole("button", { name: "草稿历史" }).click();
  await page.waitForSelector("[data-history-delete='history-test-1']");
  page.once("dialog", (dialog) => dialog.accept());
  await page.locator("[data-history-delete='history-test-1']").click();
  await page.waitForFunction(() => document.querySelectorAll(".draft-history-card").length === 0);
  const draftDeleteWorks = (await page.locator(".draft-history-card").count()) === 0;
  if (!draftDeleteWorks) {
    throw new Error("Deleting a history record should remove it from the local draft list.");
  }
  await page.unroute(draftHistoryPattern);
  await page.unroute(draftHistoryDetailPattern);
  await page.unroute(deleteDraftPattern);
  await page.unroute(editLearningPattern);
  await page.unroute(learnDraftPattern);
  await page.locator("#newArticleButton").click();
  await page.waitForSelector(".article-form");
  const selectedTemplateSummaryCount = await page.locator(".selected-template-summary").count();
  const inlineTemplateCardCount = await page.locator("#questionPanel .template-form-card").count();
  const articleTypeChoiceCount = await page.locator("[data-value='campus_activity']").count();
  const personaChoiceCount = await page.locator("[data-value='warm-editor']").count();
  if (
    selectedTemplateSummaryCount !== 1
    || inlineTemplateCardCount !== 0
    || articleTypeChoiceCount !== 0
    || personaChoiceCount !== 0
  ) {
    throw new Error("New article page should show one selected-template summary and no inline template gallery.");
  }
  await page.waitForSelector("#articleExemplarSelect");
  await page.waitForFunction(() => document.querySelectorAll("#articleExemplarSelect option").length >= 1);
  const exemplarOptionCount = await page.locator("#articleExemplarSelect option").count();
  if (exemplarOptionCount < 1) {
    throw new Error("Exemplar dropdown did not load exemplar options.");
  }
  await page.locator("#exemplarToggle + .switch-track").click();
  if (await page.locator("#exemplarPickerWrap").isVisible()) {
    throw new Error("Exemplar selector should hide when reference learning is disabled.");
  }
  await page.locator("#materialsToggle + .switch-track").click();
  if (!(await page.locator("#materialsUploadWrap").isVisible())) {
    throw new Error("Material upload controls should appear when import is enabled.");
  }
  const imageOptions = await page.locator("#articleImageMode option").allTextContents();
  if (imageOptions.join("|") !== "选择已有图片（在下方导入）|AI 生成|不使用") {
    throw new Error("Article image select should contain the requested three choices.");
  }
  await page.locator("#articleImageMode").selectOption("ai_generated");
  const aiImageMode = await page.evaluate(() => state.articleOptions.imageMode);
  if (aiImageMode !== "ai_generated") {
    throw new Error("AI image selection should use the ai_generated backend mode.");
  }
  const generationLabels = await page.evaluate(() => getGenerationSteps().map(([label]) => label));
  if (
    !generationLabels.includes("正在读取素材和写作要求")
    || !generationLabels.includes("正在撰写文章初稿")
    || !generationLabels.includes("正在套用模板排版")
  ) {
    throw new Error("Generation progress should expose clear user-facing stages.");
  }
  await page.locator("#browseTemplatesButton").click();
  await page.waitForSelector(".template-browser-modal");
  const templateCardCount = await page.locator(".template-browser-card").count();
  const templatePreviewButtonCount = await page.locator("[data-gallery-preview]").count();
  const templateSelectButtonCount = await page.locator("[data-gallery-select]").count();
  if (templateCardCount !== 9 || templatePreviewButtonCount !== 9 || templateSelectButtonCount !== 9) {
    throw new Error("Template browser modal should contain all 9 templates with preview and select actions.");
  }
  await page.locator("[data-gallery-preview='studio-brief']").click();
  await page.waitForSelector(".preview-modal .preview-large");
  await page.locator(".preview-modal button[data-close='true']").click();
  await page.locator("#browseTemplatesButton").click();
  await page.waitForSelector(".template-browser-modal");
  await page.locator("[data-gallery-select='daily-intelligence']").click();
  if ((await page.locator(".selected-template-summary").getByText("日报资讯", { exact: true }).count()) !== 1) {
    throw new Error("Selecting a template should update the selected-template summary.");
  }
  await page.evaluate(() => {
    state.selectedFiles = [
      { name: "activity.docx", webkitRelativePath: "materials/activity.docx" },
      { name: "scene.jpg", webkitRelativePath: "materials/photos/scene.jpg" },
    ];
    openMaterialsSuccessModal({
      materials: { stats: { total_docs: 1, total_photos: 1, total_chars: 320 } },
    });
  });
  await page.waitForSelector(".materials-success-modal");
  const uploadedFileRowCount = await page.locator(".uploaded-file-list > div").count();
  if (uploadedFileRowCount !== 2) {
    throw new Error("Material success modal should list uploaded files and types.");
  }
  await page.locator(".materials-success-modal button[data-close='true']").first().click();
  if (await page.locator("#materialsToggle").isChecked()) {
    await page.locator("#materialsToggle + .switch-track").click();
  }
  await page.getByRole("button", { name: "下一步：填写写作要求" }).click();
  await page.waitForSelector("#writingPromptInput");
  const writingControlCount = await page.locator("#questionPanel textarea, #questionPanel input, #questionPanel select").count();
  if (writingControlCount !== 1) {
    throw new Error(`Writing requirements page should contain exactly one form control, found ${writingControlCount}.`);
  }
  const legacyWritingControlCount = await page.locator(
    "#topicInput, #timeInput, #locationInput, #focusInput, #avoidInput",
  ).count();
  if (legacyWritingControlCount !== 0) {
    throw new Error("Legacy writing requirement fields should not be rendered.");
  }
  await page.locator("#writingPromptInput").fill(
    "帮我写一篇 AI 科技进校园活动报道，重点写学生互动体验和现场氛围，语气活泼简洁，不要编造学生原话。"
    + "文章需要面向学生家长，交代活动过程、参与方式和学习收获，但素材没有提供的数据一律不要自行补充。"
    + "标题要清楚自然，正文段落不要太长，避免空泛口号和过度抒情。\n"
    + "结尾简短收束，不需要重复全文内容。",
  );
  await page.getByRole("button", { name: "保存要求" }).click();
  await page.waitForSelector(".summary-box");
  if ((await page.getByText("提示词", { exact: true }).count()) < 1) {
    throw new Error("Draft-ready summary should show the single writing prompt.");
  }
  const promptWrapsInsideSummary = await page.locator(".prompt-summary span").evaluate((element) => (
    element.scrollWidth <= element.clientWidth
    && getComputedStyle(element).whiteSpace === "pre-wrap"
  ));
  if (!promptWrapsInsideSummary) {
    throw new Error("Writing prompt should wrap inside the confirmation panel.");
  }
  await page.locator("#backButton").click();
  await page.waitForSelector("#writingPromptInput");
  await page.locator("#backButton").click();
  await page.waitForSelector(".article-form");

  await page.evaluate(() => {
    state.articleOptions.imageMode = "both";
    state.useMaterials = true;
    state.materials = {
      photos: Array.from({ length: 7 }, (_, index) => ({
        filename: `sample-cover-${index + 1}.png`,
        url: `C:\\fake\\sample-cover-${index + 1}.png`,
        preview_url: "/static/template-previews/studio-brief.png",
        category: `素材封面 ${index + 1}`,
      })),
      stats: { total_photos: 7, total_chars: 500 },
    };
    state.generatedDraft = {
      ok: true,
      article: {
        meta: { title: "图片闭环测试", digest: "测试封面选择和推送前校验。" },
        headline: { title: "图片闭环测试", body: ["测试正文。"] },
        sections: [{
          cn: "活动回顾",
          image: {
            url: "C:\\fake\\ai-generated.png",
            local_path: "C:\\fake\\ai-generated.png",
            preview_url: "/static/template-previews/neo-brutalism.png",
            caption: "AI 活动插图",
            source: "ai",
          },
          blocks: [{ type: "image", url: "C:\\fake\\sample-cover.png", caption: "活动现场" }],
        }],
      },
      html: "<main><h1>图片闭环测试</h1><p>测试正文。</p></main>",
      errors: [],
      warnings: [],
      user_issues: { errors: [], warnings: [] },
      image_generation: { mode: "ai_generated", generated_count: 1 },
    };
    renderGeneratedDraft(state.generatedDraft);
  });
  await page.waitForSelector(".image-workflow");
  const coverCandidateCount = await page.locator(".cover-candidate").count();
  const pushDisabledBeforeCover = await page.locator("#pushDraftButton").isDisabled();
  if (coverCandidateCount !== 8 || !pushDisabledBeforeCover) {
    throw new Error("Image workflow should require a cover and show material cover candidates.");
  }
  const coverScrollBefore = await page.locator(".cover-candidate-strip").evaluate((element) => {
    element.scrollLeft = element.scrollWidth;
    return element.scrollLeft;
  });
  await page.locator(".cover-candidate").filter({ hasText: "AI 活动插图" }).click();
  const coverScrollAfter = await page.locator(".cover-candidate-strip").evaluate((element) => element.scrollLeft);
  const selectedCoverCount = await page.locator(".cover-candidate.selected").count();
  const pushEnabledAfterCover = await page.locator("#pushDraftButton").isEnabled();
  const coverPreviewCount = await page.locator(".cover-preview img").count();
  if (
    selectedCoverCount !== 1
    || !pushEnabledAfterCover
    || coverPreviewCount !== 1
    || coverScrollBefore <= 0
    || Math.abs(coverScrollAfter - coverScrollBefore) > 2
  ) {
    throw new Error("Selecting a material cover should update the preview and enable draft push.");
  }
  await page.setViewportSize({ width: 390, height: 844 });
  const hasHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  if (hasHorizontalOverflow) {
    throw new Error("Image workflow causes horizontal overflow on mobile.");
  }
  await page.evaluate(() => {
    state.revisionRequest = "沿用上一篇修改要求";
    state.writingRequest = { prompt: "上一篇 AI 科技活动", topic: "上一篇 AI 科技活动" };
    localStorage.setItem("writingRequest", JSON.stringify(state.writingRequest));
  });
  page.once("dialog", (dialog) => dialog.accept());
  await page.locator("#newArticleButton").click();
  await page.waitForSelector(".article-form");
  const newArticleStateReset = await page.evaluate(() => (
    state.selectedFiles.length === 0
    && state.materials === null
    && state.generatedDraft === null
    && state.revisionRequest === ""
    && state.useMaterials === false
    && Object.keys(state.writingRequest).length === 0
    && localStorage.getItem("writingRequest") === null
  ));
  if (!newArticleStateReset) {
    throw new Error("Starting a second article should clear all per-article state from the previous draft.");
  }
  const disabledMaterialsExcluded = await page.evaluate(() => {
    state.materials = {
      documents: [{ filename: "old-ai-topic.docx", text: "上一篇 AI 科技活动" }],
      photos: [{ filename: "old-photo.jpg", url: "C:\\fake\\old-photo.jpg", preview_url: "/old.jpg" }],
      stats: { total_chars: 1200, total_photos: 1 },
    };
    state.useMaterials = false;
    state.writingRequest = {
      prompt: "近视防控科普宣传的文章",
      topic: "近视防控科普宣传的文章",
      focus: "近视防控科普宣传的文章",
      activity_time: "",
      activity_location: "",
      avoid: "",
    };
    const payload = buildDraftPayload();
    return payload.materials === null
      && !Object.hasOwn(payload, "previous_article")
      && getMaterialCoverCandidates().length === 0
      && payload.requirements.user_prompt === "近视防控科普宣传的文章";
  });
  if (!disabledMaterialsExcluded) {
    throw new Error("Disabled materials must not leak old documents, photos, or previous drafts into a new payload.");
  }

  console.log(JSON.stringify({
    ok: true,
    title,
    cardCount,
    importPanelCount,
    learnedRuleCount,
    learningResultRuleCount,
    restoredHistoryCoverCandidateCount,
    restoredAfterReload,
    draftDeleteWorks,
    exemplarOptionCount,
    configRowCount,
    configModifyCount,
    configInputCount,
    styleRowCount,
    styleModifyCount,
    styleInputCount,
    selectedTemplateSummaryCount,
    inlineTemplateCardCount,
    templateCardCount,
    templatePreviewButtonCount,
    templateSelectButtonCount,
    uploadedFileRowCount,
    promptWrapsInsideSummary,
    coverCandidateCount,
    coverScrollBefore,
    coverScrollAfter,
    selectedCoverCount,
    pushDisabledBeforeCover,
    pushEnabledAfterCover,
    coverPreviewCount,
    newArticleStateReset,
    disabledMaterialsExcluded,
  }, null, 2));
} finally {
  await browser.close();
}
