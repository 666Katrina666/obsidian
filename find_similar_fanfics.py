# -*- coding: utf-8 -*-
"""Find similar fanfic .md files by tag overlap and text (exact paragraph or shingles).
Only pairs that pass BOTH tag threshold and text confirmation are reported.
Output: .md report with groups, reason suffix, and for exact paragraph matches the repeated text and Obsidian links to file and line.
"""
import argparse
import os
import re
import sys

ENCODING = "utf-8"
DEFAULT_TAG_THRESHOLD = 0.9   # tag overlap must be strictly > this
DEFAULT_MIN_PARAGRAPH_WORDS = 26   # paragraph must have more than 25 words
DEFAULT_SHINGLE_SIZE = 5
DEFAULT_SHINGLE_JACCARD = 0.25
REPEATED_PARAGRAPH_TRUNCATE = 200


def parse_tags_from_first_line(line):
    """Parse tags from first line. Same logic as apply_tags.py."""
    if not line or not line.strip():
        return []
    line = line.strip()
    if line.lower().startswith("теги:"):
        line = line[5:].strip()
    tags = re.findall(r"#([^\s#]+)", line)
    return list(dict.fromkeys(tags))


def file_number_from_path(path):
    """Extract leading number from filename, e.g. '351. Dark Mirror...' -> '351'. Returns None if no match."""
    name = os.path.basename(path)
    m = re.match(r"^(\d+)\.", name)
    return m.group(1) if m else None


def get_md_files(folder):
    """Return list of .md file paths in folder, sorted."""
    paths = []
    for name in os.listdir(folder):
        if name.endswith(".md"):
            paths.append(os.path.join(folder, name))
    return sorted(paths)


def normalize_paragraph(s):
    """Collapse whitespace to single space and strip."""
    return " ".join(s.split()).strip()


def get_long_paragraphs_with_lines(content, min_words, body_start_line=2):
    """Return (set of normalized paragraphs, dict normalized -> start_line).
    Paragraph must have at least min_words words. start_line is 1-based (body_start_line = first line of body in file).
    """
    if not content:
        return set(), {}
    lines = content.split("\n")
    out_set = set()
    out_line = {}
    current = []
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


def word_shingles(text, size):
    """Return set of word n-grams (shingles) of given size. Words are lowercased."""
    words = text.lower().split()
    if len(words) < size:
        return set()
    return set(tuple(words[i : i + size]) for i in range(len(words) - size + 1))


def jaccard(a, b):
    """Jaccard similarity |A cap B| / |A cup B|. Returns 0 if both empty."""
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def read_first_line_and_body(path):
    """Return (first_line, body). Body is everything after the first line."""
    with open(path, "r", encoding=ENCODING) as f:
        content = f.read()
    if "\n" in content:
        first, _, body = content.partition("\n")
        return first, body
    return content, ""


