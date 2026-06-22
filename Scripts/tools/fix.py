import os
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

_FANFICS = vault_root(__file__) / "Fanfics"


def remove_links(line):
    pattern = r"\[([^\]]+)\]\([^\)]+\)"
    line = re.sub(pattern, r"\1", line)
    return line


def fix_paragraphs_line(line):
    pattern1 = r"([.!?…»])([A-ZА-ЯЁ—a-zа-яё«\"])"
    line = re.sub(pattern1, r"\1\n\n\2", line)
    pattern2 = r"([a-zа-яё])([A-ZА-ЯЁ])"
    line = re.sub(pattern2, r"\1\n\n\2", line)
    return line


def process_file(input_path):
    base, ext = os.path.splitext(input_path)
    output_path = base + " fixed" + ext
    with open(input_path, encoding="utf-8") as infile, open(
        output_path, "w", encoding="utf-8"
    ) as outfile:
        for lineno, line in enumerate(infile):
            if lineno < 7:
                outfile.write(line)
            else:
                if line.strip():
                    line_without_links = remove_links(line.rstrip())
                    fixed_line = fix_paragraphs_line(line_without_links)
                    outfile.write(fixed_line + "\n")
                else:
                    outfile.write("\n")
    print(f"Done! Fixed text saved to {output_path}")


def process_range(start_num, end_num, directory: Path) -> None:
    for n in range(start_num, end_num + 1):
        input_path = directory / f"{n}.md"
        if not input_path.exists():
            print(f"Skip: file not found {input_path}")
            continue
        process_file(str(input_path))


def print_usage():
    print("Usage:")
    print("  python fix.py path_to_file.md")
    print("  python fix.py START-END   # Fanfics/START.md … END.md")
    print("  python fix.py START END")
    print("  python fix.py N           # Fanfics/N.md")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
    else:
        arg1 = sys.argv[1]
        if len(sys.argv) == 2 and "-" in arg1:
            try:
                start_str, end_str = arg1.split("-", 1)
                start_num = int(start_str)
                end_num = int(end_str)
                if start_num > end_num:
                    start_num, end_num = end_num, start_num
                process_range(start_num, end_num, _FANFICS)
            except ValueError:
                print_usage()
        elif len(sys.argv) == 3:
            try:
                start_num = int(sys.argv[1])
                end_num = int(sys.argv[2])
                if start_num > end_num:
                    start_num, end_num = end_num, start_num
                process_range(start_num, end_num, _FANFICS)
            except ValueError:
                print_usage()
        else:
            try:
                n = int(arg1)
                process_file(str(_FANFICS / f"{n}.md"))
            except ValueError:
                process_file(arg1)
