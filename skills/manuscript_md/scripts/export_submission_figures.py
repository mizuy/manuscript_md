#!/usr/bin/env python3
"""Export Markdown-referenced figures as journal TIFF files at a target DPI."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def _require_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Pillow is required for TIFF export. Install with: "
            "uv add pillow  (in lab/manuscript_md) or use an environment that provides PIL."
        ) from exc
    from PIL import Image

    return Image


def iter_image_paths(markdown: Path) -> list[Path]:
    text = markdown.read_text(encoding="utf-8")
    paper_dir = markdown.parent
    seen: set[Path] = set()
    ordered: list[Path] = []
    for match in IMAGE_RE.finditer(text):
        raw = match.group(1).strip()
        path = Path(raw)
        if not path.is_absolute():
            path = (paper_dir / path).resolve()
        if path in seen:
            continue
        seen.add(path)
        ordered.append(path)
    return ordered


def source_dpi(image, default: float = 300.0) -> float:
    info = image.info.get("dpi")
    if not info:
        return default
    try:
        return float(info[0])
    except (TypeError, ValueError, IndexError):
        return default


def to_rgb(image, Image):
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def export_tiff(
    src: Path,
    dst: Path,
    *,
    target_dpi: int,
    Image,
) -> dict:
    if not src.is_file():
        raise FileNotFoundError(f"figure not found: {src}")

    with Image.open(src) as opened:
        image = to_rgb(opened, Image)
        dpi0 = source_dpi(opened)
        scale = target_dpi / dpi0 if dpi0 > 0 else 1.0
        if abs(scale - 1.0) > 0.01:
            new_size = (
                max(1, round(image.width * scale)),
                max(1, round(image.height * scale)),
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        else:
            new_size = image.size

        dst.parent.mkdir(parents=True, exist_ok=True)
        image.save(
            dst,
            format="TIFF",
            dpi=(target_dpi, target_dpi),
            compression="tiff_lzw",
        )

    return {
        "source": str(src),
        "output": str(dst),
        "source_dpi": dpi0,
        "target_dpi": target_dpi,
        "output_size": list(new_size),
    }


def numbered_name(prefix: str, index: int) -> str:
    return f"{prefix}_{index}.tif"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export figures cited in Markdown to TIFF at a target DPI."
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        required=True,
        help="Paper directory containing manuscript.md / fig/",
    )
    parser.add_argument(
        "--files",
        default="manuscript supplementary",
        help="Space-separated Markdown stems (default: manuscript supplementary)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory for TIFFs (default: PAPER_DIR/submission/figures)",
    )
    parser.add_argument("--dpi", type=int, default=600, help="Target DPI (default: 600)")
    parser.add_argument(
        "--prefix-manuscript",
        default="Figure",
        help="Filename prefix for manuscript figures (default: Figure)",
    )
    parser.add_argument(
        "--prefix-supplementary",
        default="Supplementary_Figure",
        help="Filename prefix for supplementary figures",
    )
    args = parser.parse_args(argv)

    Image = _require_pillow()
    paper_dir = args.paper_dir.expanduser().resolve()
    out_dir = (
        args.out_dir.expanduser().resolve()
        if args.out_dir is not None
        else paper_dir / "submission" / "figures"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    for stem in args.files.split():
        md = paper_dir / f"{stem}.md"
        if not md.is_file():
            print(f"skip missing markdown: {md}", file=sys.stderr)
            continue
        if stem == "manuscript":
            prefix = args.prefix_manuscript
        elif stem.startswith("supplement"):
            prefix = args.prefix_supplementary
        else:
            prefix = stem.replace(" ", "_")

        paths = iter_image_paths(md)
        for i, src in enumerate(paths, start=1):
            dst = out_dir / numbered_name(prefix, i)
            rec = export_tiff(src, dst, target_dpi=args.dpi, Image=Image)
            rec["markdown"] = stem
            rec["label"] = f"{prefix} {i}"
            records.append(rec)
            print(f"{rec['label']}: {src.name} -> {dst.name} ({rec['output_size'][0]}x{rec['output_size'][1]} @ {args.dpi} dpi)")

    manifest = out_dir / "manifest.json"
    manifest.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest} ({len(records)} figures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
