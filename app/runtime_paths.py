from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _resource_root() -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root).resolve()
    return Path(__file__).resolve().parents[1]


def _data_root(resource_root: Path) -> Path:
    configured = os.environ.get("WEWRITE_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return (Path(sys.executable).resolve().parent / "data").resolve()
    return resource_root


RESOURCE_ROOT = _resource_root()
DATA_ROOT = _data_root(RESOURCE_ROOT)


def initialize_user_data() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for name in ("output", "corpus", "lessons", "references/exemplars"):
        (DATA_ROOT / name).mkdir(parents=True, exist_ok=True)

    defaults_root = RESOURCE_ROOT / "packaging" / "default-data"
    default_files = {
        "config.example.yaml": RESOURCE_ROOT / "config.example.yaml",
        "playbook.md": defaults_root / "playbook.md",
        "history.yaml": defaults_root / "history.yaml",
    }
    for relative, source in default_files.items():
        target = DATA_ROOT / relative
        if not target.exists() and source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    personas_source = RESOURCE_ROOT / "personas"
    personas_target = DATA_ROOT / "personas"
    if personas_source.exists() and not personas_target.exists():
        shutil.copytree(personas_source, personas_target)

    exemplar_index = DATA_ROOT / "references" / "exemplars" / "index.yaml"
    if not exemplar_index.exists():
        exemplar_index.write_text("[]\n", encoding="utf-8")

    os.environ["WEWRITE_RESOURCE_DIR"] = str(RESOURCE_ROOT)
    os.environ["WEWRITE_DATA_DIR"] = str(DATA_ROOT)
