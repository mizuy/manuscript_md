#!/usr/bin/env python3
"""Build/update paper checkme_paper.md citation dashboard (auto section).

Hand-edited notes outside the auto markers are preserved.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_bibliography import (  # noqa: E402
    extract_cite_keys_from_text,
    resolve_paperpile_bib,
    scan_keys_from_markdown,
)

BEGIN = "<!-- auto:checkme-dashboard -->"
END = "<!-- /auto:checkme-dashboard -->"


def _keys_in_bib(bib_path: Path) -> set[str]:
    if not bib_path.is_file():
        return set()
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"@\w+\{([^,]+),", text))


def _mark(ok: bool) -> str:
    return "✅" if ok else "⬜"


def build_dashboard(paper_dir: Path, *, paperpile: Path | None) -> str:
    paper_dir = paper_dir.resolve()
    md_dir = paper_dir / "reference" / "md"
    ref_bib = paper_dir / "reference" / "reference.bib"
    refs_bib = paper_dir / "references.bib"

    cited = scan_keys_from_markdown(paper_dir)
    cited_set = set(cited)

    ingest_keys = sorted(p.stem for p in md_dir.glob("*.md")) if md_dir.is_dir() else []
    ingest_set = set(ingest_keys)

    try:
        pp = resolve_paperpile_bib(paperpile)
        pp_keys = _keys_in_bib(pp)
        pp_label = str(pp)
    except FileNotFoundError:
        pp_keys = set()
        pp_label = "(paperpile.bib not found)"

    ref_keys = _keys_in_bib(ref_bib) if ref_bib.is_file() else set()
    # Prefer paperpile for "in paperpile" column; fall back to reference.bib
    in_pp = lambda k: k in pp_keys or k in ref_keys  # noqa: E731

    n_cited = len(cited)
    n_cited_pp = sum(1 for k in cited if in_pp(k))
    n_cited_ing = sum(1 for k in cited if k in ingest_set)

    reserve = [k for k in ingest_keys if k not in cited_set]
    n_res = len(reserve)
    n_res_pp = sum(1 for k in reserve if in_pp(k))

    lines = [
        BEGIN,
        "",
        f"_Generated {date.today().isoformat()} by `lab-paper checkme` "
        f"(manuscript-reference). Paperpile: `{pp_label}`._",
        "",
        "## 総合ダッシュボード",
        "",
        "| カテゴリ | 件数 | paperpile | ingest | 原稿 `[@key]` |",
        "|----------|------|-----------|--------|---------------|",
        f"| 原稿引用 | **{n_cited}** | {n_cited_pp}/{n_cited} {_mark(n_cited_pp == n_cited)} | "
        f"{n_cited_ing}/{n_cited} {_mark(n_cited_ing == n_cited)} | {n_cited}/{n_cited} ✅ |",
        f"| 文献メモのみ（未引用） | {n_res} | {n_res_pp}/{n_res} {_mark(n_res == 0 or n_res_pp == n_res)} | "
        f"{n_res}/{n_res} {_mark(n_res == 0 or True)} | 0/{n_res} ⬜ |",
        f"| **reference/md 合計** | **{len(ingest_keys)}** | — | {len(ingest_keys)} | — |",
        "",
        "### 原稿引用キー",
        "",
        "| pandoc-id | paperpile | ingest |",
        "|-----------|-----------|--------|",
    ]
    for k in cited:
        lines.append(f"| `{k}` | {_mark(in_pp(k))} | {_mark(k in ingest_set)} |")

    if reserve:
        lines += [
            "",
            "### 未引用（ingest のみ）",
            "",
            "| pandoc-id | paperpile |",
            "|-----------|-----------|",
        ]
        for k in reserve:
            lines.append(f"| `{k}` | {_mark(in_pp(k))} |")

    lines += [
        "",
        "### 確認コマンド",
        "",
        "```bash",
        f"cd {paper_dir}",
        "rg -o '\\[@[^\\]]+\\]' manuscript.md supplementary.md | sort -u",
        "ls reference/md/*.md | wc -l",
        "task paper:checkme   # or: lab-paper checkme --paper-dir .",
        "```",
        "",
        END,
        "",
    ]
    return "\n".join(lines)


def upsert_checkme(path: Path, dashboard: str) -> None:
    header = (
        f"# 文献チェックリスト（{path.parent.name}）\n\n"
        "運用: [manuscript-reference]("
        "https://github.com/mizuy/manuscript_md/blob/main/skills/manuscript-reference/SKILL.md)。\n\n"
        "手書きメモ（優先度・候補など）は **auto マーカーの下** に書いてください。"
        "ダッシュボード再生成ではマーカー外を保持します。\n\n"
    )
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        if BEGIN in text and END in text:
            pattern = re.compile(
                re.escape(BEGIN) + r".*?" + re.escape(END),
                re.S,
            )
            text = pattern.sub(dashboard.rstrip("\n"), text, count=1)
        else:
            text = header + dashboard + "\n---\n\n" + text.lstrip()
    else:
        text = header + dashboard + "\n---\n\n## 手書きメモ\n\n（任意）\n"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Default: PAPER_DIR/checkme_paper.md",
    )
    parser.add_argument("--paperpile-bib", type=Path, default=None)
    args = parser.parse_args()

    paper_dir = args.paper_dir.resolve()
    out = (args.out or (paper_dir / "checkme_paper.md")).resolve()
    dash = build_dashboard(paper_dir, paperpile=args.paperpile_bib)
    upsert_checkme(out, dash)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
