# -*- coding: utf-8 -*-
"""Интерактивное меню: Beta ↔ Fanfics (DeepSeek JSON, ручные файлы, сверка, утилиты)."""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

_SCRIPTS_FANFICS = Path(__file__).resolve().parent
OBSIDIAN_ROOT = vault_root(__file__)
_SCRIPTS_TAGS = OBSIDIAN_ROOT / "Scripts" / "tags"
BETA_DIR = OBSIDIAN_ROOT / "Beta"
FANFICS_DIR = OBSIDIAN_ROOT / "Fanfics"
PLAN_NOTE = OBSIDIAN_ROOT / "План_Beta_Fanfics.md"
DEDUP_REPORT = OBSIDIAN_ROOT / "Beta_vs_Fanfics_dedup_report.md"
PARTIAL_REPORT = OBSIDIAN_ROOT / "Beta_vs_Fanfics_partial_report.md"
PARTIAL_FANFICS_ONLY_REPORT = OBSIDIAN_ROOT / "Fanfics_partial_overlap_report.md"
PREPARE_BETA_SCRIPT = _SCRIPTS_FANFICS / "prepare_beta_batch.py"
PARTIAL_MATCH_MIN_PARAGRAPH_CHARS = 250
PARTIAL_PARAGRAPH_DISPLAY_MAX = 800
PARTIAL_MAX_FRAGMENTS_PER_PAIR = 3

EXPORT_SCRIPT = _SCRIPTS_FANFICS / "export_deepseek_chats.py"
UPDATE_LINKS_SCRIPT = _SCRIPTS_FANFICS / "update_links.py"
RENUMBER_SCRIPT = _SCRIPTS_FANFICS / "renumber_fanfics.py"
FANFIC_TAGS_SCRIPT = _SCRIPTS_TAGS / "fanfic_tags.py"

HEADER_TEMPLATE = """Теги: 

Описание: 

---
"""


def plan_note_body() -> str:
    return """# План: Beta → Fanfics

Чеклист (отмечайте по мере работы):

- [ ] **Вход:** либо экспорт DeepSeek JSON в Beta (п. меню оркестратора), либо вручную создать `.md` в папке `Beta/` (Kimi, ChatGPT и т.д.)
- [ ] **Шапка:** в каждом файле блок `Теги:` / `Описание:` / `---` (оркестратор может вставить шаблон)
- [ ] **Имена:** осмысленно переименовать черновики (`N. Краткое название.md`); для веток одного сюжета — `N.1. …`, `N.2. …` в Fanfics
- [ ] **Сверка идентичных:** меню 5 → `Beta_vs_Fanfics_dedup_report.md`; меню 11 → удаление полных дубликатов из Beta
- [ ] **Частичные совпадения:** меню 12 → `Beta_vs_Fanfics_partial_report.md`; меню 14 → только `Fanfics/` (без пар N↔N.k и N.k↔N.m одного N)
- [ ] **Пропуски номеров в Beta:** меню 13 → перенумерация файлов вида `N. …`
- [ ] **Теги:** меню 6 → `fanfic_tags.py apply Beta` (сначала dry-run по желанию)
- [ ] **Решения:** для каждого файла зафиксировать: новый номер / дубль / ветка `N.k`
- [ ] **Перенос:** из Beta в `Fanfics/` (вручную или пункт меню оркестратора)
- [ ] **Ссылки:** после появления `N.k` запустить `Scripts/fanfics/update_links.py`
- [ ] **Нумерация:** при необходимости `python Scripts/fanfics/renumber_fanfics.py --dry-run`

Пути:

- Папка Beta: `Beta/`
- Fanfics: `Fanfics/`
- Скрипты: `Scripts/fanfics/`, теги: `Scripts/tags/fanfic_tags.py`

Запуск оркестратора (из корня хранилища):

```text
python Scripts/fanfics/beta_fanfics_orchestrator.py
```
"""


def ensure_beta_and_plan() -> None:
    BETA_DIR.mkdir(parents=True, exist_ok=True)
    if not PLAN_NOTE.is_file():
        PLAN_NOTE.write_text(plan_note_body(), encoding="utf-8")
        print(f"Создан файл плана: {PLAN_NOTE}")
    else:
        print(f"План уже есть: {PLAN_NOTE}")
    print(f"Папка Beta: {BETA_DIR}")


def prompt_line(msg: str, default: str | None = None) -> str:
    tail = f" [{default}]" if default else ""
    s = input(f"{msg}{tail}: ").strip()
    if not s and default is not None:
        return default
    return s


