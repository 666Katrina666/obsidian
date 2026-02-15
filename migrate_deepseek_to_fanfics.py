# -*- coding: utf-8 -*-
"""One-time migration: move .md from Fanfics/Deepseek Export to Fanfics (renumber from 373),
move non-.md to Obsidian root, then delete Deepseek Export folder.
"""
import os
import re
import shutil

OBSIDIAN = r"c:\Obsidian"
FANFICS = os.path.join(OBSIDIAN, "Fanfics")
DEEPSEEK = os.path.join(FANFICS, "Deepseek Export")
START_NUM = 373


def main():
    # 1. Move .md with renumbering
    md_files = [f for f in os.listdir(DEEPSEEK) if f.endswith(".md") and os.path.isfile(os.path.join(DEEPSEEK, f))]
    md_files.sort()
    for i, name in enumerate(md_files):
        m = re.match(r"^\d+\.\s*(.+)$", name)
        if m:
            rest = m.group(1)
        else:
            rest = name
        new_name = f"{START_NUM + i}. {rest}"
        src = os.path.join(DEEPSEEK, name)
        dst = os.path.join(FANFICS, new_name)
        shutil.move(src, dst)
        print(f"Moved: {name} -> {new_name}")
    print(f"Moved {len(md_files)} .md files to Fanfics.")

    # 2. Move non-.md to Obsidian root
    root_py = ["export_deepseek_chats.py", "rename_to_english.py", "apply_tags.py"]
    for f in root_py:
        src = os.path.join(DEEPSEEK, f)
        if os.path.isfile(src):
            shutil.move(src, os.path.join(OBSIDIAN, f))
            print(f"Moved: {f} -> Obsidian/")

    for subdir in ["tag_criteria", "__pycache__"]:
        src_dir = os.path.join(DEEPSEEK, subdir)
        if not os.path.isdir(src_dir):
            continue
        dst_dir = os.path.join(OBSIDIAN, subdir)
        if os.path.exists(dst_dir):
            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(dst_dir, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)
                    os.remove(s)
                else:
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.move(s, d)
            os.rmdir(src_dir)
        else:
            shutil.move(src_dir, dst_dir)
        print(f"Moved folder: {subdir} -> Obsidian/")

    # 3. Delete Deepseek Export (should be empty or only empty dirs)
    def remove_readonly(func, path, exc_info):
        os.chmod(path, 0o700)
        func(path)
    shutil.rmtree(DEEPSEEK, onerror=remove_readonly)
    print("Removed Deepseek Export folder.")


if __name__ == "__main__":
    main()
