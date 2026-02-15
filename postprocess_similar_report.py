# -*- coding: utf-8 -*-
"""Post-process similar_fanfics_report.md: one repeated paragraph per group; add file links for (shingles) groups."""
import os
import re

ENCODING = "utf-8"
REPORT_PATH = "similar_fanfics_report.md"
FANFICS_FOLDER = "Fanfics"


def file_number_from_path(path):
    name = os.path.basename(path)
    m = re.match(r"^(\d+)\.", name)
    return m.group(1) if m else None


def build_number_to_link(repo_root):
    """Scan Fanfics (and subdirs) for *.md, return dict: num -> Obsidian link (Fanfics/... or Fanfics/subdir/...)."""
    fanfics_dir = os.path.join(repo_root, FANFICS_FOLDER)
    out = {}
    for root, _dirs, files in os.walk(fanfics_dir):
        for name in files:
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            num = file_number_from_path(path)
            if num is None:
                continue
            rel = os.path.relpath(path, repo_root)
            link = rel.replace("\\", "/").replace(".md", "")
            out[num] = "[[" + link + "]]"
    return out


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, REPORT_PATH)
    num_to_link = build_number_to_link(script_dir)

    with open(report_path, "r", encoding=ENCODING) as f:
        lines = f.readlines()

    header_re = re.compile(r"^\*\*([0-9, ]+)\*\*\s*\((.*)\)\s*$")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = header_re.match(line.strip())
        if m:
            nums_str, reason = m.group(1), m.group(2)
            nums = [x.strip() for x in nums_str.split(",") if x.strip()]
            is_shingles = "shingles" in reason
            has_exact = "exact paragraph" in reason
            out.append(line)
            i += 1
            if i < len(lines) and lines[i].strip() == "":
                out.append(lines[i])
                i += 1
            if is_shingles and not has_exact:
                links = [num_to_link.get(n, "[[" + FANFICS_FOLDER + "/" + n + ".]]") for n in nums]
                out.append("In: " + ", ".join(links) + "\n")
                out.append("\n")
                while i < len(lines) and not header_re.match(lines[i].strip()):
                    i += 1
            else:
                first_para_done = False
                while i < len(lines):
                    cur = lines[i]
                    if header_re.match(cur.strip()):
                        break
                    if cur.strip().startswith("Repeated paragraph:"):
                        if not first_para_done:
                            first_para_done = True
                            out.append(cur)
                            i += 1
                            while i < len(lines):
                                next_line = lines[i]
                                if next_line.strip().startswith("Repeated paragraph:") or header_re.match(next_line.strip()):
                                    break
                                out.append(next_line)
                                i += 1
                        else:
                            i += 1
                            while i < len(lines):
                                next_line = lines[i]
                                if next_line.strip().startswith("Repeated paragraph:") or header_re.match(next_line.strip()):
                                    break
                                i += 1
                    else:
                        out.append(cur)
                        i += 1
            continue
        out.append(line)
        i += 1

    with open(report_path, "w", encoding=ENCODING) as f:
        f.writelines(out)
    print("Done. Wrote", report_path)


if __name__ == "__main__":
    main()
