#!/usr/bin/env python3
"""Render the local, self-contained slide HTML to five PDF pages and previews.

Requires Chromium, Python Playwright and PyMuPDF. Does not read study data.
Run after build_slides.py: python3 render_slides.py
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import tempfile

import fitz
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
EXPECTED_PAGES = 5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = ROOT / "index.html"
    source_hash = sha256(source)
    executable = shutil.which("chromium") or shutil.which("chromium-browser")
    if executable is None:
        raise SystemExit("Chromium is required to render the slides.")

    with tempfile.TemporaryDirectory(prefix="overt-covert-render-") as scratch:
        temporary = Path(scratch)
        temporary_pdf = temporary / "SLIDES.pdf"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=executable,
                headless=True,
                timeout=20000,
                args=[
                    "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                    "--single-process", "--no-zygote", "--disable-software-rasterizer",
                    "--disable-background-networking", "--no-proxy-server",
                ],
            )
            chromium_version = browser.version
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            # Images are embedded by build_slides.py. Forbid remote requests.
            page.route("**/*", lambda route: route.abort())
            # Managed Chromium blocks file:// navigation; set_content is local.
            page.set_content(source.read_text(), wait_until="load", timeout=20000)
            page.emulate_media(media="print")
            page.evaluate("document.fonts.ready")
            layout = page.locator(".slide").evaluate_all("""slides => slides.map(s => {
                const r = s.getBoundingClientRect();
                const elements = [...s.querySelectorAll('*')].filter(e => e.checkVisibility());
                const bounds = elements.map(e => e.getBoundingClientRect());
                return {
                    title: s.querySelector('h1')?.textContent,
                    width_px: r.width, height_px: r.height,
                    content_bottom_px: Math.max(...bounds.map(b => b.bottom)) - r.top,
                    content_right_px: Math.max(...bounds.map(b => b.right)) - r.left,
                    links: [...s.querySelectorAll('a[href]')].filter(a => a.checkVisibility()).flatMap(a =>
                        [...a.getClientRects()].map(b => ({
                            uri: a.getAttribute('href'),
                            rect_px: [b.left-r.left, b.top-r.top, b.right-r.left, b.bottom-r.top]
                        }))),
                    images: [...s.querySelectorAll('img')].map(i => ({
                        loaded: i.complete && i.naturalWidth > 0,
                        width: i.naturalWidth, height: i.naturalHeight
                    }))
                };
            })""")
            if len(layout) != EXPECTED_PAGES:
                raise SystemExit(f"Expected five HTML slides; found {len(layout)}.")
            for number, slide in enumerate(layout, 1):
                if slide["content_bottom_px"] > slide["height_px"] + 1:
                    raise SystemExit(f"Slide {number} content extends below its page.")
                if slide["content_right_px"] > slide["width_px"] + 1:
                    raise SystemExit(f"Slide {number} content extends beyond its page width.")
                if not all(image["loaded"] for image in slide["images"]):
                    raise SystemExit(f"Slide {number} has an unloaded image.")
            page.pdf(path=str(temporary_pdf), print_background=True, prefer_css_page_size=True)
            browser.close()

        # set_content has no base URL. Restore each source anchor as a portable
        # PDF URI, keeping relative links relative to SLIDES.pdf beside index.html.
        with fitz.open(temporary_pdf) as document:
            if len(document) != EXPECTED_PAGES:
                raise SystemExit(f"Expected five PDF pages; found {len(document)}.")
            for number, pdf_page in enumerate(document):
                for link in layout[number]["links"]:
                    box = fitz.Rect([coordinate * .75 for coordinate in link["rect_px"]])
                    pdf_page.insert_link({"kind": fitz.LINK_URI, "from": box, "uri": link["uri"]})
            linked_pdf = temporary / "linked.pdf"
            document.save(linked_pdf, garbage=4, deflate=True)
        temporary_pdf = linked_pdf

        with fitz.open(temporary_pdf) as document:
            pages = []
            for number, pdf_page in enumerate(document, 1):
                rect = pdf_page.rect
                if abs(rect.width - 960) > 1 or abs(rect.height - 540) > 1:
                    raise SystemExit(f"Page {number} has unexpected dimensions: {rect}.")
                text = pdf_page.get_text()
                if f"{number} / {EXPECTED_PAGES}" not in text:
                    raise SystemExit(f"Page {number} is missing its expected footer.")
                preview = temporary / f"slide_{number}.png"
                pdf_page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(preview)
                pages.append({
                    "page": number, "width_pt": rect.width, "height_pt": rect.height,
                    "preview": f"previews/{preview.name}",
                    "preview_sha256": sha256(preview),
                    "preview_width_px": 1440, "preview_height_px": 810,
                    "text_characters": len(text), "source_link_count": len(pdf_page.get_links()),
                    "layout": layout[number - 1],
                })

        if sha256(source) != source_hash:
            raise SystemExit("index.html changed during rendering; rerun on the final source.")
        (ROOT / "previews").mkdir(exist_ok=True)
        shutil.copyfile(temporary_pdf, ROOT / "SLIDES.pdf")
        for number in range(1, EXPECTED_PAGES + 1):
            shutil.copyfile(temporary / f"slide_{number}.png", ROOT / "previews" / f"slide_{number}.png")
        manifest = {
            "schema_version": 1,
            "source": "index.html", "source_sha256": source_hash,
            "renderer": "render_slides.py", "renderer_sha256": sha256(Path(__file__)),
            "engine": {"chromium": chromium_version, "python": platform.python_version(),
                       "playwright": importlib.metadata.version("playwright"),
                       "pymupdf": fitz.VersionBind},
            "pdf": "SLIDES.pdf", "pdf_sha256": sha256(ROOT / "SLIDES.pdf"),
            "pdf_page_count": EXPECTED_PAGES, "pages": pages,
        }
        (ROOT / "RENDER_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Rendered {EXPECTED_PAGES} PDF pages and previews; source SHA-256 {source_hash}.")


if __name__ == "__main__":
    main()
