#!/usr/bin/env python3
"""Render the local five-slide Markdown only; no study-data reads or APIs.

This intentionally small renderer supports this deck's paragraphs, tables,
links, emphasis, fenced code and ::: notes blocks. Browser print yields five
landscape PDF pages. It does not supply or infer experimental results.
"""
import html
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def inline(text):
    escaped = html.escape(text)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def blocks(text):
    lines = text.strip().splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "::: notes":
            end = lines.index(":::", i + 1)
            out.append('<details class="notes"><summary>Speaker notes</summary>'
                       + blocks("\n".join(lines[i + 1:end])) + "</details>")
            i = end + 1
        elif line.startswith("```"):
            end = next(j for j in range(i + 1, len(lines)) if lines[j].strip() == "```")
            out.append("<pre>" + html.escape("\n".join(lines[i + 1:end])) + "</pre>")
            i = end + 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", x) for x in row):
                    rows.append(row)
                i += 1
            head = "<thead><tr>" + "".join("<th>" + inline(x) + "</th>" for x in rows[0]) + "</tr></thead>"
            body = "<tbody>" + "".join("<tr>" + "".join("<td>" + inline(x) + "</td>" for x in row) + "</tr>" for row in rows[1:]) + "</tbody>"
            out.append("<table>" + head + body + "</table>")
        elif line.startswith("> "):
            out.append('<div class="reserved">' + inline(line[2:]) + "</div>")
            i += 1
        else:
            paragraph = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("|", "```", "::: notes", "> ")):
                paragraph.append(lines[i].strip())
                i += 1
            joined = " ".join(paragraph)
            css = ' class="sources"' if joined.startswith(("Sources:", "Source contract:")) else ""
            out.append("<p" + css + ">" + inline(joined) + "</p>")
    return "\n".join(out)


STYLE = """
:root{color-scheme:light;font-family:Arial,Helvetica,sans-serif;background:#e9eef3;color:#14283d}
*{box-sizing:border-box}body{margin:0}.toolbar{max-width:1280px;margin:16px auto;padding:0 12px;display:flex;justify-content:space-between;gap:16px;font-size:13px}
button{border:0;background:#163c5d;color:white;padding:8px 14px;border-radius:5px;cursor:pointer}
.slide{width:min(1280px,96vw);min-height:720px;margin:20px auto;padding:34px 44px 24px;background:white;border-top:8px solid #008575;box-shadow:0 3px 18px #14283d18;position:relative}
.kicker{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#456477;margin-bottom:12px}
h1{font-size:30px;line-height:1.16;margin:0 0 20px;letter-spacing:-.025em}p{font-size:18px;line-height:1.4;margin:14px 0}strong{color:#123954}
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:16px;line-height:1.35}th{text-align:left;background:#e6f2f0;color:#123954}th,td{padding:10px 12px;border-bottom:1px solid #d4dfe5;vertical-align:top}td:first-child{font-weight:600}
a{color:#087366;text-decoration:none}a:hover{text-decoration:underline}code{font-family:ui-monospace,monospace;font-size:.9em;background:#f0f4f6;padding:1px 4px}pre{white-space:pre-wrap;font-size:15px;line-height:1.5;background:#edf4f6;padding:12px 16px}
.sources{font-size:12px;line-height:1.4;color:#526779;margin-top:18px}.reserved{border:1px dashed #b2c4cf;background:#f5f8fa;padding:16px;font-size:16px;color:#4a6173;margin:14px 0}.notes{font-size:14px;line-height:1.5;border-top:1px solid #d4dfe5;padding-top:10px;color:#526779}.notes summary{cursor:pointer}.notes p{font-size:14px}.footer{font-size:11px;color:#607989;display:flex;justify-content:space-between;margin-top:18px}
@page{size:13.333in 7.5in;margin:0}
@media print{html,body{background:white;margin:0}.toolbar,.notes{display:none}.slide{width:13.333in;height:7.5in;min-height:0;margin:0;padding:26px 36px 20px;box-shadow:none;break-after:page;overflow:hidden}.slide:last-child{break-after:auto}h1{font-size:27px;margin-bottom:14px}p{font-size:16px;line-height:1.34;margin:12px 0}table{font-size:14px;margin:12px 0}th,td{padding:8px 10px}.sources{font-size:10px;margin-top:14px}.reserved{padding:12px;font-size:14px;margin:12px 0}.footer{margin-top:14px;font-size:10px}pre{font-size:13px;padding:9px 12px}}
"""


def build():
    source = (HERE / "SLIDES.md").read_text()
    pieces = re.split(r"^## Slide ([1-5]) — (.+)$", source, flags=re.M)
    if len(pieces) != 16 or pieces[1::3] != list("12345"):
        raise ValueError("The deck must contain exactly slides 1–5 in order")
    sections = []
    for n, title, text in zip(pieces[1::3], pieces[2::3], pieces[3::3]):
        sections.append('<section class="slide"><div class="kicker">Overt / covert agreement study · prospective skeleton</div>'
                        + "<h1>" + inline(title) + "</h1>" + blocks(text)
                        + '<div class="footer"><span>16 October 2026 · Pre-sprint work · AI-assisted notes</span><span>' + n + " / 5</span></div></section>")
    document = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Reciprocal approval and bounded payment — five slides</title><style>' + STYLE + '</style><body><div class="toolbar"><span>Source-only skeleton. Results await explicit release. Expand speaker notes for evidence boundaries.</span><button onclick="window.print()">Print five-page PDF</button></div>' + "\n".join(sections) + "</body></html>\n"
    target = HERE / "index.html"
    target.write_text(document)
    return target


if __name__ == "__main__":
    print(build())
