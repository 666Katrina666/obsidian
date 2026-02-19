# -*- coding: utf-8 -*-
"""Update Иерархия_тегов.md with current tag counts from Fanfics (or given folder).
Preserves everything from '## Правила использования тегов' to end of file.
Usage: python update_tag_hierarchy.py [folder]
Default folder: Fanfics
"""
import os
import re
import argparse

ENCODING = "utf-8"
OUTPUT_FILE = "Иерархия_тегов.md"
TAG_PATTERN = re.compile(r"#([\w\-/.]+)")

# Sections: (section_title, list of (tag, description))
# Description can be None - then we use default or skip
UNIVERSE_DC = [
    ("dc/marvel", "DC x Marvel (основной кроссовер)"),
    ("dc/dp", "DC x Danny Phantom"),
    ("dc/bnha", "DC x My Hero Academia"),
    ("dc/concept/talon", "DC x Суд Сов (концепт)"),
    ("dc/concept/dark_Bruce", "DC с темным Брюсом Уэйном (концепт)"),
    ("dc/ori", "DC x Ori"),
    ("dc/undertale", "DC x Undertale"),
    ("dc", "только DC без кроссовера (редко)"),
]
UNIVERSE_OTHER = [
    ("dsmp", "Dream SMP"),
]
PLOT = [
    ("dimentional_travel", "Путешествия между измерениями"),
    ("time_travel", "Путешествия во времени"),
    ("time_loop", "Временные петли"),
    ("reincarnation", "Реинкарнация персонажей"),
    ("reveal", "Раскрытие тайн и секретов"),
]
TRANSFORMATION = [
    ("wings", "Крылья и полет"),
    ("transformation", "Трансформации между формами"),
    ("de-aging", "Омоложение (взрослый → ребенок)"),
    ("dragon", "Драконьи трансформации"),
]
MAGIC = [
    ("magic", "Магия как основной элемент"),
    ("MahouShoujo", "Подтеги `MahouShoujo/*` учитываются суммарно"),
]
OTHER = [
    ("ABO", "Alpha/Beta/Omega динамика"),
]
EMOTIONAL = [
    ("hurt-comfort", "Боль и утешение"),
    ("trust_issues", "Проблемы с доверием"),
]


def is_valid_tag(tag):
    """Skip numeric and too-short false positives."""
    if tag.isdigit():
        return False
    if len(tag) <= 2:
        return False
    return True


def collect_tags(folder):
    """Walk folder for .md files, extract tags, return (files_with_tags, Counter)."""
    from collections import Counter
    counts = Counter()
    files_with_tags = 0
    for root, _, files in os.walk(folder):
        for name in files:
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, "r", encoding=ENCODING) as f:
                    text = f.read()
            except Exception:
                continue
            found = []
            for m in TAG_PATTERN.finditer(text):
                t = m.group(1)
                if is_valid_tag(t):
                    found.append(t)
            if found:
                files_with_tags += 1
                for t in found:
                    counts[t] += 1
    return files_with_tags, counts


def format_count(n, total_files):
    pct = 100 * n / total_files if total_files else 0
    if n % 10 == 1 and n % 100 != 11:
        word = "раз"
    elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        word = "раза"
    else:
        word = "раз"
    return f"{n} {word} ({pct:.1f}%)"


def build_mahou_subtags(counts):
    subtags = [t for t in counts if t.startswith("MahouShoujo/")]
    return sorted(subtags)


