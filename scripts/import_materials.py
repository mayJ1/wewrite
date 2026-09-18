#!/usr/bin/env python3
"""
WeWrite 素材目录导入工具

扫描素材目录，提取文档文本 + 上传照片到微信素材库。
用于学校活动报道场景：活动方案文档(Word/PDF) + 活动照片 → 结构化素材数据。

用法:
  python3 import_materials.py <目录>                    # 输出 JSON 到 stdout
  python3 import_materials.py <目录> --output result.json  # 写到文件
  python3 import_materials.py <目录> --no-upload            # 仅提取文档，不上传照片
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# --- 将 scripts 目录加入 sys.path，以便导入 wechat_api ---
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

# --- 支持的格式 ---
DOC_EXTENSIONS = {".docx", ".pdf", ".txt", ".md"}
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

# 微信图片上传限制
WECHAT_IMAGE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
WECHAT_THUMB_MAX_BYTES = 1 * 1024 * 1024   # 1 MB（封面图）


def compress_image(filepath: str, max_bytes: int = WECHAT_IMAGE_MAX_BYTES) -> str:
    """
    如果图片超过 max_bytes，自动等比缩放压缩。
    返回压缩后的临时文件路径（原文件不变）。
    如果不需要压缩，返回原路径。
    """
    filepath = str(filepath)
    original_size = Path(filepath).stat().st_size
    if original_size <= max_bytes:
        return filepath

    try:
        from PIL import Image
    except ImportError:
        print(f"  WARNING: PIL/Pillow 未安装，无法压缩 {Path(filepath).name}（{original_size/1024/1024:.1f}MB）", file=sys.stderr)
        return filepath

    img = Image.open(filepath)
    original_mode = img.mode

    # 尝试 1：等比缩放到 1920px 宽
    quality = 85
    w, h = img.size
    if w > 1920:
        ratio = 1920 / w
        img = img.resize((1920, int(h * ratio)), Image.LANCZOS)

    # 保存到临时文件
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=Path(filepath).suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()

    # JPEG 用 quality 控制大小，PNG 用 optimize
    save_kwargs = {"quality": quality, "optimize": True}
    if original_mode in ("RGBA", "P") and Path(filepath).suffix.lower() == ".png":
        save_kwargs = {"optimize": True}
    elif original_mode in ("RGBA", "P"):
        # 非 PNG 的透明图转 RGB
        img = img.convert("RGB")

    img.save(tmp_path, **{k: v for k, v in save_kwargs.items() if k in ("quality", "optimize")})

    compressed_size = Path(tmp_path).stat().st_size
    if compressed_size > max_bytes:
        # 尝试 2：降 quality
        quality = 60
        img.save(tmp_path, quality=quality, optimize=True)
        compressed_size = Path(tmp_path).stat().st_size

    if compressed_size > max_bytes:
        # 尝试 3：进一步缩小尺寸
        img_small = img.resize((1280, int(1280 * img.size[1] / img.size[0])), Image.LANCZOS)
        img_small.save(tmp_path, quality=quality, optimize=True)
        compressed_size = Path(tmp_path).stat().st_size

    reduction = (1 - compressed_size / original_size) * 100
    print(f"  压缩: {Path(filepath).name} {original_size/1024/1024:.1f}MB -> {compressed_size/1024/1024:.1f}MB (-{reduction:.0f}%)", file=sys.stderr)
    return tmp_path


def load_config(skill_dir: Path) -> dict:
    """加载 config.yaml，返回微信配置。"""
    config_path = skill_dir / "config.yaml"
    if not config_path.exists():
        return {}

    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    wechat = config.get("wechat", {})
    return {
        "appid": wechat.get("appid", ""),
        "secret": wechat.get("secret", ""),
    }


def extract_docx(filepath: Path) -> str:
    """从 .docx 文件提取文本。"""
    try:
        import docx
    except ImportError:
        raise ImportError(
            "需要 python-docx 库提取 Word 文档。请运行: pip install python-docx"
        )

    doc = docx.Document(str(filepath))
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    # 也提取表格中的文本
    for table in doc.tables:
        for row in table.rows:
            row_texts = []
            for cell in row.cells:
                ct = cell.text.strip()
                if ct:
                    row_texts.append(ct)
            if row_texts:
                paragraphs.append(" | ".join(row_texts))

    return "\n\n".join(paragraphs)


def extract_pdf(filepath: Path) -> str:
    """从 .pdf 文件提取文本。优先用 pdfplumber，失败回退 PyPDF2。"""
    # 先试 pdfplumber（提取质量更好）
    try:
        import pdfplumber
        with pdfplumber.open(str(filepath)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text.strip())
            return "\n\n".join(pages)
    except ImportError:
        pass

    # 回退 PyPDF2
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(str(filepath))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except ImportError:
        raise ImportError(
            "需要 pdfplumber 或 PyPDF2 库提取 PDF 文档。请运行: pip install pdfplumber"
        )


def extract_txt(filepath: Path) -> str:
    """从纯文本文件读取内容。"""
    encodings = ["utf-8", "gbk", "gb2312", "utf-16"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 最后尝试忽略错误
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def scan_directory(directory: Path) -> dict:
    """
    扫描目录，支持子文件夹分类。

    - 文档（.docx/.pdf/.txt/.md）只从根目录扫描
    - 图片支持两种组织方式：
      1. 子文件夹分类：每个子文件夹名作为分类标签
         例：绘画/xxx.png → category: "绘画"
      2. 平铺：所有图片放在根目录，category 为 null
    - 混合模式（根目录有图 + 有子文件夹）：子文件夹作为分类，
      根目录图片归入 category: null

    Returns:
        {
            "documents": [{"filename": str, "ext": str, "path": str}, ...],
            "images": [{"filename": str, "ext": str, "path": str, "category": str|null}, ...],
            "categories": ["绘画", "书法"] | null
        }
    """
    documents = []
    images = []
    categories = []

    # 先收集子目录名作为候选分类
    subdirs = [d for d in sorted(directory.iterdir()) if d.is_dir()]
    has_subdirs = len(subdirs) > 0

    # 扫描根目录文件
    for entry in sorted(directory.iterdir()):
        if not entry.is_file():
            continue
        ext = entry.suffix.lower()
        if ext in DOC_EXTENSIONS:
            documents.append({
                "filename": entry.name,
                "ext": ext,
                "path": str(entry.resolve()),
            })
        elif ext in IMG_EXTENSIONS and not has_subdirs:
            # 平铺模式：根目录的图片直接加入
            images.append({
                "filename": entry.name,
                "ext": ext,
                "path": str(entry.resolve()),
                "category": None,
            })

    # 扫描子文件夹中的图片（分类模式）
    if has_subdirs:
        for subdir in subdirs:
            category = subdir.name
            categories.append(category)
            for entry in sorted(subdir.iterdir()):
                if not entry.is_file():
                    continue
                ext = entry.suffix.lower()
                if ext in IMG_EXTENSIONS:
                    images.append({
                        "filename": entry.name,
                        "ext": ext,
                        "path": str(entry.resolve()),
                        "category": category,
                    })

    return {
        "documents": documents,
        "images": images,
        "categories": categories if categories else None,
    }


def extract_document(file_info: dict) -> dict:
    """提取单个文档的文本内容。"""
    filepath = Path(file_info["path"])
    ext = file_info["ext"]

    extractors = {
        ".docx": extract_docx,
        ".pdf": extract_pdf,
        ".txt": extract_txt,
        ".md": extract_txt,
    }

    extractor = extractors.get(ext)
    if not extractor:
        return {**file_info, "text": "", "error": f"Unsupported format: {ext}"}

    try:
        text = extractor(filepath)
        return {
            "filename": file_info["filename"],
            "ext": ext,
            "text": text,
            "char_count": len(text),
        }
    except ImportError as e:
        return {
            "filename": file_info["filename"],
            "ext": ext,
            "text": "",
            "error": str(e),
        }
    except Exception as e:
        return {
            "filename": file_info["filename"],
            "ext": ext,
            "text": "",
            "error": f"Extraction failed: {e}",
        }


def upload_photos(image_files: list, appid: str, secret: str) -> list:
    """
    上传照片到微信素材库，返回带 CDN URL 的结果列表。

    Args:
        image_files: list of {"filename": str, "path": str, "ext": str}
        appid: WeChat appid
        secret: WeChat secret

    Returns:
        list of {"filename": str, "url": str, "error": str|None}
    """
    # 保留 category 字段的辅助函数
    def _result(img, url=None, error=None, local_only=True):
        r = {
            "filename": img["filename"],
            "url": url or img["path"],
            "error": error,
            "local_only": local_only,
        }
        if img.get("category"):
            r["category"] = img["category"]
        return r

    if not appid or not secret:
        return [_result(img) for img in image_files]

    try:
        from wechat_api import get_access_token, upload_image
    except ImportError:
        return [_result(img, error="Cannot import wechat_api") for img in image_files]

    try:
        token = get_access_token(appid, secret)
    except Exception as e:
        return [_result(img, error=f"Auth failed: {e}") for img in image_files]

    results = []
    for img in image_files:
        try:
            # 上传前自动压缩超大图片
            upload_path = compress_image(img["path"])
            cdn_url = upload_image(token, upload_path)
            results.append(_result(img, url=cdn_url, local_only=False))
            # 清理临时压缩文件
            if upload_path != img["path"]:
                try:
                    os.unlink(upload_path)
                except OSError:
                    pass
        except Exception as e:
            results.append(_result(img, error=str(e)))

    return results


def main():
    parser = argparse.ArgumentParser(
        description="WeWrite 素材目录导入 — 提取文档 + 上传照片到微信素材库"
    )
    parser.add_argument(
        "directory",
        help="素材目录路径（包含活动方案文档和照片）",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出 JSON 文件路径（默认输出到 stdout）",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="跳过照片上传（仅提取文档文本）",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="config.yaml 路径（默认: {skill_dir}/config.yaml）",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="美化 JSON 输出（默认 compact）",
    )

    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"错误：目录不存在 - {directory}", file=sys.stderr)
        sys.exit(1)
    if not directory.is_dir():
        print(f"错误：路径不是目录 - {directory}", file=sys.stderr)
        sys.exit(1)

    # --- 扫描目录 ---
    scan_result = scan_directory(directory)
    documents = scan_result["documents"]
    images = scan_result["images"]

    # --- 提取文档 ---
    doc_results = []
    for doc in documents:
        result = extract_document(doc)
        doc_results.append(result)

    # --- 上传照片 ---
    photo_results = []
    creds = {"appid": "", "secret": ""}
    if not args.no_upload and images:
        config_path = Path(args.config) if args.config else (SKILL_DIR / "config.yaml")
        if config_path.exists():
            creds = load_config(SKILL_DIR)

        photo_results = upload_photos(images, creds.get("appid", ""), creds.get("secret", ""))
    elif images:
        # no-upload 模式，保留本地路径和分类标签
        def _keep_category(img):
            r = {"filename": img["filename"], "url": img["path"], "error": None, "local_only": True}
            if img.get("category"):
                r["category"] = img["category"]
            return r
        photo_results = [_keep_category(img) for img in images]

    # --- 构建输出 ---
    uploaded_count = sum(1 for p in photo_results if not p.get("error"))
    failed_upload_count = sum(1 for p in photo_results if p.get("error"))

    output = {
        "directory": str(directory.resolve()),
        "documents": doc_results,
        "photos": photo_results,
        "categories": scan_result.get("categories"),
        "stats": {
            "total_docs": len(documents),
            "total_photos": len(images),
            "total_chars": sum(d.get("char_count", 0) for d in doc_results),
            "docs_with_errors": sum(1 for d in doc_results if d.get("error")),
            "photos_uploaded": uploaded_count,
            "photos_failed": failed_upload_count,
            "photos_local_only": args.no_upload or not creds.get("appid"),
        },
    }

    indent = 2 if args.pretty else None
    json_str = json.dumps(output, ensure_ascii=False, indent=indent)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str, encoding="utf-8")
        print(f"OK: 输出已保存: {output_path.resolve()}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
