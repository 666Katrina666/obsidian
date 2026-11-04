# -*- coding: utf-8 -*-
"""Resolve Obsidian vault root (folder containing tag_criteria/) and its work folders."""
from __future__ import annotations

from pathlib import Path


def vault_root(from_file: str | Path) -> Path:
    p = Path(from_file).resolve()
    for d in [p, *p.parents]:
        if (d / "tag_criteria").is_dir():
            return d
    raise FileNotFoundError(
        f"Could not find vault root (no tag_criteria/) starting from {from_file!r}"
    )


# Генерируемые отчёты скриптов и рабочие заметки живут в своих папках,
# а не в корне хранилища: корень держит только заметки и служебное.
REPORTS_DIR = "Reports"
NOTES_DIR = "Notes"


def reports_dir(from_file: str | Path) -> Path:
    """Папка отчётов; создаётся при первом обращении."""
    d = vault_root(from_file) / REPORTS_DIR
    d.mkdir(exist_ok=True)
    return d


def notes_dir(from_file: str | Path) -> Path:
    """Папка рабочих заметок: задачи, иерархия тегов, план конвейера."""
    return vault_root(from_file) / NOTES_DIR