def parse_index_ranges(spec: str, n_files: int) -> list[int]:
    spec = spec.strip()
    if not spec:
        return []
    out: set[int] = set()
    for part in re.split(r"\s*,\s*", spec):
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            try:
                lo = int(a.strip())
                hi = int(b.strip())
            except ValueError:
                return []
            if lo > hi:
                lo, hi = hi, lo
            for k in range(lo, hi + 1):
                if 1 <= k <= n_files:
                    out.add(k)
        else:
            try:
                k = int(part.strip())
            except ValueError:
                return []
            if 1 <= k <= n_files:
                out.add(k)
    return sorted(out)


def list_beta_md_files() -> list[Path]:
    if not BETA_DIR.is_dir():
        return []
    return sorted(BETA_DIR.glob("*.md"))


def has_tags_header(text: str) -> bool:
    return text.lstrip("\ufeff").lstrip().lower().startswith("теги:")


def run_export_json() -> None:
    path = prompt_line("Путь к conversations.json")
    if not path:
        print("Отмена.")
        return
    p = Path(path)
    if not p.is_file():
        print(f"Файл не найден: {p}")
        return
    cmd = [
        sys.executable,
        str(EXPORT_SCRIPT),
        "--out",
        str(BETA_DIR),
        "--fanfics",
        str(FANFICS_DIR),
        str(p),
    ]
    print("Запуск:", " ".join(cmd))
    subprocess.run(cmd, cwd=str(OBSIDIAN_ROOT), check=False)


def manual_beta_help() -> None:
    print(
        "\nРучной сценарий (Kimi / GPT и т.д.):\n"
        "1. Создайте новый файл в папке Beta (или вставьте текст в существующий).\n"
        "2. В меню выберите «Вставить шаблон шапки» при необходимости.\n"
        "3. Переименуйте файл в формат «N. Название.md», где N больше максимума в Fanfics "
        "(см. пункт «Показать следующий свободный номер»).\n"
    )


