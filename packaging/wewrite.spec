# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path


root = Path.cwd()
datas = [
    (str(root / "app" / "static"), "app/static"),
    (str(root / "app" / "prompts"), "app/prompts"),
    (str(root / "templates"), "templates"),
    (str(root / "personas"), "personas"),
    (str(root / "packaging" / "default-data"), "packaging/default-data"),
    (str(root / "config.example.yaml"), "."),
]
rewrite_engine = root / "rewrite-engine"
if rewrite_engine.exists():
    datas.append((str(rewrite_engine), "rewrite-engine"))

a = Analysis(
    [str(root / "app" / "server.py")],
    pathex=[str(root / "app"), str(root / "scripts"), str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "article_lib",
        "edit_learning_service",
        "extract_exemplar",
        "fetch_article",
        "humanness_score",
        "import_materials",
        "publisher",
        "rewrite_service",
        "wechat_api",
        "docx",
        "PIL",
        "pdfplumber",
        "PyPDF2",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["playwright"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WeWrite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WeWrite",
)
