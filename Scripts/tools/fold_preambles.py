# -*- coding: utf-8 -*-
"""Сворачивает вводные абзацы-преамбулы под запросом в callout размышлений.

В выгрузках ChatGPT над ответом часто стоит короткий служебный абзац, который
интерфейс выводил, пока модель думала: «Похоже на уже существующие ветки…»,
«Сделаю главу с тремя слоями: …», «Сначала сверю канон…». Это не ответ, а
его анонс; сам ответ идёт следом и нередко повторяет тот же абзац почти
дословно. В формате хранилища такой абзац лежит в свёрнутом
`> [!abstract]- Размышления` сразу под callout запроса — так его читает
`runs.parse_runs` (поле `think`).

Где преамбула, а где начало ответа, видно только по смыслу, поэтому места
не ищутся регекспом, а записываются вручную в карту `Notes/preamble_map.json`:

    {"203.2. Jason as a Mew Mew - ….md": [[9, 9, "Похоже на уже существ"]]}

- Диапазон — строки **текущего** файла, с единицы, конец включительно.
  Третье поле — начало первой строки: если файл сдвинулся, заметка не
  трогается.
- Диапазон начинается с первой непустой строки сразу под callout запроса
  (между ними только пустые строки) и не доходит до конца прогона: под ним
  обязан остаться ответ.
- Текст не меняется ни на символ: строкам диапазона приписывается `> `
  (пустой строке — `>`, как в `runs.render_callout`), сверху встаёт
  заголовок callout, до и после — по пустой строке.

Самопроверка каждой заметки:

- `content_seq` (из `convert_prompt_markup.py`) старого и нового тела совпадает;
- `parse_runs` даёт столько же прогонов с теми же запросами, у свёрнутых
  прогонов `think` равен тексту диапазона, у остальных не изменился;
- шапка не тронута, в файле нет `\\r`.

Заметки из `Notes/prompt_map.json` дополнительно получают там поле `think`
(номера строк исходника `--source-ref` с разрезами `splits`, как его читает
`wrap_bare_prompts.py`). Перед записью карта проверяется: обёртка исходника
по обновлённой записи обязана дать ровно тот же файл, что получился здесь,
байт в байт. Так повторная переразметка по `REVIEW_TASK.md` преамбулы не
потеряет. Без `--no-sync` расхождение — отказ.

Повторный прогон безопасен: заметка, где все диапазоны уже свёрнуты, только
отмечается в отчёте.

По умолчанию ничего не меняет. Запись — с `--apply`. Отчёт —
`Reports/fold_preambles_report.md`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
import notes
import runs as runs_mod
from paths import notes_dir, reports_dir, vault_root
from convert_prompt_markup import content_seq
import wrap_bare_prompts as wrapper

VAULT = vault_root(__file__)
MAP_FILE = notes_dir(__file__) / "preamble_map.json"
PROMPT_MAP_FILE = notes_dir(__file__) / "prompt_map.json"
REPORT_FILE = "fold_preambles_report.md"
SOURCE_REF = "ff02e1c~1"


class FoldError(Exception):
    pass


def body_offset(text: str) -> tuple[int, list[str]]:
    return wrapper.body_offset(text)


def think_text(lines: list[str]) -> str:
    """Текст размышлений так, как его соберёт `parse_runs`: строки через пробел."""
    return " ".join(l.strip() for l in lines if l.strip())


def _norm(s: str) -> str:
    # parse_runs снимает ровно один уровень цитаты — сравниваем так же,
    # как wrap_bare_prompts.check.
    return s.replace("> ", "").replace(">", "")


def already_folded(body: list[str], anchor: str) -> bool:
    """Диапазон с этим якорем уже лежит первой строкой callout размышлений."""
    for i, l in enumerate(body[:-1]):
        if runs_mod._is_callout(l, runs_mod.THINK_CALLOUT):
            m = runs_mod._QUOTE_RE.match(body[i + 1])
            if m and m.group(1).strip().startswith(anchor):
                return True
    return False


def resolve(ranges: list, text: str) -> list[tuple[int, int, int]]:
    """Диапазоны карты → (номер прогона, начало, конец) в индексах тела.

    Конец не включён. Прогоны — в порядке `parse_runs`.
    """
    offset, body = body_offset(text)
    file_lines = text.split("\n")
    parsed = runs_mod.parse_runs(body)
    out: list[tuple[int, int, int]] = []
    for item in ranges:
        if len(item) != 3:
            raise FoldError(f"диапазон {item}: нужно [начало, конец, якорь]")
        a, b, anchor = item
        if b < a:
            raise FoldError(f"диапазон {a}-{b} перевёрнут")
        if not (1 <= a and b <= len(file_lines)):
            raise FoldError(f"диапазон {a}-{b} вне файла")
        if a - 1 < offset:
            raise FoldError(f"строка {a} лежит в шапке")
        if not file_lines[a - 1].strip().startswith(anchor):
            raise FoldError(f"строка {a} не начинается с {anchor!r}: "
                            f"{file_lines[a - 1].strip()[:50]!r}")
        t0, t1 = a - 1 - offset, b - offset
        k = next((n for n, r in enumerate(parsed) if r.start < t0 < r.end), None)
        if k is None:
            raise FoldError(f"строка {a} не лежит под запросом")
        run = parsed[k]
        if run.think:
            raise FoldError(f"у прогона со строки {run.start + offset + 1} "
                            f"размышления уже есть")
        _, q_end = runs_mod._quote_body(body, run.start + 1, run.end)
        if q_end > t0 or any(l.strip() for l in body[q_end:t0]):
            raise FoldError(f"строка {a} не идёт сразу под callout запроса")
        if t1 > run.end:
            raise FoldError(f"диапазон {a}-{b} заходит на следующий запрос")
        if not body[t1 - 1].strip():
            raise FoldError(f"диапазон {a}-{b} кончается пустой строкой")
        if not any(l.strip() for l in body[t1:run.end]):
            raise FoldError(f"после диапазона {a}-{b} нет ответа")
        for l in body[t0:t1]:
            if runs_mod.is_prompt_start(l) or runs_mod._CALLOUT_RE.match(l):
                raise FoldError(f"внутри диапазона {a}-{b} есть callout")
        if any(k == o[0] for o in out):
            raise FoldError(f"у прогона со строки {run.start + offset + 1} два диапазона")
        out.append((k, t0, t1))
    return sorted(out)


def fold(body: list[str], folds: list[tuple[int, int, int]]) -> list[str]:
    """Новое тело: каждый диапазон — в callout размышлений под своим запросом."""
    parsed = runs_mod.parse_runs(body)
    new = list(body)
    for k, t0, t1 in sorted(folds, key=lambda f: -f[1]):
        _, q_end = runs_mod._quote_body(body, parsed[k].start + 1, parsed[k].end)
        after = t1
        while after < len(body) and not body[after].strip():
            after += 1
        block = runs_mod.render_callout(runs_mod.THINK_CALLOUT, runs_mod.THINK_LABEL,
                                        body[t0:t1])
        new[q_end:after] = ["", *block, ""]
    return new


def check(body: list[str], new_body: list[str],
          folds: list[tuple[int, int, int]]) -> str:
    """Пустая строка — всё сошлось, иначе причина отказа."""
    old = content_seq(body, new_format=True)
    new = content_seq(new_body, new_format=True)
    if old != new:
        if len(old) != len(new):
            return f"строк текста было {len(old)}, стало {len(new)}"
        for k, (a, b) in enumerate(zip(old, new), start=1):
            if a != b:
                return f"строка {k} разошлась: {a[:40]!r} против {b[:40]!r}"
        return "неизвестное расхождение"
    before = runs_mod.parse_runs(body)
    after = runs_mod.parse_runs(new_body)
    if len(before) != len(after):
        return f"parse_runs: прогонов было {len(before)}, стало {len(after)}"
    want = {k: think_text(body[t0:t1]) for k, t0, t1 in folds}
    for k, (r0, r1) in enumerate(zip(before, after)):
        if r0.prompt != r1.prompt:
            return f"запрос {k + 1} прочитан иначе: {r1.prompt[:50]!r}"
        if k in want:
            if _norm(want[k]) != _norm(r1.think):
                return f"размышления в прогоне {k + 1} прочитаны иначе: {r1.think[:50]!r}"
        elif r0.think != r1.think:
            return f"размышления в прогоне {k + 1} изменились, хотя их нет в карте"
    return ""


def git_show(ref: str, rel: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], capture_output=True, cwd=VAULT)
    return None if r.returncode else r.stdout.decode("utf-8")


def rewrap(entry: dict, source: str) -> str:
    """Файл, который `wrap_bare_prompts.py` соберёт из исходника по записи карты."""
    text = wrapper.apply_splits(source, entry.get("splits", []))
    offset, body = body_offset(text)
    spans = wrapper.resolve(entry, text)
    thinks = wrapper.resolve_think(entry, text, spans)
    new_body = wrapper.wrap(body, spans, thinks)
    problem = wrapper.check(body, new_body, spans, thinks)
    if problem:
        raise FoldError(f"обёртка исходника не сошлась: {problem}")
    prefix = "\n".join(text.split("\n")[:offset])
    return prefix + "\n" + "\n".join(new_body) + "\n"


def sync_entry(entry: dict, source: str, folds: list[tuple[int, int, int]],
               new_text: str) -> list[list[int]]:
    """Поле `think` записи `prompt_map.json`, которое даёт ровно `new_text`.

    Прогон k текущего файла — это k-й отрезок карты (`resolve` сортирует их
    так же, как стоят callout). Ответ под ним в исходнике начинается с первой
    непустой строки после отрезка; число строк диапазона не меняется, потому
    что обёртка срезает пустые строки только по краям ответа.
    """
    text = wrapper.apply_splits(source, entry.get("splits", []))
    offset, body = body_offset(text)
    spans = wrapper.resolve(entry, text)
    think = [list(t) for t in entry.get("think", [])]
    for k, t0, t1 in folds:
        if k >= len(spans):
            raise FoldError(f"в prompt_map нет отрезка для прогона {k + 1}")
        s = spans[k][1]
        while s < len(body) and not body[s].strip():
            s += 1
        think.append([s + offset + 1, s + (t1 - t0) + offset])
    think.sort()
    trial = dict(entry, think=think)
    if rewrap(trial, source) != new_text:
        raise FoldError("обёртка исходника с новым think не совпала с файлом побайтно")
    return think


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", default="Fanfics", help="Папка (по умолчанию Fanfics)")
    ap.add_argument("--map", default=str(MAP_FILE), help="Карта преамбул")
    ap.add_argument("--prompt-map", default=str(PROMPT_MAP_FILE),
                    help="Карта голых запросов, куда дописывается think")
    ap.add_argument("--source-ref", default=SOURCE_REF,
                    help=f"Коммит с исходниками для prompt_map (по умолчанию {SOURCE_REF})")
    ap.add_argument("--no-sync", action="store_true",
                    help="Не трогать prompt_map.json")
    ap.add_argument("--apply", action="store_true", help="Записать изменения")
    args = ap.parse_args()

    directory = VAULT / args.folder
    mapping = json.loads(Path(args.map).read_text(encoding="utf-8"))
    pmap_path = Path(args.prompt_map)
    pmap = json.loads(pmap_path.read_text(encoding="utf-8")) if pmap_path.is_file() else {}
    pmap_changed = False

    report = [f"# Преамбулы в callout размышлений: {args.folder}", "",
              f"Режим: {'запись' if args.apply else 'dry-run, ничего не меняется'}.", ""]
    done = folded = synced = already = 0
    failures: list[tuple[str, str]] = []
    pending: list[tuple[Path, str]] = []

    for name, ranges in mapping.items():
        path = directory / name
        if not path.is_file():
            failures.append((name, "нет такого файла"))
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            text = fh.read()
        if "\r" in text:
            failures.append((name, "в файле есть \\r"))
            continue
        if not notes.has_tag_header(text):
            failures.append((name, "нет шапки — не понять, где начинается тело"))
            continue
        offset, body = body_offset(text)
        if not runs_mod.uses_new_format(body):
            failures.append((name, "нет callout запроса"))
            continue
        anchors = [r[2] for r in ranges if len(r) == 3]
        file_lines = text.split("\n")
        moved = [r for r in ranges if len(r) == 3 and not (
            1 <= r[0] <= len(file_lines) and file_lines[r[0] - 1].strip().startswith(r[2]))]
        if moved and len(moved) == len(ranges) and all(already_folded(body, a) for a in anchors):
            already += 1
            continue
        try:
            folds = resolve(ranges, text)
        except FoldError as e:
            failures.append((name, str(e)))
            continue
        new_body = fold(body, folds)
        problem = check(body, new_body, folds)
        if problem:
            failures.append((name, problem))
            continue
        # Тело уже несёт хвост файла: его последняя «строка» — пустая после
        # финального перевода строки, добавлять свой не нужно.
        prefix = "\n".join(file_lines[:offset])
        new_text = prefix + "\n" + "\n".join(new_body)
        if "\r" in new_text or new_text[:len(prefix) + 1] != text[:len(prefix) + 1]:
            failures.append((name, "шапка изменилась или появился \\r"))
            continue

        sync_note = ""
        if name in pmap and not args.no_sync:
            source = git_show(args.source_ref, f"{args.folder}/{name}")
            if source is None:
                failures.append((name, f"нет в {args.source_ref} — prompt_map не сверить"))
                continue
            try:
                think = sync_entry(pmap[name], source, folds, new_text)
            except (FoldError, wrapper.MapError) as e:
                failures.append((name, f"prompt_map: {e}"))
                continue
            pmap[name] = dict(pmap[name], think=think)
            pmap_changed = True
            synced += 1
            sync_note = f" — в prompt_map: think {think}"

        done += 1
        folded += len(folds)
        report.append(f"## {name}{sync_note}")
        report.append("")
        for k, t0, t1 in folds:
            first = next(l.strip() for l in body[t0:t1] if l.strip())
            after = next((l.strip() for l in body[t1:] if l.strip()), "")
            report.append(f"- **Запрос {k + 1}**, строки {t0 + offset + 1}–{t1 + offset}: "
                          f"{first[:160]}")
            report.append(f"  - ответ: {after[:110]}")
        report.append("")
        pending.append((path, new_text))

    if args.apply and not failures:
        for path, new_text in pending:
            # newline="\n": заметки хранятся в LF (.gitattributes), а write_text
            # на Windows иначе молча пишет CRLF.
            path.write_text(new_text, encoding="utf-8", newline="\n")
        if pmap_changed:
            pmap_path.write_text(json.dumps(pmap, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8", newline="\n")
    elif args.apply:
        report[2] = "Режим: запись отменена — есть отказы, ничего не записано."

    summary = [f"заметок к записи: {done}", f"  преамбул: {folded}",
               f"  записей prompt_map с think: {synced}",
               f"уже свёрнуты раньше: {already}", f"отказов: {len(failures)}"]
    report[4:4] = [*summary, ""]
    if failures:
        report.append("## Отказы")
        report.append("")
        report.extend(f"- {n}: {why}" for n, why in failures)
    out = reports_dir(__file__) / REPORT_FILE
    out.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")

    print("\n".join(summary))
    for n, why in failures:
        print(f"  ! {n}: {why}")
    if args.apply and failures:
        print("запись отменена: сначала исправить отказы")
    print(f"отчёт: {out}")


if __name__ == "__main__":
    main()
