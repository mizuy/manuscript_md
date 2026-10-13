"""Character-level tracked-changes diff of two docx files without Word.

The output is a copy of CHANGED.docx whose body text carries w:ins / w:del
revisions against BASE.docx. Only text is compared: styles, run formatting,
and paragraph properties are ignored, and the output keeps CHANGED's
formatting. Uses the Python standard library only.

Limitations:
- Only word/document.xml is diffed (not footnotes, headers, comments).
- Table row/column insertions show as text changes, not row revisions.
- Deleted paragraphs are copied from BASE as plain text runs (no images).
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import difflib
import io
import itertools
import os
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
DOCUMENT_PART = "word/document.xml"
OBJECT_CHAR = "￼"


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


# Run children that carry visible text, mapped to their text value.
CHAR_ELEMENTS = {
    w("tab"): "\t",
    w("br"): "\n",
    w("cr"): "\n",
    w("noBreakHyphen"): "‑",
    w("softHyphen"): "­",
    w("drawing"): OBJECT_CHAR,
    w("pict"): OBJECT_CHAR,
    w("object"): OBJECT_CHAR,
    w("footnoteReference"): OBJECT_CHAR,
    w("endnoteReference"): OBJECT_CHAR,
}
REVISION_PROPERTY_CHANGES = {
    w("rPrChange"),
    w("pPrChange"),
    w("sectPrChange"),
    w("tblPrChange"),
    w("tblGridChange"),
    w("trPrChange"),
    w("tcPrChange"),
}


# --------------------------------------------------------------------------
# XML helpers


def parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def register_namespaces(data: bytes) -> None:
    for _, (prefix, uri) in ET.iterparse(io.BytesIO(data), events=("start-ns",)):
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass


def root_start_tag(data: bytes) -> bytes:
    text = re.sub(rb"^\s*<\?xml[^>]*\?>\s*", b"", data)
    match = re.match(rb"<[^!?][^>]*>", text)
    if not match:
        raise ValueError("cannot find root element")
    return match.group(0)


def serialize(root: ET.Element, original: bytes) -> bytes:
    """Serialize while restoring the original root namespace declarations.

    ElementTree only declares namespaces it uses, which would break
    mc:Ignorable prefixes; the root element itself is never modified.
    """
    body = ET.tostring(root, encoding="unicode").encode("utf-8")
    body = root_start_tag(original) + body[len(root_start_tag(body)) :]
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n' + body


def accept_existing_revisions(root: ET.Element) -> None:
    """Accept tracked changes already present so both inputs are clean."""
    parents = parent_map(root)
    # A deleted paragraph mark joins the paragraph with the next one.
    for p in list(root.iter(w("p"))):
        mark = p.find(f"{w('pPr')}/{w('rPr')}/{w('del')}")
        if mark is None:
            continue
        parent = parents[p]
        siblings = list(parent)
        following = siblings[siblings.index(p) + 1 :]
        parent.remove(p)
        if following and following[0].tag == w("p"):
            target = following[0]
            index = 1 if target.find(w("pPr")) is not None else 0
            for offset, child in enumerate(c for c in p if c.tag != w("pPr")):
                target.insert(index + offset, child)
    parents = parent_map(root)
    for elem in list(root.iter()):
        in_mark = elem in parents and parents[elem].tag == w("rPr")
        removed_run = elem.tag in (w("del"), w("moveFrom")) and not in_mark
        revision_mark = in_mark and elem.tag in (w("ins"), w("del"), w("moveFrom"), w("moveTo"))
        if removed_run or revision_mark or elem.tag in REVISION_PROPERTY_CHANGES:
            parents[elem].remove(elem)
    parents = parent_map(root)
    for elem in list(root.iter()):
        if elem.tag in (w("ins"), w("moveTo")) and elem in parents:
            parent = parents[elem]
            index = list(parent).index(elem)
            parent.remove(elem)
            for offset, child in enumerate(list(elem)):
                parent.insert(index + offset, child)
                parents[child] = parent
    for tag in ("moveFromRangeStart", "moveFromRangeEnd", "moveToRangeStart", "moveToRangeEnd"):
        for elem in list(root.iter(w(tag))):
            parent_map(root)[elem].remove(elem)


# --------------------------------------------------------------------------
# Paragraph text model


def body_paragraphs(root: ET.Element) -> list[ET.Element]:
    """Top-level text paragraphs in document order (incl. table cells)."""
    body = root.find(w("body"))
    if body is None:
        return []
    nested = {p for box in body.iter(w("txbxContent")) for p in box.iter(w("p"))}
    return [p for p in body.iter(w("p")) if p not in nested]


def paragraph_runs(p: ET.Element) -> list[ET.Element]:
    nested = {r for box in p.iter(w("txbxContent")) for r in box.iter(w("r"))}
    return [r for r in p.iter(w("r")) if r not in nested]


def element_text(child: ET.Element) -> str:
    if child.tag == w("t"):
        return child.text or ""
    if child.tag == w("sym"):
        char = child.get(w("char"), "")
        try:
            return chr(int(char, 16))
        except ValueError:
            return OBJECT_CHAR
    return CHAR_ELEMENTS.get(child.tag, "")


def paragraph_text(p: ET.Element) -> str:
    return "".join(
        element_text(child) for run in paragraph_runs(p) for child in run
    )


@dataclass
class Piece:
    """A run holding exactly one text-bearing child, at [start, end)."""

    run: ET.Element
    start: int
    end: int


def atomize(p: ET.Element) -> list[Piece]:
    """Split runs so every text-bearing child sits in its own run."""
    parents = parent_map(p)
    pieces: list[Piece] = []
    pos = 0
    for run in paragraph_runs(p):
        rpr = run.find(w("rPr"))
        content = [c for c in run if c.tag != w("rPr")]
        text_children = [c for c in content if element_text(c)]
        if not text_children:
            continue
        parent = parents[run]
        index = list(parent).index(run)
        parent.remove(run)
        groups: list[list[ET.Element]] = []
        current: list[ET.Element] = []
        for child in content:
            current.append(child)
            if element_text(child):
                groups.append(current)
                current = []
        if current:
            groups[-1].extend(current)
        for offset, group in enumerate(groups):
            new_run = ET.Element(run.tag, run.attrib)
            if rpr is not None:
                new_run.append(copy.deepcopy(rpr))
            new_run.extend(group)
            parent.insert(index + offset, new_run)
            length = sum(len(element_text(c)) for c in group)
            pieces.append(Piece(new_run, pos, pos + length))
            pos += length
    return pieces


def split_pieces(p: ET.Element, pieces: list[Piece], cuts: set[int]) -> list[Piece]:
    """Split w:t pieces so no piece crosses a cut position."""
    parents = parent_map(p)
    result: list[Piece] = []
    for piece in pieces:
        inner = sorted(c for c in cuts if piece.start < c < piece.end)
        if not inner:
            result.append(piece)
            continue
        children = [c for c in piece.run if c.tag != w("rPr")]
        t_index = next(k for k, c in enumerate(children) if c.tag == w("t"))
        before, t, after = children[:t_index], children[t_index], children[t_index + 1 :]
        rpr = piece.run.find(w("rPr"))
        bounds = [piece.start, *inner, piece.end]
        parent = parents[piece.run]
        index = list(parent).index(piece.run)
        parent.remove(piece.run)
        last = len(bounds) - 2
        for k, (a, b) in enumerate(itertools.pairwise(bounds)):
            run = ET.Element(piece.run.tag, piece.run.attrib)
            if rpr is not None:
                run.append(copy.deepcopy(rpr))
            if k == 0:
                run.extend(before)
            part = ET.SubElement(run, w("t"))
            part.text = (t.text or "")[a - piece.start : b - piece.start]
            part.set(XML_SPACE, "preserve")
            if k == last:
                run.extend(after)
            parent.insert(index + k, run)
            result.append(Piece(run, a, b))
    return result


# --------------------------------------------------------------------------
# Diff


Op = tuple[str, str]  # ("=", text) | ("-", text) | ("+", text)


def char_diff(old: str, new: str, cleanup: bool = True) -> list[Op]:
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    ops: list[Op] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            ops.append(("=", old[i1:i2]))
        else:
            if i2 > i1:
                ops.append(("-", old[i1:i2]))
            if j2 > j1:
                ops.append(("+", new[j1:j2]))
    return semantic_cleanup(ops) if cleanup else ops


def merge_ops(ops: list[Op]) -> list[Op]:
    """Merge neighbours and order each edit run as deletion then insertion."""
    result: list[Op] = []
    pending = {"-": "", "+": ""}

    def flush() -> None:
        for kind in "-+":
            if pending[kind]:
                result.append((kind, pending[kind]))
                pending[kind] = ""

    for kind, text in ops:
        if not text:
            continue
        if kind == "=":
            flush()
            if result and result[-1][0] == "=":
                result[-1] = ("=", result[-1][1] + text)
            else:
                result.append(("=", text))
        else:
            pending[kind] += text
    flush()
    return result


def semantic_cleanup(ops: list[Op]) -> list[Op]:
    """Fold short equalities between edits into the edits.

    Same rule as diff-match-patch's cleanupSemantic: an equality is dropped
    when it is no longer than the edits on both sides. This turns scattered
    single-letter matches into one readable replacement.
    """
    ops = merge_ops(ops)
    changed = True
    while changed:
        changed = False
        for k, (kind, text) in enumerate(ops):
            if kind != "=" or k == 0 or k == len(ops) - 1:
                continue
            m = k - 1
            dels = ins = 0
            while m >= 0 and ops[m][0] != "=":
                dels += len(ops[m][1]) if ops[m][0] == "-" else 0
                ins += len(ops[m][1]) if ops[m][0] == "+" else 0
                m -= 1
            before = (dels, ins)
            m = k + 1
            dels = ins = 0
            while m < len(ops) and ops[m][0] != "=":
                dels += len(ops[m][1]) if ops[m][0] == "-" else 0
                ins += len(ops[m][1]) if ops[m][0] == "+" else 0
                m += 1
            after = (dels, ins)
            if len(text) <= max(before) and len(text) <= max(after):
                ops = merge_ops(ops[:k] + [("-", text), ("+", text)] + ops[k + 1 :])
                changed = True
                break
    return ops


def align_paragraphs(old: list[str], new: list[str]) -> list[tuple[int | None, int | None]]:
    """Pair old/new paragraph indexes; None marks an unpaired side."""
    pairs: list[tuple[int | None, int | None]] = []
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            pairs.extend(zip(range(i1, i2), range(j1, j2)))
        else:
            pairs.extend(align_block(old, new, i1, i2, j1, j2))
    return pairs


def similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    if matcher.real_quick_ratio() < 0.4 or matcher.quick_ratio() < 0.4:
        return 0.0
    return matcher.ratio()


def align_block(old, new, i1, i2, j1, j2, threshold: float = 0.4):
    """Best monotonic pairing of a changed block by text similarity."""
    n, m = i2 - i1, j2 - j1
    if n * m > 250_000:
        sims = None
    else:
        sims = [[similarity(old[i1 + a], new[j1 + b]) for b in range(m)] for a in range(n)]
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    for a in range(n - 1, -1, -1):
        for b in range(m - 1, -1, -1):
            best = max(score[a + 1][b], score[a][b + 1])
            s = sims[a][b] if sims else 0.0
            if s >= threshold:
                best = max(best, s + score[a + 1][b + 1])
            score[a][b] = best
    pairs = []
    a = b = 0
    while a < n and b < m:
        s = sims[a][b] if sims else 0.0
        if s >= threshold and score[a][b] == s + score[a + 1][b + 1]:
            pairs.append((i1 + a, j1 + b))
            a += 1
            b += 1
        elif score[a + 1][b] >= score[a][b + 1]:
            pairs.append((i1 + a, None))
            a += 1
        else:
            pairs.append((None, j1 + b))
            b += 1
    pairs.extend((i1 + k, None) for k in range(a, n))
    pairs.extend((None, j1 + k) for k in range(b, m))
    return pairs


# --------------------------------------------------------------------------
# Revision markup


class Revisions:
    def __init__(self, author: str, date: str) -> None:
        self.author = author
        self.date = date
        self.next_id = 90_000

    def element(self, kind: str) -> ET.Element:
        self.next_id += 1
        return ET.Element(
            w(kind),
            {w("id"): str(self.next_id), w("author"): self.author, w("date"): self.date},
        )

    def deleted_run(self, text: str, rpr: ET.Element | None) -> ET.Element:
        run = ET.Element(w("r"))
        if rpr is not None:
            run.append(copy.deepcopy(rpr))
        buffer = ""

        def flush() -> None:
            nonlocal buffer
            if buffer:
                dt_elem = ET.SubElement(run, w("delText"))
                dt_elem.text = buffer
                dt_elem.set(XML_SPACE, "preserve")
                buffer = ""

        for char in text:
            if char == "\t":
                flush()
                ET.SubElement(run, w("tab"))
            elif char == "\n":
                flush()
                ET.SubElement(run, w("br"))
            elif char != OBJECT_CHAR:
                buffer += char
        flush()
        wrapper = self.element("del")
        wrapper.append(run)
        return wrapper

    def mark_paragraph(self, p: ET.Element, kind: str) -> None:
        ppr = p.find(w("pPr"))
        if ppr is None:
            ppr = ET.Element(w("pPr"))
            p.insert(0, ppr)
        rpr = ppr.find(w("rPr"))
        if rpr is None:
            rpr = ET.Element(w("rPr"))
            tail = [c for c in ppr if c.tag in (w("sectPr"), w("pPrChange"))]
            index = list(ppr).index(tail[0]) if tail else len(ppr)
            ppr.insert(index, rpr)
        rpr.insert(0, self.element(kind))


def apply_paragraph_diff(p: ET.Element, old_text: str, rev: Revisions, cleanup: bool) -> int:
    new_text = paragraph_text(p)
    if old_text == new_text:
        return 0
    ops = char_diff(old_text, new_text, cleanup)
    cuts = set()
    pos = 0
    for kind, text in ops:
        if kind != "-":
            cuts.add(pos)
            pos += len(text)
            cuts.add(pos)
    pieces = split_pieces(p, atomize(p), cuts)
    by_start = {piece.start: piece for piece in pieces}
    by_end = {piece.end: piece for piece in pieces}
    parents = parent_map(p)

    def container(piece: Piece) -> ET.Element:
        return parents[piece.run]

    # Wrap inserted pieces.
    pos = 0
    for kind, text in ops:
        if kind == "-":
            continue
        if kind == "+":
            for piece in pieces:
                if pos <= piece.start and piece.end <= pos + len(text):
                    parent = parents[piece.run]
                    index = list(parent).index(piece.run)
                    wrapper = rev.element("ins")
                    parent.remove(piece.run)
                    wrapper.append(piece.run)
                    parent.insert(index, wrapper)
                    parents[wrapper] = parent
                    parents[piece.run] = wrapper
        pos += len(text)

    # Place deletions at their position in the new text.
    def outer(run: ET.Element) -> ET.Element:
        node = run
        while parents[node].tag == w("ins"):
            node = parents[node]
        return node

    edits = 0
    pos = 0
    for kind, text in ops:
        if kind == "-":
            edits += 1
            prev_piece = by_end.get(pos)
            next_piece = by_start.get(pos)
            source = prev_piece or next_piece
            rpr = source.run.find(w("rPr")) if source else None
            deletion = rev.deleted_run(text, rpr)
            if next_piece is not None:
                node = outer(next_piece.run)
                parent = parents[node]
                parent.insert(list(parent).index(node), deletion)
            elif prev_piece is not None:
                node = outer(prev_piece.run)
                parent = parents[node]
                parent.insert(list(parent).index(node) + 1, deletion)
            else:
                p.append(deletion)
            parents[deletion] = p
            continue
        if kind == "+":
            edits += 1
        pos += len(text)
    merge_adjacent_wrappers(p)
    return edits


def merge_adjacent_wrappers(root: ET.Element) -> None:
    for parent in list(root.iter()):
        children = list(parent)
        k = 0
        while k < len(children) - 1:
            a, b = children[k], children[k + 1]
            if a.tag in (w("ins"), w("del")) and a.tag == b.tag:
                a.extend(list(b))
                parent.remove(b)
                children.pop(k + 1)
            else:
                k += 1


def insert_whole_paragraph(p: ET.Element, rev: Revisions) -> None:
    for piece in atomize(p):
        parents = parent_map(p)
        parent = parents[piece.run]
        index = list(parent).index(piece.run)
        wrapper = rev.element("ins")
        parent.remove(piece.run)
        wrapper.append(piece.run)
        parent.insert(index, wrapper)
    merge_adjacent_wrappers(p)
    rev.mark_paragraph(p, "ins")


def deleted_paragraph(old_p: ET.Element, rev: Revisions) -> ET.Element:
    """A plain-text copy of an old paragraph, marked fully deleted."""
    p = ET.Element(w("p"))
    ppr = old_p.find(w("pPr"))
    if ppr is not None:
        ppr = copy.deepcopy(ppr)
        for child in list(ppr):
            if child.tag in (w("sectPr"), w("pPrChange"), w("numPr")):
                ppr.remove(child)
        p.append(ppr)
    for run in paragraph_runs(old_p):
        text = "".join(element_text(c) for c in run)
        if text.strip(OBJECT_CHAR):
            p.append(rev.deleted_run(text, run.find(w("rPr"))))
    merge_adjacent_wrappers(p)
    rev.mark_paragraph(p, "del")
    return p


# --------------------------------------------------------------------------
# Driver


def diff_documents(
    base_xml: bytes,
    changed_xml: bytes,
    author: str = "manuscript_md",
    date: str | None = None,
    cleanup: bool = True,
) -> tuple[bytes, dict[str, int]]:
    register_namespaces(base_xml)
    register_namespaces(changed_xml)
    base_root = ET.fromstring(base_xml)
    new_root = ET.fromstring(changed_xml)
    accept_existing_revisions(base_root)
    accept_existing_revisions(new_root)
    date = date or dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rev = Revisions(author, date)

    old_ps = body_paragraphs(base_root)
    new_ps = body_paragraphs(new_root)
    old_texts = [paragraph_text(p) for p in old_ps]
    new_texts = [paragraph_text(p) for p in new_ps]
    pairs = align_paragraphs(old_texts, new_texts)
    parents = parent_map(new_root)
    stats = {"changed": 0, "inserted": 0, "deleted": 0, "edits": 0}

    last_new: int | None = None
    pending_deletes: list[tuple[int, int | None]] = []
    for i, j in pairs:
        if i is not None and j is not None:
            edits = apply_paragraph_diff(new_ps[j], old_texts[i], rev, cleanup)
            stats["edits"] += edits
            stats["changed"] += bool(edits)
            last_new = j
        elif j is not None:
            insert_whole_paragraph(new_ps[j], rev)
            stats["inserted"] += 1
            last_new = j
        else:
            pending_deletes.append((i, last_new))

    # Insert deleted paragraphs after the preceding new paragraph, keeping
    # them out of table cells when the old paragraph was in the body.
    offsets: dict[int | None, int] = {}
    for i, after in pending_deletes:
        old_p = old_ps[i]
        old_in_cell = any(old_p in list(tc) for tc in base_root.iter(w("tc")))
        new_p = deleted_paragraph(old_p, rev)
        anchor = new_ps[after] if after is not None else None
        if anchor is not None and (parents[anchor].tag == w("tc")) == old_in_cell:
            parent = parents[anchor]
            index = list(parent).index(anchor) + 1 + offsets.get(after, 0)
            offsets[after] = offsets.get(after, 0) + 1
        else:
            following = next(
                (new_ps[j] for j in range((after or -1) + 1, len(new_ps))), None
            )
            if following is not None and (parents[following].tag == w("tc")) == old_in_cell:
                parent = parents[following]
                index = list(parent).index(following)
            elif anchor is not None:
                # Fall back to the top level of the body after the anchor's table.
                node = anchor
                while parents[node].tag != w("body"):
                    node = parents[node]
                parent = parents[node]
                index = list(parent).index(node) + 1 + offsets.get(after, 0)
                offsets[after] = offsets.get(after, 0) + 1
            else:
                parent = new_root.find(w("body"))
                index = offsets.get(None, 0)
                offsets[None] = index + 1
        parent.insert(index, new_p)
        parents[new_p] = parent
        stats["deleted"] += 1

    return serialize(new_root, changed_xml), stats


def diff_docx(
    base: Path,
    changed: Path,
    output: Path,
    author: str = "manuscript_md",
    cleanup: bool = True,
) -> dict[str, int]:
    with zipfile.ZipFile(base) as zb:
        base_xml = zb.read(DOCUMENT_PART)
    with zipfile.ZipFile(changed) as zc:
        changed_xml = zc.read(DOCUMENT_PART)
        result, stats = diff_documents(base_xml, changed_xml, author, cleanup=cleanup)
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f".{output.stem}.", suffix=".docx", dir=output.parent)
        os.close(fd)
        try:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
                for item in zc.infolist():
                    data = result if item.filename == DOCUMENT_PART else zc.read(item.filename)
                    zo.writestr(item, data)
            os.replace(tmp, output)
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            raise
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="manuscript-md diff-docx",
        description=(
            "Write CHANGED.docx with character-level tracked changes against "
            "BASE.docx. Formatting differences are ignored."
        ),
    )
    parser.add_argument("base", type=Path, help="older docx")
    parser.add_argument("changed", type=Path, help="newer docx (output keeps its formatting)")
    parser.add_argument("output", type=Path, help="tracked-changes docx to write")
    parser.add_argument("--author", default="manuscript_md", help="revision author label")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="keep the raw character diff (no merging of short matches)",
    )
    args = parser.parse_args(argv)
    stats = diff_docx(args.base, args.changed, args.output, args.author, cleanup=not args.raw)
    print(
        f"Wrote {args.output}: {stats['changed']} paragraphs changed "
        f"({stats['edits']} edits), {stats['inserted']} inserted, "
        f"{stats['deleted']} deleted"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