def next_free_parent_number() -> int:
    import importlib.util

    if not EXPORT_SCRIPT.is_file():
        raise FileNotFoundError(str(EXPORT_SCRIPT))
    spec = importlib.util.spec_from_file_location("export_deepseek_chats", EXPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load export_deepseek_chats")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.next_export_index(str(FANFICS_DIR), str(BETA_DIR)))


def add_header_to_beta_file() -> None:
    files = list_beta_md_files()
    if not files:
        print("В Beta нет .md файлов.")
        return
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")
    raw = prompt_line('Номера: одно число или список "1, 5-10, 15" (Enter — отмена)', "")
    if not raw:
        print("Отмена.")
        return
    indices = parse_index_ranges(raw, len(files))
    if not indices and re.fullmatch(r"\d+", raw.strip()):
        k = int(raw.strip())
        if 1 <= k <= len(files):
            indices = [k]
    if not indices:
        print("Неверный формат или пустой список.")
        return
    skip_existing = prompt_line("Пропускать файлы, где уже есть строка Теги:? (y/n)", "y").lower() == "y"
    done = 0
    skipped = 0
    for idx in indices:
        path = files[idx - 1]
        text = path.read_text(encoding="utf-8")
        if has_tags_header(text):
            if skip_existing:
                print(f"  пропуск (уже шапка): {path.name}")
                skipped += 1
                continue
            if prompt_line(f"У {path.name} уже есть Теги:. Вставить шаблон сверху? (y/n)", "n").lower() != "y":
                skipped += 1
                continue
        path.write_text(HEADER_TEMPLATE + text, encoding="utf-8")
        print(f"  OK: {path.name}")
        done += 1
    print(f"Готово: обновлено {done}, пропущено {skipped}.")


def body_after_first_separator(content: str) -> str:
    sep = "\n---\n"
    pos = content.find(sep)
    if pos == -1:
        return content
    return content[pos + len(sep) :]


def file_body_hash(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    body = body_after_first_separator(raw)
    norm = " ".join(body.split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def obsidian_wikilink(folder: str, filename: str) -> str:
    """[[Folder/Title]] без расширения .md — кликабельно в Obsidian."""
    base = filename[:-3] if filename.endswith(".md") else filename
    base = base.replace("|", "—")
    return f"[[{folder}/{base}]]"


def numeric_id_from_filename(name: str) -> str | None:
    """
    Возвращает числовой ID из имени:
    - `190. Название.md` -> `190`
    - `190.1. Название.md` -> `190.1`
    """
    m = re.match(r"^(\d+)(?:\.(\d+))?[\. ]", name)
    if not m:
        return None
    major = m.group(1)
    minor = m.group(2)
    return f"{major}.{minor}" if minor is not None else major


def numeric_id_sort_key(s: str) -> tuple[int, int]:
    if "." in s:
        a, b = s.split(".", 1)
        return int(a), int(b)
    return int(s), -1


def candidate_groups_from_edges(edges: set[tuple[str, str]]) -> list[list[str]]:
    """Связные компоненты по парам ID; берём только группы размером >= 2."""
    graph: dict[str, set[str]] = {}
    for a, b in edges:
        if a == b:
            continue
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)

    groups: list[list[str]] = []
    seen: set[str] = set()
    for node in sorted(graph.keys(), key=numeric_id_sort_key):
        if node in seen:
            continue
        stack = [node]
        comp: list[str] = []
        seen.add(node)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in graph.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        comp_sorted = sorted(comp, key=numeric_id_sort_key)
        if len(comp_sorted) >= 2:
            groups.append(comp_sorted)
    return groups


def run_dedup_report() -> None:
    lines = [
        "# Beta vs Fanfics — совпадения по хэшу тела (после первого `---`)",
        "",
        "Критерий: SHA-256 нормализованного текста тела (пробелы схлопнуты). Ниже — **wikilink-и** для быстрой проверки.",
        "",
    ]

    beta_files = list_beta_md_files()

    lines.append("## Part A: дубликаты внутри Beta")
    lines.append("")
    if not beta_files:
        lines.append("_В Beta нет .md файлов._")
        lines.append("")
    else:
        beta_by_hash: dict[str, list[str]] = {}
        for f in beta_files:
            beta_by_hash.setdefault(file_body_hash(f), []).append(f.name)
        dup_groups = [names for names in beta_by_hash.values() if len(names) > 1]
        if not dup_groups:
            lines.append("_Нет двух файлов в Beta с одинаковым хэшем тела._")
            lines.append("")
        else:
            lines.append(f"**Групп с одинаковым телом (2+ файла):** {len(dup_groups)}")
            lines.append("")
            for names in sorted(dup_groups, key=lambda xs: (xs[0].lower(), len(xs))):
                first = obsidian_wikilink("Beta", names[0])
                lines.append(f"- **{first}** — то же тело, что и:")
                for x in sorted(names[1:], key=str.lower):
                    lines.append(f"  - {obsidian_wikilink('Beta', x)}")
                lines.append("")

    lines.append("## Part B: Beta vs Fanfics")
    lines.append("")
    if not FANFICS_DIR.is_dir():
        lines.append(f"_Нет папки Fanfics: `{FANFICS_DIR}`_")
        lines.append("")
    elif not beta_files:
        lines.append("_Нет файлов в Beta для сравнения._")
        lines.append("")
    else:
        fan_hashes: dict[str, list[str]] = {}
        for f in FANFICS_DIR.glob("*.md"):
            if f.name.lower() == "rename_plan.md":
                continue
            h = file_body_hash(f)
            fan_hashes.setdefault(h, []).append(f.name)

        dup_count = 0
        detail: list[str] = []
        for bf in beta_files:
            h = file_body_hash(bf)
            matches = fan_hashes.get(h, [])
            if not matches:
                continue
            dup_count += 1
            detail.append(f"### Beta: {obsidian_wikilink('Beta', bf.name)}")
            detail.append("")
            detail.append("Совпадает с Fanfics:")
            for m in matches:
                detail.append(f"- {obsidian_wikilink('Fanfics', m)}")
            detail.append("")

        lines.append(f"**Файлов Beta с совпадением в Fanfics:** {dup_count}")
        lines.append("")
        if dup_count == 0:
            lines.append("_Ни один файл Beta по этому хэшу не совпал с Fanfics._")
            lines.append("")
        lines.extend(detail)

    DEDUP_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Готово: {DEDUP_REPORT}")


def normalize_paragraph_text(s: str) -> str:
    return " ".join(s.split()).strip()


def get_long_paragraphs_by_chars(body: str, min_chars: int) -> list[str]:
    """Абзацы по пустым строкам; длина по нормализованной строке >= min_chars."""
    if not body or not body.strip():
        return []
    lines = body.split("\n")
    out: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        else:
            if current:
                n = normalize_paragraph_text(" ".join(current))
                if len(n) >= min_chars:
                    out.append(n)
                current = []
    if current:
        n = normalize_paragraph_text(" ".join(current))
        if len(n) >= min_chars:
            out.append(n)
    return out


def beta_filename_sort_key(name: str) -> tuple:
    """Меньший номер в имени — приоритет при «оставить один» дубликат в Beta."""
    m = re.match(r"^(\d+)(?:\.(\d+))?[\. ]", name)
    if m:
        return (0, int(m.group(1)), int(m.group(2) or 0), name.lower())
    return (1, 0, 0, name.lower())


def collect_identical_beta_deletions() -> tuple[set[str], str]:
    """
    Имена .md в Beta, которые стоит удалить:
    - тело (после ---) совпадает с каким-либо Fanfics;
    - лишние копии внутри Beta (один файл на хэш оставляем с минимальным N/N.k).
    """
    beta_files = list_beta_md_files()
    if not beta_files:
        return set(), "В Beta нет .md файлов."

    fan_body_hashes: set[str] = set()
    if FANFICS_DIR.is_dir():
        for f in FANFICS_DIR.glob("*.md"):
            if f.name.lower() == "rename_plan.md":
                continue
            fan_body_hashes.add(file_body_hash(f))

    to_delete: set[str] = set()

    for bf in beta_files:
        if file_body_hash(bf) in fan_body_hashes:
            to_delete.add(bf.name)

    by_hash: dict[str, list[str]] = {}
    for bf in beta_files:
        by_hash.setdefault(file_body_hash(bf), []).append(bf.name)

    for _h, names in by_hash.items():
        if len(names) < 2:
            continue
        remaining = [n for n in names if n not in to_delete]
        if len(remaining) > 1:
            keeper = min(remaining, key=beta_filename_sort_key)
            for n in remaining:
                if n != keeper:
                    to_delete.add(n)

    n_fan = sum(
        1
        for bf in beta_files
        if bf.name in to_delete and file_body_hash(bf) in fan_body_hashes
    )
    n_intra_only = len(to_delete) - n_fan
    summary = (
        f"К удалению: {len(to_delete)} файл(ов) "
        f"(полное совпадение с Fanfics: {n_fan}; лишние дубли только внутри Beta: {n_intra_only})."
    )
    return to_delete, summary


def delete_identical_beta_files() -> None:
    to_delete, summary = collect_identical_beta_deletions()
    print(summary)
    if not to_delete:
        if "нет .md" not in summary.lower():
            print("Нечего удалять (нет полных дубликатов по этим правилам).")
        return
    for name in sorted(to_delete):
        print(f"  - {name}")
    if prompt_line("Удалить перечисленные файлы из Beta? (y/n)", "n").lower() != "y":
        print("Отмена.")
        return
    for name in to_delete:
        p = BETA_DIR / name
        if p.is_file():
            p.unlink()
            print(f"Удалено: {name}")
    print("Готово.")


def run_partial_match_report() -> None:
    from collections import defaultdict

    min_c = PARTIAL_MATCH_MIN_PARAGRAPH_CHARS
    max_show = PARTIAL_PARAGRAPH_DISPLAY_MAX
    beta_files = list_beta_md_files()
    lines = [
        "# Beta vs Fanfics — частичные совпадения (длинные абзацы)",
        "",
        f"Учитываются только абзацы длиной **≥ {min_c}** символов после нормализации пробелов (одна строка). "
        "Короткие реплики вроде «— Да — сказал он.» отбрасываются. У каждой пары и у каждого фрагмента — **wikilink-и** на оба файла. "
        f"На пару не больше **{PARTIAL_MAX_FRAGMENTS_PER_PAIR}** самых длинных общих абзацев.",
        "",
    ]

    if not FANFICS_DIR.is_dir():
        lines.append(f"_Нет папки Fanfics: `{FANFICS_DIR}`_")
        PARTIAL_REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Готово: {PARTIAL_REPORT}")
        return

    fan_index: dict[str, set[str]] = defaultdict(set)
    for f in FANFICS_DIR.glob("*.md"):
        if f.name.lower() == "rename_plan.md":
            continue
        raw = f.read_text(encoding="utf-8")
        body = body_after_first_separator(raw)
        for para in get_long_paragraphs_by_chars(body, min_c):
            fan_index[para].add(f.name)

    if not beta_files:
        lines.append("_В Beta нет .md файлов._")
        PARTIAL_REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Готово: {PARTIAL_REPORT}")
        return

    pair_paras: dict[tuple[str, str], set[str]] = defaultdict(set)
    for bf in beta_files:
        raw = bf.read_text(encoding="utf-8")
        body = body_after_first_separator(raw)
        for para in get_long_paragraphs_by_chars(body, min_c):
            for ff in fan_index.get(para, ()):
                pair_paras[(bf.name, ff)].add(para)

    if not pair_paras:
        lines.append("_Нет пар Beta–Fanfics с общим длинным абзацем (по этому критерию)._")
        lines.append("")
        PARTIAL_REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Готово: {PARTIAL_REPORT}")
        return

    lines.append(f"**Найдено пар (Beta файл, Fanfics файл) с хотя бы одним общим абзацем:** {len(pair_paras)}")
    lines.append("")

    # Мини-обзор кандидатов только по числовым ID.
    # ID берём из имён Beta и Fanfics, потом группируем по связным компонентам.
    edges: set[tuple[str, str]] = set()
    for (bname, fname) in pair_paras.keys():
        bid = numeric_id_from_filename(bname)
        fid = numeric_id_from_filename(fname)
        if bid and fid and bid != fid:
            a, b = (bid, fid) if numeric_id_sort_key(bid) <= numeric_id_sort_key(fid) else (fid, bid)
            edges.add((a, b))
    groups = candidate_groups_from_edges(edges)
    if groups:
        lines.append("## Мини-обзор кандидатов на объединение (по номерам)")
        lines.append("")
        for g in groups:
            lines.append(f"- {', '.join(g)} - вариации одного сюжета")
        lines.append("")

    for (bname, fname) in sorted(pair_paras.keys(), key=lambda t: (t[0].lower(), t[1].lower())):
        wl_b = obsidian_wikilink("Beta", bname)
        wl_f = obsidian_wikilink("Fanfics", fname)
        lines.append(f"### {wl_b} — {wl_f}")
        lines.append("")
        lines.append("**Ссылки на пару (для проверки):**")
        lines.append(f"- Beta: {wl_b}")
        lines.append(f"- Fanfics: {wl_f}")
        lines.append("")
        paras = sorted(pair_paras[(bname, fname)], key=len, reverse=True)[
            :PARTIAL_MAX_FRAGMENTS_PER_PAIR
        ]
        for i, para in enumerate(paras, 1):
            excerpt = para if len(para) <= max_show else para[:max_show] + "…"
            lines.append(f"- **Фрагмент {i}** ({len(para)} симв.)")
            lines.append(f"  - Beta: {wl_b}")
            lines.append(f"  - Fanfics: {wl_f}")
            lines.append("")
            lines.append("```")
            lines.append(excerpt.replace("```", "'''"))
            lines.append("```")
            lines.append("")
        lines.append("---")
        lines.append("")

    PARTIAL_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Готово: {PARTIAL_REPORT}")


def fanfics_parse_branch(name: str) -> tuple[int, int | None] | None:
    """Родитель N и ветка k для `N.k. …`; для `N. Заголовок` — (N, None). Иначе None."""
    m = re.match(r"^(\d+)\.(\d+)[\. ]", name)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"^(\d+)\.\s", name)
    if m:
        return int(m.group(1)), None
    return None


def skip_fanfics_intentional_split_pair(name_a: str, name_b: str) -> bool:
    """
    True — не сравнивать: осознанное разбиение одного номера N в Fanfics.
    - N.k и N.m при одном N (две ветки);
    - N. Заголовок и N.k (родитель и ветка того же N).
    Пара 190.1 и 674 — сравниваем; 190 и 190.1 — нет.
    """
    pa = fanfics_parse_branch(name_a)
    pb = fanfics_parse_branch(name_b)
    if pa is None or pb is None:
        return False
    na, ka = pa
    nb, kb = pb
    if na != nb:
        return False
    if ka is not None and kb is not None:
        return True
    if (ka is None) != (kb is None):
        return True
    return False


def run_fanfics_internal_partial_report() -> None:
    """Частичные совпадения только между файлами Fanfics; пропуск связанных N / N.k / N.m."""
    min_c = PARTIAL_MATCH_MIN_PARAGRAPH_CHARS
    max_show = PARTIAL_PARAGRAPH_DISPLAY_MAX
    lines = [
        "# Fanfics — частичные совпадения между файлами (длинные абзацы)",
        "",
        f"Только папка **Fanfics**. Абзацы **≥ {min_c}** символов. "
        "**Не** сравниваются пары одного номера **N**: **N.k** с **N.m**, а также **N.** (родитель) с **N.k**. "
        f"На пару не больше **{PARTIAL_MAX_FRAGMENTS_PER_PAIR}** фрагментов.",
        "",
    ]

    if not FANFICS_DIR.is_dir():
        lines.append(f"_Нет папки Fanfics: `{FANFICS_DIR}`_")
        PARTIAL_FANFICS_ONLY_REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Готово: {PARTIAL_FANFICS_ONLY_REPORT}")
        return

    from collections import defaultdict

    fan_index: dict[str, set[str]] = defaultdict(set)
    fan_names: list[str] = []
    for f in sorted(FANFICS_DIR.glob("*.md")):
        if f.name.lower() == "rename_plan.md":
            continue
        fan_names.append(f.name)
        raw = f.read_text(encoding="utf-8")
        body = body_after_first_separator(raw)
        for para in get_long_paragraphs_by_chars(body, min_c):
            fan_index[para].add(f.name)

    if len(fan_names) < 2:
        lines.append("_В Fanfics меньше двух подходящих .md файлов._")
        PARTIAL_FANFICS_ONLY_REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Готово: {PARTIAL_FANFICS_ONLY_REPORT}")
        return

    pair_paras: dict[tuple[str, str], set[str]] = defaultdict(set)
    for _para, owners in fan_index.items():
        if len(owners) < 2:
            continue
        owners_sorted = sorted(owners)
        for i in range(len(owners_sorted)):
            for j in range(i + 1, len(owners_sorted)):
                a, b = owners_sorted[i], owners_sorted[j]
                if skip_fanfics_intentional_split_pair(a, b):
                    continue
                key = (a, b) if a < b else (b, a)
                pair_paras[key].add(_para)

    if not pair_paras:
        lines.append("_Нет пар файлов Fanfics с общим длинным абзацем (после фильтра веток)._")
        lines.append("")
        PARTIAL_FANFICS_ONLY_REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Готово: {PARTIAL_FANFICS_ONLY_REPORT}")
        return

    lines.append(f"**Найдено пар файлов:** {len(pair_paras)}")
    lines.append("")

    # Мини-обзор кандидатов внутри Fanfics только по числовым ID.
    edges: set[tuple[str, str]] = set()
    for (name_a, name_b) in pair_paras.keys():
        id_a = numeric_id_from_filename(name_a)
        id_b = numeric_id_from_filename(name_b)
        if id_a and id_b and id_a != id_b:
            a, b = (id_a, id_b) if numeric_id_sort_key(id_a) <= numeric_id_sort_key(id_b) else (id_b, id_a)
            edges.add((a, b))
    groups = candidate_groups_from_edges(edges)
    if groups:
        lines.append("## Мини-обзор кандидатов на объединение (по номерам)")
        lines.append("")
        for g in groups:
            lines.append(f"- {', '.join(g)} - вариации одного сюжета")
        lines.append("")

    for (name_a, name_b) in sorted(pair_paras.keys(), key=lambda t: (t[0].lower(), t[1].lower())):
        wl_a = obsidian_wikilink("Fanfics", name_a)
        wl_b = obsidian_wikilink("Fanfics", name_b)
        lines.append(f"### {wl_a} — {wl_b}")
        lines.append("")
        lines.append("**Ссылки:**")
        lines.append(f"- {wl_a}")
        lines.append(f"- {wl_b}")
        lines.append("")
        paras = sorted(pair_paras[(name_a, name_b)], key=len, reverse=True)[
            :PARTIAL_MAX_FRAGMENTS_PER_PAIR
        ]
        for i, para in enumerate(paras, 1):
            excerpt = para if len(para) <= max_show else para[:max_show] + "…"
            lines.append(f"- **Фрагмент {i}** ({len(para)} симв.)")
            lines.append(f"  - Fanfics: {wl_a}")
            lines.append(f"  - Fanfics: {wl_b}")
            lines.append("")
            lines.append("```")
            lines.append(excerpt.replace("```", "'''"))
            lines.append("```")
            lines.append("")
        lines.append("---")
        lines.append("")

    PARTIAL_FANFICS_ONLY_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Готово: {PARTIAL_FANFICS_ONLY_REPORT}")


def run_subprocess_script(script: Path, extra_args: list[str] | None = None) -> None:
    if not script.is_file():
        print(f"Скрипт не найден: {script}")
        return
    cmd = [sys.executable, str(script)]
    if extra_args:
        cmd.extend(extra_args)
    print("Запуск:", " ".join(cmd))
    subprocess.run(cmd, cwd=str(OBSIDIAN_ROOT), check=False)


def run_apply_tags_beta() -> None:
    if not FANFIC_TAGS_SCRIPT.is_file():
        print(f"Не найден: {FANFIC_TAGS_SCRIPT}")
        return
    dry = prompt_line("Сначала dry-run (только показать изменения)? (y/n)", "y").lower() == "y"
    extra = ["apply", str(BETA_DIR)]
    if dry:
        extra.append("--dry-run")
    run_subprocess_script(FANFIC_TAGS_SCRIPT, extra)
    if dry and prompt_line("Записать теги на диск (без dry-run)? (y/n)", "n").lower() == "y":
        run_subprocess_script(FANFIC_TAGS_SCRIPT, ["apply", str(BETA_DIR)])


def _valid_fanfics_filename(name: str) -> bool:
    if not name or not name.endswith(".md"):
        return False
    if re.search(r'[<>:"/\\\\|?*]', name):
        return False
    return True


def move_beta_to_fanfics() -> None:
    files = list_beta_md_files()
    if not files:
        print("В Beta нет .md файлов.")
        return
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")
    raw = prompt_line('Номера для переноса: одно число или "1, 5-10, 15" (Enter — отмена)', "")
    if not raw:
        print("Отмена.")
        return
    indices = parse_index_ranges(raw, len(files))
    if not indices and re.fullmatch(r"\d+", raw.strip()):
        k = int(raw.strip())
        if 1 <= k <= len(files):
            indices = [k]
    if not indices:
        print("Неверный формат или пустой список.")
        return

    FANFICS_DIR.mkdir(parents=True, exist_ok=True)
    use_same_name = False
    if len(indices) > 1:
        use_same_name = prompt_line("Несколько файлов: сохранить те же имена в Fanfics? (y/n)", "y").lower() == "y"

    for idx in indices:
        src = files[idx - 1]
        print(f"\n--- {src.name} ---")
        if use_same_name:
            new_name = src.name
        else:
            new_name = prompt_line("Имя в Fanfics (только имя, например 842. Title.md)")
        if not _valid_fanfics_filename(new_name):
            print("Пропуск: нужно имя *.md без недопустимых символов.")
            continue
        dst = FANFICS_DIR / new_name
        if dst.exists():
            if prompt_line(f"Уже есть {dst.name}. Перезаписать? (y/n)", "n").lower() != "y":
                print("Пропуск.")
                continue
        shutil.move(str(src), str(dst))
        print(f"Перенесено -> {dst}")


def renumber_beta_fill_gaps() -> None:
    """
    Перенумеровать в Beta только файлы вида «N. Название.md» (один родительский номер),
    подряд без пропусков. Файлы «N.k. …» не трогаем.
    """
    all_md = list_beta_md_files()
    parents: list[tuple[int, str, Path]] = []
    skipped_sub: list[str] = []
    skipped_other: list[str] = []
    for p in all_md:
        name = p.name
        if re.match(r"^\d+\.\d+[\. ]", name):
            skipped_sub.append(name)
            continue
        m = re.match(r"^(\d+)\.\s(.+)$", name)
        if not m:
            skipped_other.append(name)
            continue
        parents.append((int(m.group(1)), m.group(2), p))

    if skipped_sub:
        print(f"Не трогаем файлы вида N.k. (штук: {len(skipped_sub)}).")
    if skipped_other:
        print(f"Пропуск (не шаблон «N. пробел …»): {len(skipped_other)} файл(ов).")

    if not parents:
        print("Нет файлов «N. Название.md» для перенумерации.")
        return

    parents.sort(key=lambda x: x[0])
    start_default = parents[0][0]
    start_s = prompt_line(f"Первый номер после перенумерации (Enter = {start_default})", "")
    if start_s.isdigit():
        start = int(start_s)
    elif not start_s.strip():
        start = start_default
    else:
        print("Нужно целое число или Enter.")
        return

    paths = [p for _, _, p in parents]
    final_names = [f"{start + i}. {title}" for i, (_, title, _) in enumerate(parents)]

    parent_set = {p.resolve() for _, _, p in parents}
    for fn in final_names:
        dest = BETA_DIR / fn
        if dest.exists() and dest.resolve() not in parent_set:
            print(f"Конфликт: уже есть файл вне списка перенумерации: {fn}")
            return

    if all(paths[i].name == final_names[i] for i in range(len(paths))):
        print("Пропусков в нумерации нет — переименование не требуется.")
        return

    print("План:")
    for (_, _, p), fn in zip(parents, final_names):
        if p.name != fn:
            print(f"  {p.name}")
            print(f"    -> {fn}")
    if prompt_line("Применить переименование? (y/n)", "n").lower() != "y":
        print("Отмена.")
        return

    tmps: list[Path] = []
    for i, p in enumerate(paths):
        tp = BETA_DIR / f"__beta_renum_{i:04d}.md"
        if tp.exists():
            print(f"Ошибка: уже существует {tp.name} — удалите вручную и повторите.")
            return
        shutil.move(str(p), str(tp))
        tmps.append(tp)
    for tp, fn in zip(tmps, final_names):
        shutil.move(str(tp), str(BETA_DIR / fn))
        print(f"OK: {fn}")
    print("Готово.")


def print_paths() -> None:
    print(f"Obsidian: {OBSIDIAN_ROOT}")
    print(f"Beta:     {BETA_DIR}")
    print(f"Fanfics:  {FANFICS_DIR}")
    print(f"План:     {PLAN_NOTE}")
    print(f"Отчёт 1:1: {DEDUP_REPORT}")
    print(f"Отчёт частичн. Beta: {PARTIAL_REPORT}")
    print(f"Отчёт частичн. Fanfics: {PARTIAL_FANFICS_ONLY_REPORT}")


def main_menu() -> None:
    ensure_beta_and_plan()
    while True:
        print(
            "\n=== Beta / Fanfics orchestrator ===\n"
            "1. Export DeepSeek JSON -> Beta\n"
            "2. Подсказка: ручные файлы в Beta (Kimi / GPT)\n"
            "3. Вставить шаблон шапки в Beta (номера: 1, 5-10, 15)\n"
            "4. Показать пути и следующий свободный родительский номер\n"
            "5. Отчёт: идентичные тела (hash) Beta/Beta + Beta/Fanfics -> .md\n"
            "6. Apply tags: fanfic_tags.py apply Beta\n"
            "7. Run update_links.py\n"
            "8. Run renumber_fanfics.py --dry-run\n"
            "9. Run renumber_fanfics.py (write)\n"
            "10. Move Beta -> Fanfics (номера: 1, 5-10, 15)\n"
            "11. Удалить из Beta полные дубликаты (как в Fanfics + лишние копии в Beta)\n"
            "12. Отчёт: частичные совпадения (абзац >= 250 симв.) Beta vs Fanfics\n"
            "13. Beta: перенумерация «N. …» без пропусков (после удалений)\n"
            "14. Отчёт: частичные совпадения только внутри Fanfics (без связок N / N.k / N.m)\n"
            "15. Beta: пакетно шапка + описание + имена (prepare_beta_batch.py)\n"
            "0. Выход\n"
        )
        choice = prompt_line("Выбор", "0")
        if choice == "1":
            run_export_json()
        elif choice == "2":
            manual_beta_help()
        elif choice == "3":
            add_header_to_beta_file()
        elif choice == "4":
            print_paths()
            try:
                n = next_free_parent_number()
                print(f"Следующий рекомендуемый родительский номер (max+1): {n}")
            except Exception as e:
                print(f"Не удалось вычислить номер: {e}")
        elif choice == "5":
            run_dedup_report()
        elif choice == "6":
            run_apply_tags_beta()
        elif choice == "7":
            run_subprocess_script(UPDATE_LINKS_SCRIPT)
        elif choice == "8":
            run_subprocess_script(RENUMBER_SCRIPT, ["--dry-run"])
        elif choice == "9":
            if prompt_line("Точно применить renumber без dry-run? (y/n)", "n").lower() == "y":
                run_subprocess_script(RENUMBER_SCRIPT)
        elif choice == "10":
            move_beta_to_fanfics()
        elif choice == "11":
            delete_identical_beta_files()
        elif choice == "12":
            run_partial_match_report()
        elif choice == "13":
            renumber_beta_fill_gaps()
        elif choice == "14":
            run_fanfics_internal_partial_report()
        elif choice == "15":
            dry = prompt_line("Сначала dry-run? (y/n)", "y").lower() == "y"
            extra = ["--dry-run"] if dry else ["--apply"]
            run_subprocess_script(PREPARE_BETA_SCRIPT, extra)
        elif choice == "0":
            print("Выход.")
            break
        else:
            print("Неизвестный пункт.")


if __name__ == "__main__":
    main_menu()