class UnionFind:
    """Union-find for grouping file numbers (stored as strings)."""

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def _ensure(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        self._ensure(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1

    def components(self):
        """Return dict: root -> set of all elements in that component."""
        from collections import defaultdict
        comp = defaultdict(set)
        for x in self.parent:
            comp[self.find(x)].add(x)
        return comp


def main():
    parser = argparse.ArgumentParser(description="Find similar fanfic files by tags + text.")
    parser.add_argument("folder", nargs="?", default="Fanfics", help="Folder with .md files")
    parser.add_argument("--output", "-o", default="similar_fanfics_report.md", help="Output file path (default: repo root)")
    parser.add_argument("--tag-threshold", "-t", type=float, default=DEFAULT_TAG_THRESHOLD, help="Tag overlap must be > this (default: 0.9)")
    parser.add_argument("--min-paragraph-words", "-p", type=int, default=DEFAULT_MIN_PARAGRAPH_WORDS, help="Paragraph must have more than this many words (default: 26, i.e. >25)")
    parser.add_argument("--shingle-size", type=int, default=DEFAULT_SHINGLE_SIZE, help="Word shingle size (default: 5)")
    parser.add_argument("--shingle-jaccard", type=float, default=DEFAULT_SHINGLE_JACCARD, help="Shingle Jaccard threshold (default: 0.25)")
    parser.add_argument("--limit", type=int, default=0, help="Limit to first N files (0 = no limit, for testing)")
    args = parser.parse_args()

    print("find_similar_fanfics: starting", file=sys.stderr, flush=True)

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print("Error: folder not found:", folder, file=sys.stderr)
        sys.exit(1)

    # Resolve output to repo root if path is relative
    out_path = args.output
    if not os.path.isabs(out_path):
        # Assume script is in repo root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(script_dir, out_path)

    def write_progress(line):
        with open(out_path, "a", encoding=ENCODING) as f:
            f.write(line + "\n")
            f.flush()
        print(line, file=sys.stderr, flush=True)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    with open(out_path, "w", encoding=ENCODING) as f:
        f.write("# Similar fanfics report (tags + text)\n")
        f.write("# Tag overlap > {} | Min paragraph words > {} | Shingle Jaccard: {}\n".format(
            args.tag_threshold, args.min_paragraph_words - 1, args.shingle_jaccard))
        f.write("\n## Progress\n")
    write_progress("Step 1: Parsing .md files...")

    paths = get_md_files(folder)
    if args.limit > 0:
        paths = paths[: args.limit]
    # (number, path, tags) for files that have a number
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
    # Index: tag -> list of file indices. Then collect pairs that share any tag (each pair once).
    tag_to_indices = {}
    for i, (num, path, tags) in enumerate(files):
        for tag in tags:
            tag_to_indices.setdefault(tag, []).append(i)

    pairs_with_shared_tag = set()
    for indices in tag_to_indices.values():
        for ii in range(len(indices)):
            for jj in range(ii + 1, len(indices)):
                i, j = indices[ii], indices[jj]
                if i > j:
                    i, j = j, i
                pairs_with_shared_tag.add((i, j))

    write_progress("  {} tags, {} pairs with at least one shared tag.".format(
        len(tag_to_indices), len(pairs_with_shared_tag)))

    write_progress("Step 3: Filtering by tag overlap > {}...".format(args.tag_threshold))
    tag_candidates = set()
    for i, j in pairs_with_shared_tag:
        a, b = files[i][2], files[j][2]
        overlap = len(a & b) / min(len(a), len(b)) if a and b else 0
        if overlap > args.tag_threshold:
            tag_candidates.add((i, j))

    write_progress("  Tag candidates: {} pairs.".format(len(tag_candidates)))

    # Text confirmation: load body and long paragraphs only for files that appear in candidates
    file_indices_needed = set()
    for i, j in tag_candidates:
        file_indices_needed.add(i)
        file_indices_needed.add(j)

    write_progress("Step 4: Loading bodies and building paragraphs/shingles for {} files...".format(
        len(file_indices_needed)))

    paragraphs_by_index = {}
    paragraph_to_line_by_index = {}
    body_by_index = {}
    shingles_by_index = {}
    skipped = []
    for count, idx in enumerate(file_indices_needed):
        if (count + 1) % 100 == 0:
            write_progress("  Loaded {}/{} files...".format(count + 1, len(file_indices_needed)))
        _, path, _ = files[idx]
        try:
            first, body = read_first_line_and_body(path)
            body_by_index[idx] = body
            p_set, p_to_line = get_long_paragraphs_with_lines(body, args.min_paragraph_words, body_start_line=2)
            paragraphs_by_index[idx] = p_set
            paragraph_to_line_by_index[idx] = p_to_line
            shingles_by_index[idx] = word_shingles(body, args.shingle_size)
        except Exception as e:
            skipped.append((files[idx][0], path, str(e)))
            body_by_index[idx] = ""
            paragraphs_by_index[idx] = set()
            paragraph_to_line_by_index[idx] = {}
            shingles_by_index[idx] = set()
    if skipped:
        write_progress("  Skipped {} files (errors): {}.".format(len(skipped), skipped[:5]))
    write_progress("  Done.")

    def obsidian_link(path):
        rel = os.path.relpath(path, script_dir)
        return rel.replace("\\", "/").replace(".md", "")

    write_progress("Step 5: Text confirmation (exact paragraph / shingles)...")
    # Confirmed pairs: (i, j) -> (reasons, list of (paragraph, [(num, path, line), ...]))
    confirmed = {}
    for i, j in tag_candidates:
        reasons = set()
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
            if jaccard(sa, sb) >= args.shingle_jaccard:
                reasons.add("shingles")
        if reasons:
            confirmed[(i, j)] = (reasons, exact_paragraphs)

    exact_count = sum(1 for r, _ in confirmed.values() if "exact paragraph" in r)
    shingle_count = sum(1 for r, _ in confirmed.values() if "shingles" in r)
    write_progress("  Confirmed pairs: {} (exact paragraph: {}, shingles: {}).".format(
        len(confirmed), exact_count, shingle_count))

    write_progress("Step 6: Grouping (union-find)...")
    # Union-find by file number
    uf = UnionFind()
    pair_reasons = {}
    pair_paragraphs = {}  # (num_i, num_j) -> list of (paragraph, [(num, path, line), ...])
    for (i, j), (reasons, exact_paragraphs) in confirmed.items():
        num_i, num_j = files[i][0], files[j][0]
        uf.union(num_i, num_j)
        key = tuple(sorted([num_i, num_j], key=int))
        pair_reasons[key] = pair_reasons.get(key, set()) | reasons
        if exact_paragraphs:
            pair_paragraphs[key] = pair_paragraphs.get(key, []) + exact_paragraphs

    components = uf.components()
    groups = []
    for root, members in components.items():
        if len(members) < 2:
            continue
        sorted_nums = sorted(members, key=int)
        all_reasons = set()
        mem_list = list(members)
        for a in range(len(mem_list)):
            for b in range(a + 1, len(mem_list)):
                key = tuple(sorted([mem_list[a], mem_list[b]], key=int))
                all_reasons |= pair_reasons.get(key, set())
        reason_str = ", ".join(sorted(all_reasons))
        paragraph_locs = {}
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
                display = para if len(para) <= REPEATED_PARAGRAPH_TRUNCATE else para[:REPEATED_PARAGRAPH_TRUNCATE] + "..."
                write_progress("")
                write_progress("Repeated paragraph:")
                write_progress("> " + display.replace("\n", " "))
                link_parts = ["[[" + obsidian_link(path) + "]] (line " + str(line) + ")" for _, path, line in sorted(locs, key=lambda x: (int(x[0]), x[2]))]
                write_progress("In: " + ", ".join(link_parts))

    print("Done. {} groups written to {}.".format(len(groups), out_path), file=sys.stderr)


if __name__ == "__main__":
    main()
