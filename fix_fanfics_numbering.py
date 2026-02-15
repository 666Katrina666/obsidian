# -*- coding: utf-8 -*-
"""
1. Find and delete empty Fanfics *.ajson (and corresponding *.md if empty)
2. Fix numbering gaps: for each gap, rename the file with max number to fill the gap
3. Output rename map for similar_fanfics_report.md
"""
import os
import re
import json

OBSIDIAN = os.path.normpath(r"c:\Obsidian")
MULTI_DIR = os.path.join(OBSIDIAN, ".smart-env", "multi")
FANFICS_DIR = os.path.join(OBSIDIAN, "Fanfics")
REPORT_PATH = os.path.join(OBSIDIAN, "similar_fanfics_report.md")

def get_ajson_list():
    """Return list of (num, ajson_path) for Fanfics_*.ajson, num as int."""
    result = []
    for name in os.listdir(MULTI_DIR):
        if not name.startswith("Fanfics_") or not name.endswith(".ajson"):
            continue
        m = re.match(r"Fanfics_(\d+)_", name)
        if m:
            result.append((int(m.group(1)), os.path.join(MULTI_DIR, name)))
    return result

def read_path_from_ajson(ajson_path):
    """Read first 'Fanfics/NUM. ...' path from ajson (first key or 'path' value)."""
    try:
        with open(ajson_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            return None
        # ajson is JSON object; find "path":"Fanfics/...
        match = re.search(r'"path"\s*:\s*"(Fanfics/\d+\.[^"]+)"', raw)
        if match:
            return match.group(1)
        # or first key like "smart_sources:Fanfics/...
        match = re.search(r'"smart_sources:(Fanfics/\d+\.[^"]+)"', raw)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None

def is_empty_ajson(ajson_path):
    """Consider empty: size 0 or content is only whitespace/empty JSON."""
    try:
        size = os.path.getsize(ajson_path)
        if size == 0:
            return True
        if size > 10:
            return False
        with open(ajson_path, "r", encoding="utf-8") as f:
            s = f.read().strip()
        return len(s) <= 2  # e.g. "\n" or "{}"
    except Exception:
        return False

def main():
    ajson_list = get_ajson_list()
    num_to_ajson = {num: path for num, path in ajson_list}
    nums = sorted(num_to_ajson.keys())
    print("Total ajson files:", len(nums))
    if not nums:
        print("No Fanfics_*.ajson files found. Exit.")
        return
    print("Number range:", min(nums), "-", max(nums))

    # 1) Delete empty ajson
    deleted_ajson = []
    for num in list(nums):
        path = num_to_ajson.get(num)
        if path and is_empty_ajson(path):
            os.remove(path)
            deleted_ajson.append((num, path))
            del num_to_ajson[num]
    nums = sorted(num_to_ajson.keys())
    if deleted_ajson:
        print("Deleted empty ajson:", len(deleted_ajson), [n for n, _ in deleted_ajson])

    # 2) Find gaps and build renames: for each gap, assign current_max -> gap
    renames = []  # (old_num, new_num, old_path_in_file) for report
    while True:
        nums = sorted(num_to_ajson.keys())
        if not nums:
            break
        gap = None
        for i in range(1, len(nums)):
            if nums[i] - nums[i-1] > 1:
                gap = nums[i-1] + 1
                break
        if gap is None:
            break
        # take file with max number and rename to gap
        old_num = max(nums)
        ajson_path = num_to_ajson[old_num]
        old_path_str = read_path_from_ajson(ajson_path)
        if not old_path_str:
            print("Skip (no path in ajson):", ajson_path)
            del num_to_ajson[old_num]
            continue

        # old_path_str like "Fanfics/717. Jason Todd revenge in a weak body.md"
        # title = "717. Jason Todd revenge in a weak body.md" -> "556. Jason Todd ..."
        parts = old_path_str.split("/", 1)
        if len(parts) != 2 or not parts[1]:
            del num_to_ajson[old_num]
            continue
        title_with_num = parts[1]  # "717. Jason Todd ..."
        title_match = re.match(r"^\d+\.\s*(.+)$", title_with_num)
        if not title_match:
            del num_to_ajson[old_num]
            continue
        title_only = title_match.group(1)  # "Jason Todd ..."
        new_path_str = "Fanfics/{}. {}".format(gap, title_only)

        # New ajson filename: Fanfics_GAP__Title_md.ajson (title in filename: replace spaces/special with _)
        safe_suffix = title_only.replace(".md", "").replace(" ", "_").replace(".", "_")
        for c in '\\/:*?"<>|':
            safe_suffix = safe_suffix.replace(c, "_")
        new_ajson_name = "Fanfics_{}__{}_md.ajson".format(gap, safe_suffix[:80])
        new_ajson_path = os.path.join(MULTI_DIR, new_ajson_name)

        # Rename md file if exists
        old_md_path = os.path.join(OBSIDIAN, "Fanfics", title_with_num)
        new_md_path = os.path.join(OBSIDIAN, "Fanfics", "{}. {}".format(gap, title_only))
        if os.path.isfile(old_md_path):
            if os.path.isfile(new_md_path):
                print("Warning: target md exists, skip md rename:", new_md_path)
            else:
                os.rename(old_md_path, new_md_path)
                print("Renamed md:", title_with_num, "->", "{}. {}".format(gap, title_only))

        # Update path inside ajson and rename ajson file
        with open(ajson_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Replace all occurrences of old path with new path (escape for regex: . and digits)
        content = content.replace(old_path_str, new_path_str)
        # Replace smart_sources:Fanfics/717. -> smart_sources:Fanfics/556.
        content = re.sub(
            r"smart_sources:Fanfics/" + str(old_num) + r"\. ",
            "smart_sources:Fanfics/" + str(gap) + ". ",
            content
        )
        content = re.sub(
            r"smart_blocks:Fanfics/" + str(old_num) + r"\. ",
            "smart_blocks:Fanfics/" + str(gap) + ". ",
            content
        )
        if os.path.isfile(new_ajson_path) and new_ajson_path != ajson_path:
            os.remove(new_ajson_path)
        with open(new_ajson_path, "w", encoding="utf-8") as f:
            f.write(content)
        if ajson_path != new_ajson_path:
            os.remove(ajson_path)
        num_to_ajson[gap] = new_ajson_path
        del num_to_ajson[old_num]
        renames.append((old_num, gap, old_path_str))
        print("Renamed ajson: {} -> {} (fill gap {})".format(old_num, gap, gap))

    # 3) Update report: replace [[Fanfics/OLD. Title]] with [[Fanfics/NEW. Title]] when (old, new) in renames
    renames_by_old = {r[0]: (r[1], r[2]) for r in renames}
    if renames_by_old and os.path.isfile(REPORT_PATH):
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            report = f.read()
        for old_num, (new_num, old_path_str) in renames_by_old.items():
            # old_path_str like "Fanfics/717. Jason Todd revenge in a weak body.md"
            link_part = old_path_str.replace(".md", "")  # "Fanfics/717. Jason Todd..."
            old_link = "[[" + link_part + "]]"
            # Title: part after "Fanfics/NUM. "
            title_match = re.match(r"Fanfics/\d+\.\s*(.+)", link_part)
            title_only = title_match.group(1).strip() if title_match else link_part.split(". ", 1)[-1].strip()
            new_link = "[[Fanfics/{}. {}]]".format(new_num, title_only)
            report = report.replace(old_link, new_link)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report)
        print("Updated report for", len(renames_by_old), "renames")

    print("Renames (old -> new):", renames)

if __name__ == "__main__":
    main()
