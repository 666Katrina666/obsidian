# -*- coding: utf-8 -*-
"""Set base file's first line to only tags that appear in ALL divergence files.
Usage: python tags_common_from_divergences.py <base.md> <div1.md> [div2.md ...]
Reads first line (tags) from each divergence, computes intersection, writes to base.
"""
import re
import sys
import os

ENCODING = "utf-8"


def parse_tags(line):
    if not line or not line.strip():
        return []
    tags = re.findall(r"#([^\s#]+)", line.strip())
    return list(dict.fromkeys(tags))


def main():
    if len(sys.argv) < 3:
        print("Usage: tags_common_from_divergences.py <base.md> <div1.md> [div2.md ...]")
        sys.exit(1)
    base_path = os.path.normpath(sys.argv[1])
    div_paths = [os.path.normpath(p) for p in sys.argv[2:]]
    for p in [base_path] + div_paths:
        if not os.path.isfile(p):
            print("Not found:", p, file=sys.stderr)
            sys.exit(1)

    tag_sets = []
    for p in div_paths:
        with open(p, "r", encoding=ENCODING) as f:
            first = f.readline()
        tag_sets.append(set(parse_tags(first)))
        print("Tags in", os.path.basename(p), ":", sorted(tag_sets[-1]))

    common = set.intersection(*tag_sets) if tag_sets else set()
    common_line = " ".join("#" + t for t in sorted(common))

    with open(base_path, "r", encoding=ENCODING) as f:
        content = f.read()
    if "\n" in content:
        _, rest = content.split("\n", 1)
    else:
        rest = ""
    with open(base_path, "w", encoding=ENCODING) as f:
        f.write(common_line + "\n" + rest)
    print("Base", base_path, "->", common_line)


if __name__ == "__main__":
    main()
