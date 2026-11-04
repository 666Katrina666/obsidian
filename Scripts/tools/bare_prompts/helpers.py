# -*- coding: utf-8 -*-
"""Помощники кампании «голые запросы» для работы в облаке.

Запускать из корня хранилища:

    python Scripts/tools/bare_prompts/helpers.py todo [N]        # оставшиеся заметки по номерам
    python Scripts/tools/bare_prompts/helpers.py propose 80 262 263   # кандидаты границ
    python Scripts/tools/bare_prompts/helpers.py show 262 6-20 400-420  # строки файла
    python Scripts/tools/bare_prompts/helpers.py add batch.json   # дописать партию в карту
    python Scripts/tools/bare_prompts/helpers.py verify [REF]     # сверка карты против REF (HEAD)

Формат партии для `add` — номера заметок и строки ФАЙЛА (с единицы):

    {"262": {"prompts": [[601, 601]], "lost": [6, 416, 791]},
     "265": {"lost": [6], "review": "почему вернуться"}}

Якоря (начало строки) `add` берёт из файла сам. Одиночная заглушка на всю
заметку получает `review` автоматически.
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Scripts" / "lib"))
sys.path.insert(0, str(ROOT / "Scripts" / "tools"))
import notes  # noqa: E402
import runs  # noqa: E402

MAP = ROOT / "Notes" / "prompt_map.json"
FANFICS = ROOT / "Fanfics"

CMD = re.compile(r"^\s*(отлично,? давай|хорошо,? давай|напиши|распиши|продолжи|помоги|давай|сделай|добавь|"
                 r"перепиши|следующ|ещё|еще|теперь|длинн|альтернатив|хочу|можешь|у меня|оцени|предложи|"
                 r"придумай|опиши|расскажи|ок\b|окей|спасибо|в общем|прекрасно|отлично|супер|круто|класс|"
                 r"напишу|а что|а теперь|а если|как насч|глава\s*\d*\s*:?\s*$)", re.I)
CLOSER = re.compile(r"^\s*(Если (вы |ты )?(хочешь|хотите|нужно|тебе|нужны|интересно|нужна|потребуется)|"
                    r"Хочешь|Хотите|Могу (также|ещё|продолжить)|Дай знать|Надеюсь,? (это|тебе)|"
                    r"Что скажешь|Как тебе)", re.I)
TOP = re.compile(r"^(#\s|#{1,4}\s*(\*\*)?Глава\b|\*\*Глава\b|Глава\s*\d*\s*[:.]|ГЛАВА)")


def note_path(pre: str) -> Path:
    hits = glob.glob(str(FANFICS / f"{pre}. *.md"))
    if len(hits) != 1:
        sys.exit(f"{pre}: найдено {len(hits)} файлов")
    return Path(hits[0])


def key(p: Path):
    m = re.match(r"(\d+)(?:\.(\d+))?\.", p.name)
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (10 ** 6, 0)


def todo(limit: int = 60) -> None:
    out = []
    for p in sorted(FANFICS.glob("*.md"), key=key):
        if p.name == "1. Content.md":
            continue
        b = notes.body_after_separator(p.read_text(encoding="utf-8")).split("\n")
        if runs.uses_new_format(b):
            continue
        if len(b) < 60 and any("[[" in l for l in b):
            continue  # хаб
        out.append((len(b), p.name))
    print(f"осталось: {len(out)}")
    for n, f in out[:limit]:
        print(n, f)


def propose(width: int, pres: list[str]) -> None:
    for pre in pres:
        p = note_path(pre)
        t = p.read_text(encoding="utf-8")
        L = t.split("\n")
        off = len(t[:len(t) - len(notes.body_after_separator(t))].split("\n")) - 1
        nb = [i for i in range(off, len(L)) if L[i].strip() and L[i].strip() != "---"]
        marks = {nb[0]: "НАЧАЛО"} if nb else {}
        for k, i in enumerate(nb):
            s = L[i].strip()
            if CLOSER.match(s) and k + 1 < len(nb):
                marks.setdefault(nb[k + 1], "после концовки")
            if TOP.match(s):
                marks.setdefault(i, "заголовок")
            if (not s.startswith(("-", "*", "|", "—", "«", '"', ">", "–", "„", "“", "#"))
                    and len(s) < 2500 and (s[0].islower() or CMD.match(s))):
                marks[i] = marks.get(i, "") + " ?ЗАПРОС"
        print(f"##### {p.name} ({len(L)} строк)")
        for i in sorted(marks):
            prev = [L[j].strip() for j in range(max(off, i - 3), i) if L[j].strip()][-1:]
            print(f"{i + 1:5} [{marks[i].strip()}] {L[i].strip()[:width]}")
            if prev and marks[i] != "НАЧАЛО":
                print(f"        ↑ {prev[0][:width - 20]}")


def show(pre: str, ranges: list[str]) -> None:
    L = note_path(pre).read_text(encoding="utf-8").split("\n")
    for r in ranges:
        a, b = (int(x) for x in r.split("-"))
        for n in range(a, min(b, len(L)) + 1):
            if L[n - 1].strip():
                print(f"{n}: {L[n - 1][:160]}")
        print("  --")


def add(batch_file: str) -> None:
    batch = json.loads(Path(batch_file).read_text(encoding="utf-8"))
    m = json.loads(MAP.read_text(encoding="utf-8"))
    for pre, e in batch.items():
        p = note_path(pre)
        L = p.read_text(encoding="utf-8").split("\n")
        anc = lambda n: L[n - 1].strip()[:25]  # noqa: E731
        entry = {}
        if e.get("prompts"):
            entry["prompts"] = [[a, b, anc(a)] for a, b in e["prompts"]]
        if e.get("lost"):
            entry["lost"] = [[n, anc(n)] for n in e["lost"]]
        for n in list(e.get("lost", [])) + [a for a, _ in e.get("prompts", [])]:
            assert L[n - 1].strip(), (pre, n, "пустая строка")
        if not entry.get("prompts") and len(entry.get("lost", [])) == 1:
            entry["review"] = "одна заглушка на всю заметку — границы ответов не видны"
        if e.get("review"):
            entry["review"] = e["review"]
        assert p.name not in m, f"{p.name} уже в карте"
        m[p.name] = entry
    MAP.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("в карте:", len(m))


def verify(ref: str = "HEAD") -> None:
    """Каждая заметка карты, изменённая относительно REF, сверяется с ним.

    Разрез склейки (`splits` в карте) принимается: прежде чем сравнивать,
    в старый текст вставляются те же переводы строки, а `apply_splits`
    сама проверяет, что куски вместе дают исходную строку побайтно. Любая
    другая разница в тексте — расхождение. Размышления (`think`) сверяются
    как текст ответа: снимается только кавычка callout.
    """
    from convert_prompt_markup import content_seq
    from wrap_bare_prompts import LOST_PROMPT, MapError, apply_splits
    m = json.loads(MAP.read_text(encoding="utf-8"))
    bad = n = tot = 0
    for name, e in m.items():
        f = f"Fanfics/{name}"
        r = subprocess.run(["git", "show", f"{ref}:{f}"], capture_output=True, cwd=ROOT)
        if r.returncode:
            print("нет в", ref, name); bad += 1; continue
        old = r.stdout.decode("utf-8")
        new = (ROOT / f).read_text(encoding="utf-8")
        if old == new:
            continue
        try:
            old = apply_splits(old, e.get("splits", []))
        except MapError as err:
            print("РАЗРЕЗ НЕ ПРИНЯТ:", name, err); bad += 1; continue
        bo, bn = notes.body_after_separator(old), notes.body_after_separator(new)
        want = len(e.get("prompts", [])) + len(e.get("lost", []))
        got = len(runs.parse_runs(bn.split("\n")))
        ok = (old[:len(old) - len(bo)] == new[:len(new) - len(bn)]
              and content_seq(bo.split("\n"), False)
              == [s for s in content_seq(bn.split("\n"), True) if s != LOST_PROMPT]
              and want == got and "\r" not in new)
        n += 1; tot += got
        if not ok:
            bad += 1; print("РАСХОЖДЕНИЕ:", name, want, got)
    print(f"сверка с {ref}: изменённых заметок {n}, прогонов {tot}, расхождений {bad}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    cmd, *args = sys.argv[1:] or ["todo"]
    if cmd == "todo":
        todo(int(args[0]) if args else 60)
    elif cmd == "propose":
        propose(int(args[0]), args[1:])
    elif cmd == "show":
        show(args[0], args[1:])
    elif cmd == "add":
        add(args[0])
    elif cmd == "verify":
        verify(args[0] if args else "HEAD")
    else:
        sys.exit(__doc__)
