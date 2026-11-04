# -*- coding: utf-8 -*-
"""Вписывает восстановленные запросы на место заглушек `(запрос не сохранился)`.

Решение автора (04.11.2026): восстановленный запрос никак не помечается —
он просто встаёт в тот же callout вместо заглушки, как будто так и было.

Тексты лежат в картах `Notes/restored_prompts/*.json` (по файлу на партию
или на облачную сессию, чтобы параллельные сессии не правили один файл):

    {
      "240. Jason and Steph's Underground Journey.md": {
        "3": "следующая глава. Джейсон и Стеф выходят к Ториэль…",
        "7": "напиши длинную главу: …\\nвторая строка запроса"
      }
    }

Ключ — номер N из заголовка `> [!question]- Запрос N`. Значение — текст
запроса; перевод строки `\\n` разбивает его на строки callout (пустая строка
внутри станет `>`, как в `runs.render_callout`).

Каждая замена проверяется:
- у callout `Запрос N` тело — ровно одна строка с заглушкой (иначе отказ:
  там уже настоящий запрос или заметка сдвинулась);
- обратная замена восстановленных строк на заглушку даёт исходный файл
  байт в байт — значит, кроме этих строк, не изменилось ничего;
- `parse_runs` видит то же число прогонов, у восстановленных запрос равен
  тексту из карты, у остальных не изменился;
- в тексте нет `\\r`, строк вида `> [!…`, и он не пустой.

Повторный прогон безопасен: уже вписанный запрос (тело callout совпадает с
текстом карты) только считается.

По умолчанию ничего не меняет. Запись — с `--apply`. Отчёт с каждым
вписанным запросом и началом ответа под ним —
`Reports/restore_prompts_report.md`; там же счётчик оставшихся заглушек.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
import notes  # noqa: E402
import runs as runs_mod  # noqa: E402
from paths import notes_dir, reports_dir, vault_root  # noqa: E402

VAULT = vault_root(__file__)
MAP_DIR = notes_dir(__file__) / "restored_prompts"
REPORT_FILE = "restore_prompts_report.md"
LOST_PROMPT = "(запрос не сохранился)"
LOST_LINE = f"> {LOST_PROMPT}"
HEAD_RE = re.compile(r"^> \[!question\]- Запрос (\d+)$")


class RestoreError(Exception):
    pass


def load_maps(map_dir: Path) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for p in sorted(map_dir.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for name, entries in data.items():
            slot = merged.setdefault(name, {})
            for n, text in entries.items():
                if n in slot and slot[n] != text:
                    raise SystemExit(f"{p.name}: {name} запрос {n} уже задан в другой карте иначе")
                slot[n] = text
    return merged


def rendered(text: str) -> list[str]:
    """Строки тела callout для текста запроса (без заголовка)."""
    return runs_mod.render_callout(runs_mod.PROMPT_CALLOUT, "x", text.split("\n"))[1:]


def validate(text: str) -> None:
    if not text.strip():
        raise RestoreError("пустой текст")
    if "\r" in text:
        raise RestoreError("в тексте \\r")
    if text.strip() == LOST_PROMPT:
        raise RestoreError("текст равен заглушке")
    for line in text.split("\n"):
        if re.match(r"^\s*>?\s*\[!", line):
            raise RestoreError(f"строка похожа на callout: {line[:40]!r}")


def restore(lines: list[str], entries: dict[str, str]):
    """Новые строки файла, список (N, позиция, число строк) и число уже вписанных."""
    heads = {}
    for i, l in enumerate(lines):
        m = HEAD_RE.match(l)
        if m:
            if m.group(1) in heads:
                raise RestoreError(f"заголовок «Запрос {m.group(1)}» встречается дважды")
            heads[m.group(1)] = i
    out = list(lines)
    plan = []
    already = 0
    for n, text in entries.items():
        validate(text)
        if n not in heads:
            raise RestoreError(f"нет callout «Запрос {n}»")
        i = heads[n]
        body = rendered(text)
        if out[i + 1:i + 1 + len(body)] == body and (
                i + 1 + len(body) >= len(out) or not out[i + 1 + len(body)].startswith(">")):
            already += 1
            continue
        if out[i + 1] != LOST_LINE or (i + 2 < len(out) and out[i + 2].startswith(">")):
            raise RestoreError(f"у «Запрос {n}» тело не заглушка: {out[i + 1][:50]!r}")
        plan.append((i + 1, body, n))
    shift = 0
    spans = []
    for pos, body, n in sorted(plan):
        p = pos + shift
        out[p:p + 1] = body
        spans.append((n, p, len(body)))
        shift += len(body) - 1
    return out, spans, already


def check(old_text: str, new_lines: list[str], spans, entries) -> None:
    back = list(new_lines)
    for n, p, k in sorted(spans, key=lambda s: -s[1]):
        back[p:p + k] = [LOST_LINE]
    if "\n".join(back) != old_text:
        raise RestoreError("обратная замена не дала исходный файл")
    new_text = "\n".join(new_lines)
    if notes.has_tag_header(new_text) != notes.has_tag_header(old_text):
        raise RestoreError("изменилось, считается ли начало файла шапкой")
    ob = notes.body_after_separator(old_text).split("\n")
    nb = notes.body_after_separator(new_text).split("\n")
    ro, rn = runs_mod.parse_runs(ob), runs_mod.parse_runs(nb)
    if len(ro) != len(rn):
        raise RestoreError(f"прогонов было {len(ro)}, стало {len(rn)}")
    restored_prompts = {" ".join(l.strip() for l in entries[n].split("\n") if l.strip())
                        for n, _, _ in spans}
    for a, b in zip(ro, rn):
        if a.prompt == b.prompt:
            continue
        if a.prompt != LOST_PROMPT or b.prompt not in restored_prompts:
            raise RestoreError(f"запрос прочитан иначе: {b.prompt[:50]!r}")
        if a.think != b.think or a.size != b.size:
            raise RestoreError("изменился ответ или размышления прогона")


def answer_head(lines: list[str], pos: int) -> str:
    j = pos
    while j < len(lines) and lines[j].startswith(">"):
        j += 1
    heads = [l.strip() for l in lines[j:j + 40] if l.strip()][:2]
    return " / ".join(h[:110] for h in heads)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", default="Fanfics")
    ap.add_argument("--maps", default=str(MAP_DIR), help="Папка с картами *.json")
    ap.add_argument("--apply", action="store_true", help="Записать изменения")
    args = ap.parse_args()

    directory = VAULT / args.folder
    mapping = load_maps(Path(args.maps))
    report = [f"# Восстановление запросов: {args.folder}", "",
              f"Режим: {'запись' if args.apply else 'dry-run, ничего не меняется'}.", ""]
    done = restored = already = 0
    failures: list[tuple[str, str]] = []
    for name in sorted(mapping):
        path = directory / name
        if not path.is_file():
            failures.append((name, "нет такого файла"))
            continue
        old = path.read_text(encoding="utf-8")
        if "\r" in old:
            failures.append((name, "в файле \\r"))
            continue
        try:
            new_lines, spans, already_here = restore(old.split("\n"), mapping[name])
            already += already_here
            if not spans:
                continue
            check(old, new_lines, spans, mapping[name])
        except RestoreError as e:
            failures.append((name, str(e)))
            continue
        done += 1
        restored += len(spans)
        report += [f"## {name}", ""]
        for n, p, k in spans:
            short = " ".join(mapping[name][n].split())
            report.append(f"- **Запрос {n}**: {short[:300]}")
            report.append(f"  - ответ: {answer_head(new_lines, p + k)}")
        report.append("")
        if args.apply:
            path.write_text("\n".join(new_lines), encoding="utf-8", newline="\n")

    left = 0
    for p in directory.glob("*.md"):
        left += p.read_text(encoding="utf-8").count("\n" + LOST_LINE + "\n")
    if not args.apply:
        left -= restored
    summary = [f"заметок к записи: {done}", f"  запросов вписано: {restored}",
               f"уже вписаны раньше: {already}", f"отказов: {len(failures)}",
               f"заглушек остаётся в {args.folder}: {left}"]
    report[4:4] = [*summary, ""]
    if failures:
        report += ["## Отказы", ""] + [f"- {n}: {why}" for n, why in failures]
    out = reports_dir(__file__) / REPORT_FILE
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(summary))
    for n, why in failures:
        print(f"  ! {n}: {why}")
    print(f"отчёт: {out}")


if __name__ == "__main__":
    main()
