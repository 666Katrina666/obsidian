# -*- coding: utf-8 -*-
"""Recalc tags for a common file and its divergence files (N, N.1, N.2).
Common file gets only tags detected from its content. Each divergence gets
common tags + tags detected from its own content. Uses tag_criteria/ like apply_tags.py.
Usage: python apply_tags_common_divergence.py <common.md> [divergence1.md divergence2.md ...]
Example: python apply_tags_common_divergence.py Fanfics/83. Title.md Fanfics/83.1. A.md Fanfics/83.2. B.md
"""
import argparse
import os
import sys

# Reuse from apply_tags
import apply_tags

ENCODING = "utf-8"


def detect_tags_from_content(content, modules):
    """Return list of tags that criteria detect in content (full file text)."""
    tags = []
    for tag, check in modules:
        try:
            if check(content):
                tags.append(tag)
        except Exception as e:
            print("Warning: tag {}: {}".format(tag, e), file=sys.stderr)
    return apply_tags.apply_dc_rule(list(dict.fromkeys(tags)))


def first_line_from_tags(tags):
    """Format first line as in project: Теги: #a #b."""
    return "Теги: " + (" ".join("#" + t for t in tags) if tags else "")


def main():
    parser = argparse.ArgumentParser(
        description="Recalc tags: common file = tags from its content; divergences = common tags + their own."
    )
    parser.add_argument("common", help="Path to common file (N. title.md)")
    parser.add_argument("divergences", nargs="*", help="Paths to divergence files (N.1. ..., N.2. ...)")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    modules = apply_tags.load_criteria_modules(script_dir)
    if not modules:
        print("No criteria modules found in tag_criteria/", file=sys.stderr)
        sys.exit(1)

    common_path = os.path.normpath(args.common)
    if not os.path.isfile(common_path):
        print("Common file not found:", common_path, file=sys.stderr)
        sys.exit(1)

    first_line, content = apply_tags.read_file(common_path)
    tags_common = detect_tags_from_content(content, modules)
    new_first = first_line_from_tags(tags_common)
    rest = content.split("\n", 1)[1] if "\n" in content else ""
    apply_tags.write_first_line(common_path, new_first, rest)
    print("Common:", common_path, "->", new_first)

    for div_path in args.divergences:
        div_path = os.path.normpath(div_path)
        if not os.path.isfile(div_path):
            print("Skip (not found):", div_path, file=sys.stderr)
            continue
        first_line, content = apply_tags.read_file(div_path)
        tags_div = detect_tags_from_content(content, modules)
        merged = list(dict.fromkeys(tags_common + tags_div))
        merged = apply_tags.apply_dc_rule(merged)
        new_first = first_line_from_tags(merged)
        rest = content.split("\n", 1)[1] if "\n" in content else ""
        apply_tags.write_first_line(div_path, new_first, rest)
        print("Divergence:", div_path, "->", new_first)


if __name__ == "__main__":
    main()
