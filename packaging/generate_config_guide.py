from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "WeWrite-Config-Guide.pdf"
FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")

BLUE = colors.HexColor("#0B6FE8")
INK = colors.HexColor("#182230")
MUTED = colors.HexColor("#5C6878")
LINE = colors.HexColor("#D9E1EA")
PALE_BLUE = colors.HexColor("#EEF6FF")
PALE_YELLOW = colors.HexColor("#FFF7E6")


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("WeWriteCN", str(FONT)))
    pdfmetrics.registerFont(TTFont("WeWriteCN-Bold", str(FONT_BOLD)))


def draw_page(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 17 * mm, width - 20 * mm, 17 * mm)
    canvas.setFont("WeWriteCN", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 10 * mm, "WeWrite 配置教程")
    canvas.drawRightString(width - 20 * mm, 10 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def main() -> None:
    register_fonts()
    width, height = A4
    frame = Frame(
        20 * mm,
        22 * mm,
        width - 40 * mm,
        height - 38 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        title="WeWrite 配置教程",
        author="WeWrite",
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=16 * mm,
        bottomMargin=22 * mm,
    )
    doc.addPageTemplates(PageTemplate(id="guide", frames=[frame], onPage=draw_page))

    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "title",
        parent=base["Title"],
        fontName="WeWriteCN-Bold",
        fontSize=25,
        leading=34,
        textColor=INK,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    )
    subtitle = ParagraphStyle(
        "subtitle",
        parent=base["BodyText"],
        fontName="WeWriteCN",
        fontSize=11,
        leading=19,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )
    h1 = ParagraphStyle(
        "h1",
        parent=base["Heading1"],
        fontName="WeWriteCN-Bold",
        fontSize=16,
        leading=24,
        textColor=INK,
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
        keepWithNext=True,
    )
    body = ParagraphStyle(
        "body",
        parent=base["BodyText"],
        fontName="WeWriteCN",
        fontSize=10.5,
        leading=19,
        textColor=INK,
        spaceAfter=2.2 * mm,
    )
    bullet = ParagraphStyle(
        "bullet",
        parent=body,
        leftIndent=6 * mm,
        firstLineIndent=-5 * mm,
        bulletIndent=0,
        spaceAfter=1.5 * mm,
    )
    link = ParagraphStyle(
        "link",
        parent=body,
        fontSize=9,
        leading=15,
        textColor=BLUE,
        leftIndent=5 * mm,
        rightIndent=5 * mm,
        borderColor=colors.HexColor("#BDD8FA"),
        borderWidth=0.8,
        borderPadding=7,
        backColor=PALE_BLUE,
        spaceBefore=2 * mm,
        spaceAfter=3 * mm,
    )
    note = ParagraphStyle(
        "note",
        parent=body,
        leftIndent=5 * mm,
        rightIndent=5 * mm,
        borderColor=colors.HexColor("#F1C977"),
        borderWidth=0.8,
        borderPadding=8,
        backColor=PALE_YELLOW,
        spaceBefore=2 * mm,
        spaceAfter=4 * mm,
    )

    story = [
        Spacer(1, 16 * mm),
        Paragraph("WeWrite 配置教程", title),
        Paragraph("第一次使用时照着做一遍，通常几分钟就能完成。", subtitle),
        Paragraph(
            "<b>开始前准备</b><br/>"
            "准备好微信公众号管理员微信、可正常登录的公众号后台，以及用于 AI 写稿和生图的平台账号。"
            "所有密钥只填写到自己电脑上的 WeWrite 设置页，不要发给他人。",
            note,
        ),
        Paragraph("打开 WeWrite", h1),
        Paragraph(
            "解压分发包后，双击 <b>Start-WeWrite.bat</b> 或 <b>WeWrite.exe</b>。"
            "浏览器打开后点击右上角设置图标，按下面步骤填写。",
            body,
        ),
        Paragraph("1. 获取公众号 AppID", h1),
        Paragraph("1）访问微信公众平台并登录自己的公众号。", body),
        Paragraph("2）在左侧菜单进入“设置与开发” - “基本配置”。不同版本后台的菜单名称可能略有差异。", body),
        Paragraph("3）找到“开发者ID（AppID）”，复制后粘贴到 WeWrite 的“公众号 AppID”。", body),
        Paragraph(
            '<link href="https://mp.weixin.qq.com/" color="#0B6FE8">'
            "微信公众平台：https://mp.weixin.qq.com/</link>",
            link,
        ),
        Paragraph("2. 获取公众号 AppSecret", h1),
        Paragraph("1）仍在“设置与开发” - “基本配置”页面，找到“开发者密码（AppSecret）”。", body),
        Paragraph("2）按页面提示查看或重置 AppSecret，通常需要公众号管理员扫码确认。", body),
        Paragraph("3）复制新生成的 AppSecret，立即粘贴到 WeWrite 的“公众号 AppSecret”。", body),
        Paragraph(
            "<b>注意：</b>重置 AppSecret 后，旧密钥会失效。AppSecret 相当于公众号密码，"
            "不要截图、不要通过聊天软件发送，也不要填写到不可信的网站。",
            note,
        ),
        Paragraph("还要配置 API IP 白名单", h1),
        Paragraph(
            "在 WeWrite 设置页点击“获取当前 IP”，复制显示的公网 IP。回到微信公众平台的基本配置页面，"
            "找到“IP 白名单”并加入该 IP。更换网络或公网 IP 变化后，需要重新设置，否则推送草稿可能失败。",
            body,
        ),
        Paragraph("3. 获取 AI 写稿 API Key（DeepSeek）", h1),
        Paragraph("1）打开 DeepSeek 开放平台，注册或登录账号。", body),
        Paragraph("2）先在账户中充值少量余额；网页版会员和 API 账户通常是分别计费的。", body),
        Paragraph("3）进入“API Keys”，点击“创建 API Key”。", body),
        Paragraph("4）复制生成的密钥，粘贴到 WeWrite 的“AI 写稿 API Key”。", body),
        Paragraph(
            '<link href="https://platform.deepseek.com/api_keys" color="#0B6FE8">'
            "DeepSeek API Keys：https://platform.deepseek.com/api_keys</link><br/>"
            '<link href="https://api-docs.deepseek.com/" color="#0B6FE8">'
            "DeepSeek 官方 API 文档：https://api-docs.deepseek.com/</link>",
            link,
        ),
        Paragraph(
            "<b>分清两件事：</b>这里需要的是开放平台生成的 API Key，不是 DeepSeek 登录密码，"
            "也不是网页版聊天账号。API 调用会按实际用量扣费。",
            note,
        ),
        Paragraph("4. 配置豆包 Seedream 生图 API Key（选填）", h1),
        Paragraph("只有需要 AI 生成正文插图或封面时才需要配置；只使用自己上传的照片可以跳过。", body),
        Paragraph("1）打开火山方舟控制台，注册并完成平台要求的认证和服务开通。", body),
        Paragraph("2）确认账户可使用豆包 Seedream 图片生成模型，并保持账户有可用额度。", body),
        Paragraph("3）进入“系统管理” - “API Key 管理”，创建或查看 API Key。", body),
        Paragraph("4）在 WeWrite 的 AI 生图配置中选择“豆包 Seedream”，粘贴 API Key。模型名称保持默认即可。", body),
        Paragraph(
            '<link href="https://console.volcengine.com/ark/region:ark+cn-beijing/apikey" color="#0B6FE8">'
            "火山方舟 API Key 管理：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey</link><br/>"
            '<link href="https://www.volcengine.com/docs/82379/seedream?lang=zh" color="#0B6FE8">'
            "Seedream 官方文档：https://www.volcengine.com/docs/82379/seedream?lang=zh</link>",
            link,
        ),
        Paragraph("上传素材的小技巧", h1),
        Paragraph(
            "<b>图片文件尽量按内容命名。</b>例如：<br/>"
            "“校长致辞.jpg”“学生体验机器人.jpg”“颁奖合影.jpg”。<br/>"
            "不要只使用“IMG_001.jpg”“微信图片.jpg”这类名称。清楚的文件名能帮助 AI 理解图片内容，"
            "把图片插到文章中更合适的位置。",
            note,
        ),
        Paragraph("配置完成后检查", h1),
        Paragraph("• AppID、AppSecret 和 AI 写稿 API 显示“已配置”。", bullet),
        Paragraph("• 需要 AI 生图时，AI 生图 API 也显示“已配置”。", bullet),
        Paragraph("• 微信后台已经加入当前公网 IP 白名单。", bullet),
        Paragraph("• 先生成一篇短文章并推送到微信草稿箱，完成首次连通性测试。", bullet),
        Paragraph(
            "<b>密钥安全：</b>不要把自己的 data 文件夹、config.yaml、API Key 或 AppSecret 一起发给别人。"
            "每位使用者都应填写自己的账号和密钥。",
            note,
        ),
    ]

    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
