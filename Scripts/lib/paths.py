# -*- coding: utf-8 -*-
"""Resolve Obsidian vault root (folder containing tag_criteria/)."""
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
