#!/usr/bin/env python3
"""
Convert a .docx into a draft essay page for the site.

Usage:
    python3 scripts/docx_to_essay.py "~/Downloads/My Essay.docx" my-essay-slug

Writes essays/<slug>.html, wrapped in the site's nav/footer, with Word's
formatting cruft stripped out. Any hyperlinks found in the docx are listed
in a comment at the top of the file (text -> URL) since Word doesn't export
them as visible links in the raw HTML -- wire them into <a> tags by hand.

Still needs a human pass after: set the real <h1> title and .meta line,
turn cited sources into links using the mapping comment, and proofread.
"""

import html
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent.parent


def convert_to_raw_html(docx_path: Path, tmp_dir: Path) -> str:
    out_path = tmp_dir / "raw.html"
    subprocess.run(
        ["textutil", "-convert", "html", str(docx_path), "-output", str(out_path)],
        check=True,
    )
    return out_path.read_text(encoding="utf-8")


def extract_hyperlinks(docx_path: Path, tmp_dir: Path) -> list[tuple[str, str]]:
    unzip_dir = tmp_dir / "unzipped"
    with zipfile.ZipFile(docx_path) as zf:
        zf.extractall(unzip_dir)

    rels_path = unzip_dir / "word" / "_rels" / "document.xml.rels"
    doc_path = unzip_dir / "word" / "document.xml"
    if not rels_path.exists() or not doc_path.exists():
        return []

    rels_xml = rels_path.read_text(encoding="utf-8")
    rid_to_url = dict(
        re.findall(
            r'Id="(rId\d+)"[^>]*Target="([^"]+)"[^>]*TargetMode="External"',
            rels_xml,
        )
    )

    doc_xml = doc_path.read_text(encoding="utf-8")
    links = []
    for m in re.finditer(
        r'<w:hyperlink[^>]*r:id="(rId\d+)"[^>]*>(.*?)</w:hyperlink>', doc_xml, re.S
    ):
        rid, inner = m.group(1), m.group(2)
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", inner))
        url = rid_to_url.get(rid)
        if text and url:
            links.append((html.unescape(text), url))
    return links


def clean_body(raw_html: str) -> str:
    body_match = re.search(r"<body>(.*)</body>", raw_html, re.S)
    body = body_match.group(1) if body_match else raw_html

    # Drop empty spacer paragraphs Word/textutil inserts (<p ...><br></p>)
    body = re.sub(r"<p[^>]*>\s*<br\s*/?>\s*</p>", "", body)

    # Unwrap <span ...>text</span> to plain text (styling doesn't carry over)
    body = re.sub(r"<span[^>]*>(.*?)</span>", r"\1", body, flags=re.S)

    # Word's italics/bold -> semantic tags; strip class/style attrs everywhere
    body = body.replace("<i>", "<em>").replace("</i>", "</em>")
    body = body.replace("<b>", "<strong>").replace("</b>", "</strong>")
    body = re.sub(r"<(p|li|ul|ol)\s+[^>]*>", r"<\1>", body)

    # Collapse runs of blank lines left behind after stripping spacer paragraphs
    body = re.sub(r"\n\s*\n+", "\n\n", body)

    return body.strip()


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TITLE HERE — Caroline Mahony</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>

  <nav>
    <a href="../index.html">Home</a>
    <a href="../projects.html">Projects</a>
    <a href="../writing.html" aria-current="page">Writing</a>
    <a href="../reading.html">Reading</a>
  </nav>

  <main>
    <h1>TITLE HERE</h1>
    <p class="meta">YEAR &middot; LABEL HERE</p>
{links_comment}
{body}

  </main>

  <footer>
    &copy; 2026 Caroline Mahony
  </footer>

</body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/docx_to_essay.py <path-to-docx> <slug>")
        sys.exit(1)

    docx_path = Path(sys.argv[1]).expanduser().resolve()
    slug = sys.argv[2]

    if not docx_path.exists():
        print(f"File not found: {docx_path}")
        sys.exit(1)
    if not shutil.which("textutil"):
        print("textutil not found — this script requires macOS.")
        sys.exit(1)

    out_path = SITE_ROOT / "essays" / f"{slug}.html"
    if out_path.exists():
        print(f"Refusing to overwrite existing file: {out_path}")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        raw_html = convert_to_raw_html(docx_path, tmp_dir)
        body = clean_body(raw_html)
        links = extract_hyperlinks(docx_path, tmp_dir)

    if links:
        lines = "\n".join(f"       {text} -> {url}" for text, url in links)
        links_comment = f"    <!-- Links found in the docx, wire these into <a> tags by hand:\n{lines}\n    -->\n"
    else:
        links_comment = ""

    out_path.write_text(
        TEMPLATE.format(links_comment=links_comment, body=body), encoding="utf-8"
    )
    print(f"Wrote {out_path}")
    print("Still to do by hand: set the real title/meta line, wire up citation")
    print("links from the comment block, and proofread against the original.")


if __name__ == "__main__":
    main()
