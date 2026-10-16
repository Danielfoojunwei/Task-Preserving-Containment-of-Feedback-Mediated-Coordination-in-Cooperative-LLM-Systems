# Five-slide overt/covert study presentation

The original source-only skeleton was prepared on 16 October 2026 before
numerical release. The coordinator then explicitly released the sealed MAIN
results. The deck now contains all eight arms, all four primary tests and a
main-only figure. Secondary execution and live continuation findings/witnesses
remain pending. All content is pre-sprint, AI-assisted material to verify.

[SLIDES.md](SLIDES.md) is the editable source; [index.html](index.html) is a
self-contained local viewer with optional speaker notes. Rebuild offline:

```sh
python presentations/overt_covert_20261016/build_slides.py
```

The standard-library viewer builder reads the adjacent Markdown and linked PNG
inside this directory, then writes the adjacent HTML with the PNG embedded.
It reads no study artifacts and makes no API/network calls.
Use the viewer's print button and a browser's PDF destination for five landscape
pages. Rebuild the main figure only after an explicit numerical release:

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
