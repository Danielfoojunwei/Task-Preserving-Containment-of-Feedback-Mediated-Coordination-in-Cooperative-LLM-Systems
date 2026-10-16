#!/usr/bin/env python3
"""Render the released Markdown working report locally, without network access.

Importing this module reads no report and writes no file. Rendering requires an
explicit --release, completed result markers, and a previously unused PDF path.
This is a working-report renderer, not the official Apart submission template.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import html
import io
import json
import math
from pathlib import Path
import re
import sys
from typing import Iterable
from urllib.parse import urlparse

from reportlab import __version__ as REPORTLAB_VERSION
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 45
MARGIN_TOP = 43
MARGIN_BOTTOM = 45
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN_X
CONTENT_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
UNFINISHED = re.compile(
    r"<!--\s*(?:SECONDARY_RESULTS|CONTINUATION_RESULTS|[^>]*\b(?:TODO|TBD|PENDING|PLACEHOLDER)\b[^>]*)\s*-->",
    re.IGNORECASE,
)
TOKEN = re.compile(
    r"(`+)(.+?)\1|\[([^\]\n]+)\]\(([^\n]+?)\)|\*\*(.+?)\*\*|__(.+?)__|(?<!\*)\*([^*\n]+)\*(?!\*)"
)


@dataclass(frozen=True)
class Block:
    kind: str
    text: str = ""
    level: int = 0
    rows: tuple[tuple[str, ...], ...] = ()
    target: str = ""


def table_cells(line: str) -> tuple[str, ...]:
    """Split a pipe row without splitting escaped pipes or pipes in code spans."""
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|") and not value.endswith("\\|"):
        value = value[:-1]
    cells, current = [], []
    escaped, code_ticks = False, 0
    index = 0
    while index < len(value):
        char = value[index]
        if escaped:
            current.append(char if char == "|" else "\\" + char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "`":
            end = index
            while end < len(value) and value[end] == "`":
                end += 1
            count = end - index
            code_ticks = 0 if code_ticks == count else count if not code_ticks else code_ticks
            current.append(value[index:end])
            index = end - 1
        elif char == "|" and not code_ticks:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return tuple(cells)


def table_separator(line: str) -> bool:
    cells = table_cells(line)
    return len(cells) > 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_markdown(source: str) -> list[Block]:
    """Parse the report's small Markdown subset, preserving every prose block."""
    lines = source.splitlines()
    blocks: list[Block] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        fence = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker = fence.group(1)
            code = []
            index += 1
            while index < len(lines) and not re.fullmatch(
                rf"\s*{re.escape(marker[0])}{{{len(marker)},}}\s*", lines[index]
            ):
                code.append(lines[index])
                index += 1
            if index == len(lines):
                raise ValueError("Unclosed fenced code block; no PDF written")
            blocks.append(Block("code", "\n".join(code)))
            index += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", stripped)
        if heading:
            blocks.append(Block("heading", heading.group(2), len(heading.group(1))))
            index += 1
            continue
        image = re.fullmatch(r"!\[([^\]]*)\]\((.+?)\)", stripped)
        if image:
            blocks.append(Block("image", image.group(1), target=image.group(2)))
            index += 1
            continue
        if index + 1 < len(lines) and "|" in line and table_separator(lines[index + 1]):
            rows = [table_cells(line)]
            index += 2
            while index < len(lines) and lines[index].strip() and "|" in lines[index]:
                cells = table_cells(lines[index])
                if len(cells) != len(rows[0]):
                    raise ValueError(f"Inconsistent Markdown table width at line {index + 1}")
                rows.append(cells)
                index += 1
            blocks.append(Block("table", rows=tuple(rows)))
            continue
        if re.fullmatch(r"(?:-{3,}|\*{3,}|_{3,})", stripped):
            blocks.append(Block("rule"))
            index += 1
            continue
        bullet = re.match(r"^(\s*)([-+*]|\d+[.)])\s+(.+)$", line)
        if bullet:
            parts = [bullet.group(3)]
            index += 1
            while index < len(lines) and lines[index].strip() and re.match(r"^\s{2,}\S", lines[index]) and not re.match(r"^\s*(?:[-+*]|\d+[.)])\s", lines[index]):
                parts.append(lines[index].strip())
                index += 1
            label = "•" if bullet.group(2) in "-+*" else bullet.group(2)
            blocks.append(Block("list", " ".join(parts), min(len(bullet.group(1)) // 2, 4), target=label))
            continue
        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            parts = [quote.group(1)]
            index += 1
            while index < len(lines) and lines[index].lstrip().startswith(">"):
                parts.append(re.sub(r"^\s*>\s?", "", lines[index]))
                index += 1
            blocks.append(Block("quote", " ".join(parts)))
            continue
        # Comments are not printable prose. Reject rather than silently discard
        # any that remain in the release source, including unresolved markers.
        if "<!--" in line or "-->" in line:
            raise ValueError(f"Unresolved HTML comment at line {index + 1}; no PDF written")
        parts = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip():
            next_line = lines[index]
            if re.match(r"^\s*(?:#{1,6}\s|`{3,}|~{3,}|!\[|>|[-+*]\s|\d+[.)]\s)", next_line):
                break
            if index + 1 < len(lines) and "|" in next_line and table_separator(lines[index + 1]):
                break
            if "<!--" in next_line or "-->" in next_line:
                break
            parts.append(next_line.strip())
            index += 1
        blocks.append(Block("paragraph", " ".join(parts)))
    return blocks


def inline(value: str, depth: int = 0) -> str:
    if depth > 8:
        raise ValueError("Excessive inline nesting")
    result, cursor = [], 0
    for match in TOKEN.finditer(value):
        result.append(html.escape(value[cursor:match.start()]))
        if match.group(1):
            result.append('<font name="ReportMono">' + html.escape(match.group(2)) + "</font>")
        elif match.group(3) is not None:
            target = match.group(4).strip()
            parsed = urlparse(target)
            if parsed.scheme.lower() not in {"", "http", "https", "mailto", "file"}:
                raise ValueError(f"Unsupported link scheme: {parsed.scheme}")
            result.append(f'<link href="{html.escape(target, quote=True)}" color="#175985">' + inline(match.group(3), depth + 1) + "</link>")
        elif match.group(5) is not None or match.group(6) is not None:
            result.append("<b>" + inline(match.group(5) or match.group(6), depth + 1) + "</b>")
        else:
            result.append("<i>" + inline(match.group(7), depth + 1) + "</i>")
        cursor = match.end()
    result.append(html.escape(value[cursor:]))
    return "".join(result)


def register_fonts(font_dir: Path) -> None:
    filenames = {
        "ReportSans": "DejaVuSans.ttf",
        "ReportSansBold": "DejaVuSans-Bold.ttf",
        "ReportSansItalic": "DejaVuSans-Oblique.ttf",
        "ReportSansBoldItalic": "DejaVuSans-BoldOblique.ttf",
        "ReportMono": "DejaVuSansMono.ttf",
        "ReportMonoBold": "DejaVuSansMono-Bold.ttf",
        "ReportMonoItalic": "DejaVuSansMono-Oblique.ttf",
        "ReportMonoBoldItalic": "DejaVuSansMono-BoldOblique.ttf",
    }
    for name, filename in filenames.items():
        path = font_dir / filename
        if not path.is_file():
            raise ValueError(f"Required embedded font unavailable: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    for family in ["ReportSans", "ReportMono"]:
        pdfmetrics.registerFontFamily(family, normal=family, bold=family + "Bold", italic=family + "Italic", boldItalic=family + "BoldItalic")


def check_glyphs(source: str) -> None:
    available = pdfmetrics.getFont("ReportSans").face.charWidths
    missing = sorted({ch for ch in source if not ch.isspace() and ord(ch) not in available})
    if missing:
        raise ValueError("Embedded DejaVuSans lacks glyphs: " + ", ".join(f"{ch!r} U+{ord(ch):04X}" for ch in missing))


def make_styles(body_size: float) -> dict[str, ParagraphStyle]:
    body = ParagraphStyle("body", fontName="ReportSans", fontSize=body_size, leading=body_size * 1.39, textColor=colors.HexColor("#18232b"), alignment=TA_LEFT, spaceAfter=6.5, splitLongWords=True, allowWidows=0, allowOrphans=0)
    styles = {"body": body}
    for level, size in [(1, 20), (2, 13), (3, 11), (4, 10.5), (5, 10.2), (6, 10.2)]:
        styles[f"h{level}"] = ParagraphStyle(f"h{level}", parent=body, fontName="ReportSansBold", fontSize=size, leading=size * 1.22, spaceBefore=13 if level > 1 else 0, spaceAfter=7, keepWithNext=True)
    styles["quote"] = ParagraphStyle("quote", parent=body, leftIndent=13, borderColor=colors.HexColor("#9eb0bd"), borderWidth=1, borderPadding=6, textColor=colors.HexColor("#334d5e"))
    styles["caption"] = ParagraphStyle("caption", parent=body, fontSize=8.5, leading=11.6, textColor=colors.HexColor("#465b69"), spaceBefore=3, spaceAfter=10)
    styles["table"] = ParagraphStyle("table", parent=body, fontSize=8.1, leading=11.2, spaceAfter=0, spaceBefore=0, allowWidows=1, allowOrphans=1)
    styles["table_header"] = ParagraphStyle("table_header", parent=styles["table"], fontName="ReportSansBold", textColor=colors.HexColor("#15374c"))
    styles["code"] = ParagraphStyle("code", parent=body, fontName="ReportMono", fontSize=8.4, leading=11.3, leftIndent=8, rightIndent=8, spaceAfter=9)
    return styles


def wrap_code(text: str, width: float, font_size: float) -> str:
    """Soft-wrap long physical lines without deleting characters."""
    lines = []
    for physical_line in text.expandtabs(4).split("\n"):
        if not physical_line:
            lines.append("")
            continue
        current = ""
        for char in physical_line:
            if current and pdfmetrics.stringWidth(current + char, "ReportMono", font_size) > width:
                lines.append(current)
                current = char
            else:
                current += char
        lines.append(current)
    return "\n".join(lines)


def column_widths(rows: tuple[tuple[str, ...], ...]) -> list[float]:
    count = len(rows[0])
    weights = []
    for column in range(count):
        length = max(len(re.sub(r"[`*_]", "", row[column])) for row in rows)
        weights.append(math.sqrt(max(12, min(length, 180))))
    minimum = min(43.0, CONTENT_WIDTH / count * 0.70)
    remaining = CONTENT_WIDTH - minimum * count
    return [minimum + remaining * weight / sum(weights) for weight in weights]


def local_image(target: str, base: Path) -> Path:
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        raise ValueError("Images must be local files; this renderer never downloads images")
    path = Path(target)
    path = path if path.is_absolute() else base / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"Image unavailable: {path}")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise ValueError(f"Use a PNG/JPEG figure (SVG/PDF conversion is not implicit): {path}")
    return path


def image_flowables(path: Path, caption: str, styles: dict[str, ParagraphStyle]) -> list:
    image = Image(str(path), lazy=0)
    scale = min(CONTENT_WIDTH / image.imageWidth, (CONTENT_HEIGHT - 55) / image.imageHeight)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    image.hAlign = "CENTER"
    result = [Spacer(1, 7), image]
    if caption:
        result.append(Paragraph(inline(caption), styles["caption"]))
    result.append(Spacer(1, 6))
    return result


class WorkingReport(BaseDocTemplate):
    def __init__(self, destination, *, title: str):
        super().__init__(destination, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X, topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM, title=title, author="", subject="AI-assisted pre-sprint research working report", creator="Local ReportLab working-report renderer")
        frame = Frame(MARGIN_X, MARGIN_BOTTOM, CONTENT_WIDTH, CONTENT_HEIGHT, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="body")
        self.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=self.footer))
        self.final_page_count = 0

    @staticmethod
    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#ccd5dc"))
        canvas.line(MARGIN_X, 31, PAGE_WIDTH - MARGIN_X, 31)
        canvas.setFont("ReportSans", 7.4)
        canvas.setFillColor(colors.HexColor("#526570"))
        canvas.drawString(MARGIN_X, 20, "Research working report · AI-assisted · Pre-sprint work")
        canvas.drawRightString(PAGE_WIDTH - MARGIN_X, 20, str(document.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if getattr(flowable, "report_heading", None):
            level, title, anchor = flowable.report_heading
            self.canv.bookmarkPage(anchor)
            self.canv.addOutlineEntry(title, anchor, min(level - 1, 1), closed=False)

    def afterPage(self):
        self.final_page_count = self.page


def story_from_blocks(blocks: Iterable[Block], source_dir: Path, styles: dict[str, ParagraphStyle]) -> list:
    story, heading_counts = [], Counter()
    for block in blocks:
        if block.kind == "heading":
            slug = re.sub(r"[^\w-]+", "-", block.text.lower()).strip("-") or "heading"
            heading_counts[slug] += 1
            anchor = slug if heading_counts[slug] == 1 else f"{slug}-{heading_counts[slug]}"
            paragraph = Paragraph(f'<a name="{html.escape(anchor, quote=True)}"/>' + inline(block.text), styles[f"h{block.level}"])
            paragraph.report_heading = (block.level, re.sub(r"[`*_]", "", block.text), anchor)
            story.append(paragraph)
        elif block.kind == "paragraph":
            story.append(Paragraph(inline(block.text), styles["body"]))
        elif block.kind == "quote":
            story.append(Paragraph(inline(block.text), styles["quote"]))
        elif block.kind == "list":
            style = ParagraphStyle("item", parent=styles["body"], leftIndent=13 + 12 * block.level, firstLineIndent=0, bulletIndent=12 * block.level, bulletFontName="ReportSans", bulletFontSize=styles["body"].fontSize, spaceAfter=4)
            story.append(Paragraph(inline(block.text), style, bulletText=block.target))
        elif block.kind == "code":
            code = wrap_code(block.text, CONTENT_WIDTH - 16, styles["code"].fontSize)
            story.append(Preformatted(code, styles["code"]))
        elif block.kind == "table":
            rows = [[Paragraph(inline(cell), styles["table_header" if index == 0 else "table"]) for cell in row] for index, row in enumerate(block.rows)]
            table = Table(rows, colWidths=column_widths(block.rows), repeatRows=1, splitByRow=1, splitInRow=1, hAlign="LEFT", spaceBefore=4, spaceAfter=11)
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eef3")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#8fa4b4")),
                ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.HexColor("#bdcbd5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(table)
        elif block.kind == "image":
            story.extend(image_flowables(local_image(block.target, source_dir), block.text, styles))
        elif block.kind == "rule":
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bdcbd5"), spaceBefore=5, spaceAfter=8))
        else:
            raise ValueError(f"Unsupported parsed block kind: {block.kind}")
    return story


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", action="store_true", help="Explicit coordinator authorization after final report markers are replaced")
    parser.add_argument("--source", type=Path, default=ROOT / "REPORT.md")
    parser.add_argument("--output", type=Path, required=True, help="New, previously unused .pdf path")
    parser.add_argument("--figure", type=Path, action="append", default=[], help="Optional local PNG/JPEG appended after the source, repeatable; inline Markdown images are also supported")
    parser.add_argument("--font-dir", type=Path, default=Path("/usr/share/fonts/truetype/dejavu"))
    parser.add_argument("--body-size", type=float, default=10.2, help="Body size in points, 9–12; never automatically reduced")
    args = parser.parse_args(argv)
    if not args.release:
        parser.error("Rendering is locked: supply --release only after coordinator release")
    if not 9 <= args.body_size <= 12:
        parser.error("--body-size must be 9–12 points")
    source_path, output_path = args.source.resolve(), args.output.resolve()
    if output_path.suffix.lower() != ".pdf":
        parser.error("--output must end in .pdf")
    if output_path.exists():
        parser.error(f"Refusing to overwrite existing output: {output_path}")
    source_bytes = source_path.read_bytes()
    source = source_bytes.decode("utf-8")
    if UNFINISHED.search(source):
        parser.error("Report still contains an unfinished result marker; no PDF written")
    blocks = parse_markdown(source)
    if not blocks or blocks[0].kind != "heading":
        parser.error("Report must begin with its existing title heading")
    register_fonts(args.font_dir)
    check_glyphs(source)
    styles = make_styles(args.body_size)
    story = story_from_blocks(blocks, source_path.parent, styles)
    figure_records = []
    for figure in args.figure:
        path = local_image(str(figure), Path.cwd())
        story.extend(image_flowables(path, "", styles))
        figure_records.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    # Build in memory; exclusive final creation avoids partial or overwritten PDFs.
    # No source, review, result, protocol or figure file is modified.
    memory = io.BytesIO()
    document = WorkingReport(memory, title=blocks[0].text)
    document.build(story)
    if source_path.read_bytes() != source_bytes:
        raise RuntimeError("Source changed during rendering; no PDF written")
    with output_path.open("xb") as handle:
        handle.write(memory.getvalue())
    print(json.dumps({"output": str(output_path), "pages": document.final_page_count, "bytes": output_path.stat().st_size, "pdf_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(), "source": str(source_path), "source_sha256": hashlib.sha256(source_bytes).hexdigest(), "source_words": len(source.split()), "blocks": dict(Counter(block.kind for block in blocks)), "appended_figures": figure_records, "body_size": args.body_size, "reportlab_version": REPORTLAB_VERSION, "status": "AI-assisted pre-sprint working report; not an official template submission"}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError) as error:
        print(f"render_report: {error}", file=sys.stderr)
        raise SystemExit(1)
