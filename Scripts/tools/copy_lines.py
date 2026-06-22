# -*- coding: utf-8 -*-
"""
Copy a range of lines from one file to another.
Usage: python copy_lines.py <source_file> <dest_file> <start_line> <end_line> [mode]
  start_line, end_line: 1-based, inclusive.
  mode: 'w' = overwrite dest with lines only; 'a' = append lines to dest (default).
"""
import os
import sys


def main():
    if len(sys.argv) < 5:
        print("Usage: copy_lines.py <source> <dest> <start_line> <end_line> [w|a]")
        sys.exit(1)
    src = os.path.normpath(sys.argv[1])
    dst = os.path.normpath(sys.argv[2])
    start = int(sys.argv[3])
    end = int(sys.argv[4])
    mode = sys.argv[5] if len(sys.argv) > 5 else "a"
    if not os.path.isfile(src):
        print("Source not found:", src)
        sys.exit(1)
    with open(src, "r", encoding="utf-8") as f:
        lines = f.readlines()
    total = len(lines)
    if end < 1 or start > total:
        print("Empty range or out of bounds. File has", total, "lines.")
        sys.exit(1)
    start = max(1, start)
    end = min(total, end)
    selected = lines[start - 1 : end]
    if mode == "w":
        with open(dst, "w", encoding="utf-8") as f:
            f.writelines(selected)
    else:
        with open(dst, "a", encoding="utf-8") as f:
            f.writelines(selected)
    print(
        "Copied lines",
        start,
        "-",
        end,
        "from",
        os.path.basename(src),
        "to",
        os.path.basename(dst),
        "(" + ("overwrite" if mode == "w" else "append") + ")",
    )


if __name__ == "__main__":
    main()
