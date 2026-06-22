# -*- coding: utf-8 -*-
"""Find similar fanfics (tags + text), write report, then optional post-process.

Post-process: one repeated paragraph per group; add wikilinks for (shingles) groups.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

OBSIDIAN_ROOT = vault_root(__file__)

ENCODING = "utf-8"
DEFAULT_TAG_THRESHOLD = 0.9
DEFAULT_MIN_PARAGRAPH_WORDS = 26
DEFAULT_SHINGLE_SIZE = 5
DEFAULT_SHINGLE_JACCARD = 0.25
REPEATED_PARAGRAPH_TRUNCATE = 200
FANFICS_FOLDER = "Fanfics"


def parse_tags_from_first_line(line: str) -> list[str]:
    if not line or not line.strip():
        return []
    line = line.strip()
    if line.lower().startswith("теги:"):
        line = line[5:].strip()
    tags = re.findall(r"#([^\s#]+)", line)
    return list(dict.fromkeys(tags))


def file_number_from_path(path: str) -> str | None:
    name = os.path.basename(path)
    m = re.match(r"^(\d+)\.", name)
    return m.group(1) if m else None


def get_md_files(folder: str) -> list[str]:
    paths = []
    for name in os.listdir(folder):
        if name.endswith(".md"):
            paths.append(os.path.join(folder, name))
    return sorted(paths)


def normalize_paragraph(s: str) -> str:
    return " ".join(s.split()).strip()


def get_long_paragraphs_with_lines(
    content: str, min_words: int, body_start_line: int = 2
) -> tuple[set[str], dict[str, int]]:
    if not content:
        return set(), {}
    lines = content.split("\n")
    out_set: set[str] = set()
    out_line: dict[str, int] = {}
    current: list[str] = []
    current_start = body_start_line
    for idx, line in enumerate(lines):
        line_num = body_start_line + idx
        if line.strip():
            if not current:
                current_start = line_num
            current.append(line.strip())
        else:
            if current:
                n = normalize_paragraph(" ".join(current))
                if len(n.split()) >= min_words:
                    out_set.add(n)
                    out_line[n] = current_start
            current = []
    if current:
        n = normalize_paragraph(" ".join(current))
        if len(n.split()) >= min_words:
            out_set.add(n)
            out_line[n] = current_start
    return out_set, out_line


def word_shingles(text: str, size: int) -> set[tuple[str, ...]]:
    words = text.lower().split()
    if len(words) < size:
        return set()
    return set(tuple(words[i : i + size]) for i in range(len(words) - size + 1))


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def read_first_line_and_body(path: str) -> tuple[str, str]:
    with open(path, "r", encoding=ENCODING) as f:
        content = f.read()
    if "\n" in content:
        first, _, body = content.partition("\n")
        return first, body
    return content, ""


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def _ensure(self, x: str) -> None:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x: str) -> str:
        self._ensure(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1

    def components(self) -> dict[str, set[str]]:
        from collections import defaultdict

        comp: dict[str, set[str]] = defaultdict(set)
        for x in self.parent:
            comp[self.find(x)].add(x)
        return comp


def build_number_to_link(repo_root: Path) -> dict[str, str]:
    fanfics_dir = repo_root / FANFICS_FOLDER
    out: dict[str, str] = {}
    for root, _dirs, files in os.walk(fanfics_dir):
        for name in files:
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            num = file_number_from_path(path)
            if num is None:
                continue
            rel = os.path.relpath(path, str(repo_root))
            link = rel.replace("\\", "/").replace(".md", "")
            out[num] = "[[" + link + "]]"
    return out


def postprocess_report(repo_root: Path, report_path: str) -> None:
    """One paragraph per group; wikilinks for shingles-only groups."""
    num_to_link = build_number_to_link(repo_root)
    with open(report_path, "r", encoding=ENCODING) as f:
        lines = f.readlines()

    header_re = re.compile(r"^\*\*([0-9, ]+)\*\*\s*\((.*)\)\s*$")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = header_re.match(line.strip())
        if m:
            nums_str, reason = m.group(1), m.group(2)
            nums = [x.strip() for x in nums_str.split(",") if x.strip()]
            is_shingles = "shingles" in reason
            has_exact = "exact paragraph" in reason
            out.append(line)
            i += 1
            if i < len(lines) and lines[i].strip() == "":
                out.append(lines[i])
                i += 1
            if is_shingles and not has_exact:
                links = [
                    num_to_link.get(n, "[[" + FANFICS_FOLDER + "/" + n + ".]]")
                    for n in nums
                ]
                out.append("In: " + ", ".join(links) + "\n")
                out.append("\n")
                while i < len(lines) and not header_re.match(lines[i].strip()):
                    i += 1
            else:
                first_para_done = False
                while i < len(lines):
                    cur = lines[i]
                    if header_re.match(cur.strip()):
                        break
                    if cur.strip().startswith("Repeated paragraph:"):
                        if not first_para_done:
                            first_para_done = True
                            out.append(cur)
                            i += 1
                            while i < len(lines):
                                next_line = lines[i]
                                if next_line.strip().startswith(
                                    "Repeated paragraph:"
                                ) or header_re.match(next_line.strip()):
                                    break
                                out.append(next_line)
                                i += 1
                        else:
                            i += 1
                            while i < len(lines):
                                next_line = lines[i]
                                if next_line.strip().startswith(
                                    "Repeated paragraph:"
                                ) or header_re.match(next_line.strip()):
                                    break
                                i += 1
                    else:
                        out.append(cur)
                        i += 1
            continue
        out.append(line)
        i += 1

    with open(report_path, "w", encoding=ENCODING) as f:
        f.writelines(out)


def run_find(
    folder: str,
    out_path: str,
    tag_threshold: float,
    min_paragraph_words: int,
    shingle_size: int,
    shingle_jaccard: float,
    limit: int,
    skip_postprocess: bool,
) -> None:
    print("similar_fanfics: starting", file=sys.stderr, flush=True)

    folder_abs = os.path.abspath(folder)
    if not os.path.isdir(folder_abs):
        print("Error: folder not found:", folder_abs, file=sys.stderr)
        sys.exit(1)

    def write_progress(line: str) -> None:
        with open(out_path, "a", encoding=ENCODING) as f:
            f.write(line + "\n")
            f.flush()
        print(line, file=sys.stderr, flush=True)

    vault = str(OBSIDIAN_ROOT)

    with open(out_path, "w", encoding=ENCODING) as f:
        f.write("# Similar fanfics report (tags + text)\n")
        f.write(
            "# Tag overlap > {} | Min paragraph words > {} | Shingle Jaccard: {}\n".format(
                tag_threshold, min_paragraph_words - 1, shingle_jaccard
            )
        )
        f.write("\n## Progress\n")
    write_progress("Step 1: Parsing .md files...")

    paths = get_md_files(folder_abs)
    if limit > 0:
        paths = paths[:limit]
    files = []
    for p in paths:
        num = file_number_from_path(p)
        if num is None:
            continue
        with open(p, "r", encoding=ENCODING) as f:
            first = f.readline()
        tags = set(parse_tags_from_first_line(first))
        files.append((num, p, tags))

    write_progress("  Parsed {} files with numeric prefix.".format(len(files)))

    if len(files) < 2:
        write_progress("  No pairs to compare (need at least 2 files).")
        print("Done. No pairs to compare.", file=sys.stderr)
        return

    write_progress("Step 2: Building tag index and pairs with shared tag...")
    tag_to_indices: dict[str, list[int]] = {}
    for i, (_num, _path, tags) in enumerate(files):
        for tag in tags:
            tag_to_indices.setdefault(tag, []).append(i)

    pairs_with_shared_tag: set[tuple[int, int]] = set()
    for indices in tag_to_indices.values():
        for ii in range(len(indices)):
            for jj in range(ii + 1, len(indices)):
                i, j = indices[ii], indices[jj]
                if i > j:
                    i, j = j, i
                pairs_with_shared_tag.add((i, j))

    write_progress(
        "  {} tags, {} pairs with at least one shared tag.".format(
            len(tag_to_indices), len(pairs_with_shared_tag)
        )
    )

    write_progress("Step 3: Filtering by tag overlap > {}...".format(tag_threshold))
    tag_candidates: set[tuple[int, int]] = set()
    for i, j in pairs_with_shared_tag:
        a, b = files[i][2], files[j][2]
        overlap = len(a & b) / min(len(a), len(b)) if a and b else 0
        if overlap > tag_threshold:
            tag_candidates.add((i, j))

    write_progress("  Tag candidates: {} pairs.".format(len(tag_candidates)))

    file_indices_needed: set[int] = set()
    for i, j in tag_candidates:
        file_indices_needed.add(i)
        file_indices_needed.add(j)

    write_progress(
        "Step 4: Loading bodies and building paragraphs/shingles for {} files...".format(
            len(file_indices_needed)
        )
    )

    paragraphs_by_index: dict[int, set] = {}
    paragraph_to_line_by_index: dict[int, dict] = {}
    body_by_index: dict[int, str] = {}
    shingles_by_index: dict[int, set] = {}
    skipped = []
    for count, idx in enumerate(file_indices_needed):
        if (count + 1) % 100 == 0:
            write_progress("  Loaded {}/{} files...".format(count + 1, len(file_indices_needed)))
        _n, path, _t = files[idx]
        try:
            _first, body = read_first_line_and_body(path)
            body_by_index[idx] = body
            p_set, p_to_line = get_long_paragraphs_with_lines(
                body, min_paragraph_words, body_start_line=2
            )
            paragraphs_by_index[idx] = p_set
            paragraph_to_line_by_index[idx] = p_to_line
            shingles_by_index[idx] = word_shingles(body, shingle_size)
        except Exception as e:
            skipped.append((files[idx][0], path, str(e)))
            body_by_index[idx] = ""
            paragraphs_by_index[idx] = set()
            paragraph_to_line_by_index[idx] = {}
            shingles_by_index[idx] = set()
    if skipped:
        write_progress("  Skipped {} files (errors): {}.".format(len(skipped), skipped[:5]))
    write_progress("  Done.")

    def obsidian_link(path: str) -> str:
        rel = os.path.relpath(path, vault)
        return rel.replace("\\", "/").replace(".md", "")

    write_progress("Step 5: Text confirmation (exact paragraph / shingles)...")
    confirmed: dict = {}
    for i, j in tag_candidates:
        reasons: set[str] = set()
        exact_paragraphs = []
        pa, pb = paragraphs_by_index.get(i, set()), paragraphs_by_index.get(j, set())
        line_i = paragraph_to_line_by_index.get(i, {})
        line_j = paragraph_to_line_by_index.get(j, {})
        common = pa & pb
        if common:
            reasons.add("exact paragraph")
            for p in common:
                locs = []
                if p in line_i:
                    locs.append((files[i][0], files[i][1], line_i[p]))
                if p in line_j:
                    locs.append((files[j][0], files[j][1], line_j[p]))
                if locs:
                    exact_paragraphs.append((p, locs))
        if not reasons:
            sa = shingles_by_index.get(i, set())
            sb = shingles_by_index.get(j, set())
            if jaccard(sa, sb) >= shingle_jaccard:
                reasons.add("shingles")
        if reasons:
            confirmed[(i, j)] = (reasons, exact_paragraphs)

    exact_count = sum(1 for r, _ in confirmed.values() if "exact paragraph" in r)
    shingle_count = sum(1 for r, _ in confirmed.values() if "shingles" in r)
    write_progress(
        "  Confirmed pairs: {} (exact paragraph: {}, shingles: {}).".format(
            len(confirmed), exact_count, shingle_count
        )
    )

    write_progress("Step 6: Grouping (union-find)...")
    uf = UnionFind()
    pair_reasons: dict[tuple[str, str], set] = {}
    pair_paragraphs: dict[tuple[str, str], list] = {}
    for (i, j), (reasons, exact_paragraphs) in confirmed.items():
        num_i, num_j = files[i][0], files[j][0]
        uf.union(num_i, num_j)
        key = tuple(sorted([num_i, num_j], key=int))
        pair_reasons[key] = pair_reasons.get(key, set()) | reasons
        if exact_paragraphs:
            pair_paragraphs[key] = pair_paragraphs.get(key, []) + exact_paragraphs

    components = uf.components()
    groups = []
    for _root, members in components.items():
        if len(members) < 2:
            continue
        sorted_nums = sorted(members, key=int)
        all_reasons: set[str] = set()
        mem_list = list(members)
        for a in range(len(mem_list)):
            for b in range(a + 1, len(mem_list)):
                key = tuple(sorted([mem_list[a], mem_list[b]], key=int))
                all_reasons |= pair_reasons.get(key, set())
        reason_str = ", ".join(sorted(all_reasons))
        paragraph_locs: dict[str, set] = {}
        for a in range(len(mem_list)):
            for b in range(a + 1, len(mem_list)):
                key = tuple(sorted([mem_list[a], mem_list[b]], key=int))
                for para, locs in pair_paragraphs.get(key, []):
                    if para not in paragraph_locs:
                        paragraph_locs[para] = set()
                    for num, path, line in locs:
                        paragraph_locs[para].add((num, path, line))
        groups.append((sorted_nums, reason_str, paragraph_locs))

    groups.sort(key=lambda g: (int(g[0][0]), g[0]))

    write_progress("  {} groups.".format(len(groups)))
    write_progress("")
    write_progress("## Results")
    for nums, reason_str, paragraph_locs in groups:
        write_progress("")
        write_progress("**" + ", ".join(nums) + "** (" + reason_str + ")")
        if paragraph_locs:
            for para, locs in paragraph_locs.items():
                display = (
                    para
                    if len(para) <= REPEATED_PARAGRAPH_TRUNCATE
                    else para[:REPEATED_PARAGRAPH_TRUNCATE] + "..."
                )
                write_progress("")
                write_progress("Repeated paragraph:")
                write_progress("> " + display.replace("\n", " "))
                link_parts = [
                    "[[" + obsidian_link(path) + "]] (line " + str(line) + ")"
                    for _, path, line in sorted(locs, key=lambda x: (int(x[0]), x[2]))
                ]
                write_progress("In: " + ", ".join(link_parts))

    print(
        "Done. {} groups written to {}.".format(len(groups), out_path),
        file=sys.stderr,
    )

    if not skip_postprocess:
        postprocess_report(OBSIDIAN_ROOT, out_path)
        print("Post-processed report.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder",
        nargs="?",
        default=str(OBSIDIAN_ROOT / FANFICS_FOLDER),
        help="Folder with .md files",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=str(OBSIDIAN_ROOT / "similar_fanfics_report.md"),
        help="Output report path",
    )
    parser.add_argument(
        "--tag-threshold",
        "-t",
        type=float,
        default=DEFAULT_TAG_THRESHOLD,
    )
    parser.add_argument(
        "--min-paragraph-words",
        "-p",
        type=int,
        default=DEFAULT_MIN_PARAGRAPH_WORDS,
    )
    parser.add_argument("--shingle-size", type=int, default=DEFAULT_SHINGLE_SIZE)
    parser.add_argument(
        "--shingle-jaccard", type=float, default=DEFAULT_SHINGLE_JACCARD
    )
    parser.add_argument("--limit", type=int, default=0, help="First N files only (0=all)")
    parser.add_argument(
        "--skip-postprocess",
        action="store_true",
        help="Do not run post-process (paragraph dedupe / shingles links)",
    )
    parser.add_argument(
        "--postprocess-only",
        action="store_true",
        help="Only post-process existing report (--output path)",
    )
    args = parser.parse_args()

    out_path = os.path.abspath(args.output)

    if args.postprocess_only:
        postprocess_report(OBSIDIAN_ROOT, out_path)
        print("Done. Wrote", out_path)
        return

    run_find(
        folder=args.folder,
        out_path=out_path,
        tag_threshold=args.tag_threshold,
        min_paragraph_words=args.min_paragraph_words,
        shingle_size=args.shingle_size,
        shingle_jaccard=args.shingle_jaccard,
        limit=args.limit,
        skip_postprocess=args.skip_postprocess,
    )


if __name__ == "__main__":
    main()
