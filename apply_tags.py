# -*- coding: utf-8 -*-
"""Apply tags to .md files using criteria from tag_criteria/.
Usage: python apply_tags.py [folder] [--dry-run]
Default folder: script directory. With --dry-run only prints would-be changes.
"""
import argparse
import importlib.util
import os
import re
import sys

CRITERIA_DIR = "tag_criteria"
ENCODING = "utf-8"


def get_md_files(folder):
    """Return list of .md file paths in folder."""
    paths = []
    for name in os.listdir(folder):
        if name.endswith(".md"):
            paths.append(os.path.join(folder, name))
    return sorted(paths)


def parse_tags_from_first_line(line):
    """Parse tags from first line. Supports 'Теги: #a #b' and bare '#a #b'."""
    if not line or not line.strip():
        return []
    line = line.strip()
    if line.lower().startswith("теги:"):
        line = line[5:].strip()
    tags = re.findall(r"#([^\s#]+)", line)
    return list(dict.fromkeys(tags))


def read_file(path):
    """Return (first_line, full_content)."""
    with open(path, "r", encoding=ENCODING) as f:
        content = f.read()
    if "\n" in content:
        first, rest = content.split("\n", 1)
        return first, content
    return content, content


def write_first_line(path, first_line, rest_content):
    """Write file with new first line and rest unchanged."""
    with open(path, "w", encoding=ENCODING) as f:
        f.write(first_line + "\n" + rest_content)


def load_criteria_modules(folder):
    """Load all .py modules from tag_criteria/ and return list of (tag, check_func)."""
    criteria_path = os.path.join(folder, CRITERIA_DIR)
    if not os.path.isdir(criteria_path):
        return []
    result = []
    for name in sorted(os.listdir(criteria_path)):
        if name.endswith(".py") and not name.startswith("_"):
            mod_path = os.path.join(criteria_path, name)
            if not os.path.isfile(mod_path):
                continue
            spec = importlib.util.spec_from_file_location(
                "tag_criteria." + name[:-3], mod_path
            )
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                print(f"Warning: skip {name}: {e}", file=sys.stderr)
                continue
            tag = getattr(mod, "TAG", None)
            check = getattr(mod, "check", None)
            if tag and callable(check):
                result.append((tag, check))
            else:
                print(f"Warning: {name} has no TAG or check()", file=sys.stderr)
    return result


def apply_dc_rule(tags):
    """If any tag is dc/*, remove 'dc' from the set."""
    has_dc_slash = any(t.startswith("dc/") for t in tags)
    if has_dc_slash:
        tags = [t for t in tags if t != "dc"]
    return tags


def run(folder, dry_run=False):
    """Process all .md in folder; if dry_run, only print changes."""
    modules = load_criteria_modules(os.path.dirname(os.path.abspath(__file__)))
    if not modules:
        print("No criteria modules found in", CRITERIA_DIR, file=sys.stderr)
        return
    md_files = get_md_files(folder)
    if not md_files:
        print("No .md files in", folder)
        return
    for path in md_files:
        first_line, content = read_file(path)
        existing = parse_tags_from_first_line(first_line)
        body = content.split("\n", 1)[1] if "\n" in content else ""
        to_add = []
        for tag, check in modules:
            if tag in existing:
                continue  # already has this tag, skip check (for files with existing tags)
            try:
                if check(content):
                    to_add.append(tag)
            except Exception as e:
                print(f"Warning: {os.path.basename(path)} tag {tag}: {e}", file=sys.stderr)
        merged = list(dict.fromkeys(existing + to_add))
        merged = apply_dc_rule(merged)
        new_first = "Теги: " + (" ".join("#" + t for t in merged) if merged else "")
        if new_first != first_line:
            if dry_run:
                print(path, "->", new_first)
            else:
                rest = content.split("\n", 1)[1] if "\n" in content else ""
                write_first_line(path, new_first, rest)
                print(path)


def main():
    parser = argparse.ArgumentParser(description="Apply tags to .md files from tag_criteria/")
    parser.add_argument("folder", nargs="?", default=None, help="Folder with .md files")
    parser.add_argument("--dry-run", action="store_true", help="Only print changes, do not write")
    args = parser.parse_args()
    folder = args.folder or os.path.dirname(os.path.abspath(__file__))
    if not os.path.isdir(folder):
        print("Not a directory:", folder, file=sys.stderr)
        sys.exit(1)
    run(folder, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
