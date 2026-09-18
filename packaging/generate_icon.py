from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SIZE = 1024


def font(size: int) -> ImageFont.FreeTypeFont:
    candidates = (
        Path("C:/Windows/Fonts/georgiab.ttf"),
        Path("C:/Windows/Fonts/georgia.ttf"),
    )
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)

# A quiet editorial mark that remains legible in Windows' smallest icon slots.
draw.rounded_rectangle((42, 42, 982, 982), radius=224, fill="#1d5f55")
draw.rounded_rectangle((94, 94, 930, 930), radius=176, fill="#287c6c")
draw.rounded_rectangle((148, 148, 876, 876), radius=132, outline="#65b8a4", width=10)

wordmark = "W"
wordmark_font = font(570)
box = draw.textbbox((0, 0), wordmark, font=wordmark_font, stroke_width=2)
width = box[2] - box[0]
height = box[3] - box[1]
draw.text(
    ((SIZE - width) / 2, (SIZE - height) / 2 - box[1] - 12),
    wordmark,
    font=wordmark_font,
    fill="#f7f4ea",
    stroke_width=2,
    stroke_fill="#f7f4ea",
)

png_path = ROOT / "wewrite-icon.png"
ico_path = ROOT / "wewrite.ico"
favicon_path = ROOT.parent / "app" / "static" / "favicon.ico"
canvas.save(png_path, optimize=True)
canvas.save(ico_path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
canvas.save(favicon_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
print(png_path)
print(ico_path)
