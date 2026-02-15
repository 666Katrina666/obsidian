# -*- coding: utf-8 -*-
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FANFICS_DIR = SCRIPT_DIR
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "0. Content.md")

def extract_meta(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = []
        for _ in range(25):
            line = f.readline()
            if not line:
                break
            lines.append(line.rstrip("\n"))
    tags = ""
    desc_lines = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if s.startswith("#") and not tags and ("#" in s or " " in s):
            tags = s
            continue
        if s == "---":
            break
        if tags and not desc_lines and not s.startswith("#"):
            desc_lines.append(s)
        elif tags and desc_lines and not s.startswith("#") and s != "---":
            desc_lines.append(s)
            if len(desc_lines) >= 2:
                break
    description = " ".join(desc_lines).strip() if desc_lines else "(без описания)"
    return tags or "(без тегов)", description

def num_from_name(name):
    m = re.match(r"^(\d+)\.", name)
    return int(m.group(1)) if m else 9999

def main():
    entries = []
    for fn in os.listdir(FANFICS_DIR):
        if not fn.endswith(".md") or fn == "0. Content.md":
            continue
        path = os.path.join(FANFICS_DIR, fn)
        if not os.path.isfile(path):
            continue
        try:
            tags, desc = extract_meta(path)
        except Exception as e:
            tags, desc = "(ошибка)", str(e)
        title = fn[:-3]
        link = f"[[{title}]]"
        entries.append((num_from_name(fn), fn, title, link, tags, desc))
    entries.sort(key=lambda x: (x[0], x[1]))

    lines = []
    for _, fn, title, link, tags, desc in entries:
        lines.append(f"- {link}\n")
        lines.append(f"  Теги: {tags}\n")
        lines.append(f"  Описание: {desc}\n\n")
    content = "".join(lines)
    out_path = os.path.join(SCRIPT_DIR, "0. Content.md")
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(content)
    print(len(entries), "entries, wrote", len(content), "chars to", out_path)

if __name__ == "__main__":
    main()
