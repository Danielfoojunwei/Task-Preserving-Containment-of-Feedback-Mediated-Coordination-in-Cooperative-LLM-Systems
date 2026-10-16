# Five-slide evidence breakdown

Open [index.html](index.html) for a self-contained presentation. Use arrow keys
or the navigation buttons; browser printing exposes all five slides.
[SLIDES.md](SLIDES.md) contains the detailed breakdown, speaker notes, sources,
uncertainty and scope limits.
[reciprocity_5_slides.pdf](reciprocity_5_slides.pdf) is the five-page export;
`preview/` contains all five rendered slide previews.

Rebuild with:

```bash
XDG_CACHE_HOME=/tmp/reciprocity-presentation-cache python presentations/reciprocity_20261016/build_presentation.py
```

The builder reads only complete released analysis/review outputs. It makes no
API calls, runs no new inference and preserves the historical presentation.
`BUILD_MANIFEST.json` hashes the evidence inputs, source and generated outputs.
The standalone defense figure is available as PNG and SVG.
Rebuilding requires Matplotlib, Playwright with `/usr/bin/chromium`, and PyMuPDF.