def build_body(files_with_tags, counts):
    total_files = files_with_tags
    top_tag = counts.most_common(1)
    top_name = top_tag[0][0] if top_tag else "—"
    top_n = top_tag[0][1] if top_tag else 0
    top_pct = 100 * top_n / total_files if total_files else 0
    unique = len(counts)

    mahou_subtags = build_mahou_subtags(counts)
    mahou_subtags_str = ", ".join(mahou_subtags) if mahou_subtags else "—"

    sections_lines = []

        # 1. Universe
    sections_lines.append("\n## 1. Вселенные (Universe Tags)\n")
    sections_lines.append("\n### Основная вселенная и кроссоверы DC\n")
    for tag, desc in UNIVERSE_DC:
        n = counts.get(tag, 0)
        if n == 0:
            continue
        sections_lines.append(f"- **{tag}** - {format_count(n, total_files)} - {desc}\n")
    sections_lines.append("\n### Другие вселенные\n")
    for tag, desc in UNIVERSE_OTHER:
        n = counts.get(tag, 0)
        if n == 0:
            continue
        sections_lines.append(f"- **{tag}** - {format_count(n, total_files)} - {desc}\n")
    other_dc = [t for t in sorted(counts) if t.startswith("dc/") and not any(t == x for x, _ in UNIVERSE_DC)]
    for tag in other_dc:
        n = counts[tag]
        sections_lines.append(f"- **{tag}** - {format_count(n, total_files)}\n")

    # 2. Plot
    sections_lines.append("\n## 2. Сюжетные элементы (Plot Tags)\n\n")
    for tag, desc in PLOT:
        n = counts.get(tag, 0)
        if n == 0:
            continue
        sections_lines.append(f"- **{tag}** - {format_count(n, total_files)} - {desc}\n")
    sections_lines.append("\n")

    # 3. Transformation
    sections_lines.append("## 3. Трансформации (Transformation Tags)\n\n")
    for tag, desc in TRANSFORMATION:
        n = counts.get(tag, 0)
        if n == 0:
            continue
        sections_lines.append(f"- **{tag}** - {format_count(n, total_files)} - {desc}\n")
    sections_lines.append("\n")

    # 4. Magic
    sections_lines.append("## 4. Магические элементы (Magic Tags)\n\n")
    for tag, desc in MAGIC:
        n = counts.get(tag, 0)
        if n == 0:
            continue
        sections_lines.append(f"- **{tag}** - {format_count(n, total_files)} - {desc}\n")
    if mahou_subtags:
        sections_lines.append(f"  - {mahou_subtags_str}\n")
    sections_lines.append("\n")

    # 5. Other
    sections_lines.append("## 5. Остальное (Other Tags)\n\n")
    for tag, desc in OTHER:
        n = counts.get(tag, 0)
        if n == 0:
            continue
        sections_lines.append(f"- **{tag}** - {format_count(n, total_files)} - {desc}\n")
    sections_lines.append("\n")

    # 6. Emotional
    sections_lines.append("## 6. Эмоциональные темы (Emotional Tags)\n\n")
    for tag, desc in EMOTIONAL:
        n = counts.get(tag, 0)
        if n == 0:
            continue
        sections_lines.append(f"- **{tag}** - {format_count(n, total_files)} - {desc}\n")
    sections_lines.append("\n")

    # Sort order: collect all tags we listed
    order_universe = ["dc"] + [t for t, _ in UNIVERSE_DC if t != "dc"] + [t for t, _ in UNIVERSE_OTHER]
    order_universe = [t for t in order_universe if counts.get(t, 0) > 0]
    other_dc_order = [t for t in sorted(counts) if t.startswith("dc/") and t not in order_universe]
    order_universe.extend(other_dc_order)
    order_plot = [t for t, _ in PLOT if counts.get(t, 0) > 0]
    order_trans = [t for t, _ in TRANSFORMATION if counts.get(t, 0) > 0]
    order_magic = ["MahouShoujo (и подтеги MahouShoujo/*)", "magic"]
    order_other = [t for t, _ in OTHER if counts.get(t, 0) > 0]
    order_emotional = [t for t, _ in EMOTIONAL if counts.get(t, 0) > 0]

    sections_lines.append("## Порядок сортировки тегов в файлах\n\n")
    sections_lines.append(f"1. **Вселенные и кроссоверы**: {', '.join(order_universe)}\n")
    sections_lines.append(f"2. **Сюжеты**: {', '.join(order_plot)}\n")
    sections_lines.append(f"3. **Трансформации**: {', '.join(order_trans)}\n")
    sections_lines.append(f"4. **Магические элементы**: {', '.join(order_magic)}\n")
    sections_lines.append(f"5. **Остальное**: {', '.join(order_other)}\n")
    sections_lines.append(f"6. **Эмоциональные темы**: {', '.join(order_emotional)}\n")
    sections_lines.append("\n")

    # Top-20 table
    top20 = counts.most_common(20)
    sections_lines.append("## Топ-20 самых популярных тегов\n\n")
    sections_lines.append("| Место | Тег                | Использований | Процент |\n")
    sections_lines.append("| ----- | ------------------ | ------------- | ------- |\n")
    for i, (tag, n) in enumerate(top20, 1):
        pct = 100 * n / total_files if total_files else 0
        sections_lines.append(f"| {i:<5} | {tag:<18} | {n:<13} | {pct:.1f}%   |\n")
    sections_lines.append("\n")

    header = f"""# Иерархия тегов фанфиков

**Общая статистика:**
- Всего файлов с тегами: {total_files}
- Всего уникальных тегов: ~{unique}
- Самый популярный тег: **{top_name}** ({top_n} раз, {top_pct:.1f}%)

"""
    return header + "".join(sections_lines)


