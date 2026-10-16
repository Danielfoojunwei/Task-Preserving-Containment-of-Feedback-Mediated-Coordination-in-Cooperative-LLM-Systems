# Local working-report PDF renderer

`render_report.py` reads the adjacent `REPORT.md` and uses installed ReportLab
and embedded DejaVu fonts. It makes no network or model calls and does not edit
the report, results, reviews or source figures. The PDF is an AI-assisted,
pre-sprint research working report; this renderer does not implement or claim
the official Apart submission template or add authors.

The coordinator must first replace all final report result markers and explicitly
release rendering. Without `--release`, or while an HTML comment/result marker
remains, it refuses to create a PDF. Output creation is exclusive: choose a new
filename for each revision.

```sh
python research/outputs/overt_covert_release_20261016/render_report.py \
  --release \
  --output research/outputs/overt_covert_release_20261016/REPORT_WORKING_v1.pdf
```

It supports headings and PDF bookmarks, paragraphs, inline bold/italic/code,
clickable links, pipe tables with repeated headers, fenced code, lists,
blockquotes and local Markdown PNG/JPEG images. `--figure /absolute/image.png`
can append figures in the supplied order; add captions in `REPORT.md` when
captions are required. External images and implicit SVG/PDF conversion are
rejected. `--body-size` accepts 9–12 point body text (default 10.2); the renderer
never drops text or automatically shrinks it to meet a page limit.

Successful rendering prints a JSON receipt with page count, source/PDF hashes,
block counts, appended-figure hashes and configuration. Inspect the resulting
pages visually before sharing. This receipt is provenance, not validation of
the research claims or semantic completeness of Markdown-to-PDF extraction.
