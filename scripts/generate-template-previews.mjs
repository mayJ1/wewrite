import { chromium } from "playwright";
import path from "node:path";

const chromePath = process.env.CHROME_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const appUrl = process.env.APP_URL || "http://127.0.0.1:8770";
const outputDir = path.resolve("app/static/template-previews");
const templates = [
  "studio-brief",
  "neo-brutalism",
  "campus-party",
  "daily-intelligence",
  "weekly-financial",
  "deep-analysis",
  "breaking-watch",
  "product-release",
  "industry-radar",
];

const baseArticle = {
  meta: {
    title: "智启未来，AI筑梦",
    digest: "校园人工智能科普活动纪实，记录课堂讲解、互动体验与学生探索。",
    author: "学校编辑部",
    date: "2026-06-24",
  },
  headline: {
    title: "人工智能科普走进校园",
    body: ["同学们在讲解与实践中感受科技魅力，理解人工智能在学习和生活中的应用。"],
  },
  sections: [
    {
      en: "OPENING",
      cn: "活动回顾",
      intro: "活动从基础知识讲解开始，逐步走向互动体验。",
      blocks: [
        { type: "paragraph", text: "老师结合生活实例介绍人工智能的发展与应用，帮助学生建立清晰、真实的初步认识。" },
        { type: "takeaways", title: "活动亮点", items: ["科普讲解", "互动体验", "作品展示"] },
      ],
    },
    {
      en: "EXPERIENCE",
      cn: "科技体验",
      intro: "学生分组参与实践，在观察、提问和操作中加深理解。",
      blocks: [
        { type: "paragraph", text: "现场设置了多个体验环节，学生在教师指导下有序参与，课堂氛围专注而活跃。" },
      ],
    },
  ],
  conclusion: "一次近距离的科技体验，为校园里的好奇心打开了新的窗口。",
  cta: "关注校园动态，见证每一次成长。",
};

const browser = await chromium.launch({ headless: true, executablePath: chromePath });
try {
  const page = await browser.newPage({ viewport: { width: 430, height: 920 }, deviceScaleFactor: 1 });
  for (const template of templates) {
    const response = await fetch(`${appUrl}/api/render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ article: { ...baseArticle, template } }),
    });
    const data = await response.json();
    if (!data.html) throw new Error(`No HTML returned for ${template}`);
    await page.setContent(data.html, { waitUntil: "load" });
    await page.screenshot({
      path: path.join(outputDir, `${template}.png`),
      fullPage: false,
    });
    console.log(`Generated ${template}.png`);
  }
} finally {
  await browser.close();
}
