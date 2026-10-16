# Five-slide overt/covert study presentation

The original source-only skeleton was prepared on 16 October 2026 before
numerical release. The coordinator then explicitly released the sealed MAIN
results. The deck now contains all eight arms, all four primary tests and a
main-only figure. The final version adds all 20-source continuations and the complete secondary
execution review, with their distinct evidence and inference boundaries. All content is pre-sprint, AI-assisted material to verify.

[SLIDES.md](SLIDES.md) is the editable source; [index.html](index.html) is a
self-contained local viewer with optional speaker notes. Rebuild offline:

```sh
python presentations/overt_covert_20261016/build_slides.py
```

The standard-library viewer builder reads the adjacent Markdown and linked PNG
inside this directory, then writes the adjacent HTML with the PNG embedded.
It reads no study artifacts and makes no API/network calls.
[SLIDES.pdf](SLIDES.pdf) contains exactly five landscape pages. PDF-derived PNG
previews are in [previews](previews); [RENDER_MANIFEST.json](RENDER_MANIFEST.json)
records page dimensions, source and output hashes, browser/runtime versions and
layout checks. Rebuild with installed Chromium, Python Playwright and PyMuPDF:

```sh
python presentations/overt_covert_20261016/build_slides.py
python presentations/overt_covert_20261016/render_slides.py
```

The renderer reads only local HTML, blocks remote requests, preserves evidence
links and rejects non-five-page output, missing footers or overflow. Rebuild the
optional main figure only after an explicit numerical release:

```sh
MPLCONFIGDIR=/tmp/overt-covert-matplotlib python presentations/overt_covert_20261016/build_main_figure.py --release
python presentations/overt_covert_20261016/build_slides.py
```

That figure builder reads only the released main `ANALYSIS.json`, checks both
20-world arm denominators and the primary contrast, and records source/output
hashes in [MAIN_FIGURE_MANIFEST.json](MAIN_FIGURE_MANIFEST.json). It uses
Matplotlib and makes no API calls. M uses rounds 2–4; descriptive owner loss
uses all four rounds. The main study's full figure/replay build is separately
recorded under [the release directory](../../research/outputs/overt_covert_release_20261016/BUILD_MANIFEST.json).