def read_tail_from_current_md(path):
    """Return content from '## Правила использования тегов' to end, or None.
    Removes duplicate '## Топ-20 самых популярных тегов' block if present in tail.
    """
    try:
        with open(path, "r", encoding=ENCODING) as f:
            content = f.read()
    except FileNotFoundError:
        return None
    marker = "## Правила использования тегов"
    idx = content.find(marker)
    if idx == -1:
        return None
    tail = content[idx:]
    # Remove duplicate Top-20 section (between Правила and Жесткие требования)
    top20_marker = "\n## Топ-20 самых популярных тегов\n"
    if top20_marker in tail:
        before, rest = tail.split(top20_marker, 1)
        # Rest: table lines then \n## or end. Drop until next ##
        next_sec = rest.find("\n## ")
        if next_sec != -1:
            tail = before + rest[next_sec:]
        else:
            tail = before.rstrip() + "\n"
    return tail.rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Update Иерархия_тегов.md with tag stats")
    parser.add_argument("folder", nargs="?", default="Fanfics", help="Folder with .md files (default: Fanfics)")
    args = parser.parse_args()
    folder = args.folder
    if not os.path.isdir(folder):
        print(f"Error: folder not found: {folder}")
        return 1
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder_abs = os.path.join(script_dir, folder) if not os.path.isabs(folder) else folder
    output_path = os.path.join(script_dir, OUTPUT_FILE)

    files_with_tags, counts = collect_tags(folder_abs)
    body = build_body(files_with_tags, counts)
    tail = read_tail_from_current_md(output_path)
    if tail is None:
        tail = """## Правила использования тегов

### Составные теги
- Составные теги типа `#dc/dp`, `#dc/bnha`, `#dc/concept/talon` **НЕ РАЗДЕЛЯЮТСЯ** на отдельные теги
- Тег `#dc` **НЕ ДОБАВЛЯЕТСЯ** если есть составной тег с `dc/`
- Подтеги `MahouShoujo/*` учитываются суммарно как один тег `MahouShoujo` (при необходимости можно указывать конкретный подтег, например `#MahouShoujo/TokyoMewMew`)

### Примеры правильного использования
- `#dc/dp #dc/marvel #wings #reveal` - кроссовер DC/Danny Phantom и Marvel
- `#dc/marvel #dc/concept/talon #time_travel` - DC/Marvel со Судом Сов
- `#dc/marvel #transformation #wings` - только DC/Marvel, без других кроссоверов
- `#dc #dc/dp #wings` - неправильно, дублирование вселенной
- `#dc/marvel` без дополнительных тегов - желательно добавить сюжетные теги
"""

    with open(output_path, "w", encoding=ENCODING) as f:
        f.write(body)
        f.write(tail)
    print(f"Updated {OUTPUT_FILE} (scanned {files_with_tags} files, {len(counts)} unique tags)")
    return 0


if __name__ == "__main__":
    exit(main())
