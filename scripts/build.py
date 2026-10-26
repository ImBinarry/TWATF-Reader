#!/usr/bin/env python3
"""Build static chapters and EPUB 3 downloads from the same repository sources.
Requires only Python 3.9+; no third-party packages or first EPUB files.
"""

import argparse
import copy
import datetime
import hashlib
import html
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EDITIONS = {"first": "First", "revised": "Revised"}
NS = "{http://www.w3.org/1999/xhtml}"
ALLOWED = {
    "body",
    "p",
    "br",
    "hr",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "em",
    "strong",
    "b",
    "i",
    "blockquote",
    "sup",
    "sub",
    "ul",
    "ol",
    "li",
    "span",
}
STYLE = "body{font-family:serif;line-height:1.6;margin:5%;}h1,h2{line-height:1.3;}p{margin:1em 0;}img{max-width:100%;} .cover{text-align:center;}"


def xml(value):
    return html.escape(str(value), quote=True)


def document(title, body):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en"><head><title>{xml(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head><body>{body}</body></html>'
    )


def read_chapters(root, edition):
    files = sorted((root / "chapters" / edition).glob("*.xhtml"))
    if not files:
        raise ValueError(f"No chapters found for {edition}")
    rows = []
    for path in files:
        if not re.fullmatch(r"\d{4,}\.xhtml", path.name):
            raise ValueError(f"Invalid chapter filename: {path}")
        number = int(path.stem)
        try:
            tree = ET.parse(path).getroot()
        except ET.ParseError as e:
            raise ValueError(f"{path}: invalid XHTML: {e}") from e
        title = tree.find(f"{NS}head/{NS}title")
        body = tree.find(f"{NS}body")
        if title is None or not (title.text or "").strip() or body is None:
            raise ValueError(f"{path}: title and body required")
        body = copy.deepcopy(body)
        # Whitespace after </body> belongs to the document, not the chapter fragment.
        body.tail = None
        for el in body.iter():
            el.tag = el.tag.removeprefix(NS)
            if el.tag not in ALLOWED or el.attrib:
                raise ValueError(
                    f"{path}: unsupported element/attributes: {el.tag} {el.attrib}"
                )
        if not "".join(body.itertext()).strip():
            raise ValueError(f"{path}: empty chapter")
        fragment = ET.tostring(body, encoding="unicode", method="xml")[6:-7]
        rows.append(
            {
                "number": number,
                "title": title.text.strip(),
                "html": fragment,
                "words": len(" ".join(body.itertext()).split()),
                "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    rows.sort(key=lambda c: c["number"])
    if [c["number"] for c in rows] != list(range(1, len(rows) + 1)):
        raise ValueError(
            f"{edition}: chapter numbers must be unique and contiguous from 1"
        )
    return rows


def build_epub(target, edition, rows, cover, modified):
    title = f"The World After the Fall — {EDITIONS[edition]}"
    identifier = f"urn:twatf:{edition}"
    items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="style" href="style.css" media-type="text/css"/>',
        '<item id="cover-image" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
    ]
    items += [
        f'<item id="c{c["number"]}" href="chapter-{c["number"]}.xhtml" media-type="application/xhtml+xml"/>'
        for c in rows
    ]
    spine = '<itemref idref="cover"/>' + "".join(
        f'<itemref idref="c{c["number"]}"/>' for c in rows
    )
    opf = f"""<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="en"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">{identifier}</dc:identifier><dc:title>{xml(title)}</dc:title><dc:creator>Sing Shong</dc:creator><dc:language>en</dc:language><dc:description>{xml(EDITIONS[edition])} edition, regenerated from the reader's current chapter sources.</dc:description><meta property="dcterms:modified">{modified}</meta><meta name="cover" content="cover-image"/></metadata><manifest>{''.join(items)}</manifest><spine toc="ncx">{spine}</spine></package>"""
    toc = "".join(
        f'<li><a href="chapter-{c["number"]}.xhtml">{xml(c["title"])}</a></li>'
        for c in rows
    )
    nav = document(
        "Contents",
        f'<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>{toc}</ol></nav>',
    )
    points = "".join(
        f'<navPoint id="c{c["number"]}" playOrder="{i+1}"><navLabel><text>{xml(c["title"])}</text></navLabel><content src="chapter-{c["number"]}.xhtml"/></navPoint>'
        for i, c in enumerate(rows)
    )
    ncx = f'<?xml version="1.0" encoding="utf-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{identifier}"/><meta name="dtb:depth" content="1"/><meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head><docTitle><text>{xml(title)}</text></docTitle><navMap>{points}</navMap></ncx>'
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        )
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/nav.xhtml", nav)
        z.writestr("OEBPS/toc.ncx", ncx)
        z.writestr("OEBPS/style.css", STYLE)
        z.write(cover, "OEBPS/cover.jpg")
        z.writestr(
            "OEBPS/cover.xhtml",
            document(
                title,
                '<div class="cover"><img src="cover.jpg" alt="Book cover"/></div>',
            ),
        )
        for c in rows:
            z.writestr(
                f'OEBPS/chapter-{c["number"]}.xhtml', document(c["title"], c["html"])
            )


def verify_epub(path, rows):
    with zipfile.ZipFile(path) as z:
        assert (
            z.infolist()[0].filename == "mimetype"
            and z.infolist()[0].compress_type == zipfile.ZIP_STORED
        )
        assert z.read("mimetype") == b"application/epub+zip"
        for name in z.namelist():
            if name.endswith((".xml", ".opf", ".ncx", ".xhtml")):
                ET.fromstring(z.read(name))
        opf = ET.fromstring(z.read("OEBPS/content.opf"))
        manifest = opf.find("{*}manifest")
        for item in manifest:
            assert "OEBPS/" + item.get("href") in z.namelist()
        spine = opf.find("{*}spine")
        assert len(spine) == len(rows) + 1
        for c in rows:
            actual = ET.fromstring(z.read(f'OEBPS/chapter-{c["number"]}.xhtml')).find(
                NS + "body"
            )
            expected = ET.fromstring("<body>" + c["html"] + "</body>")
            assert "".join(actual.itertext()) == "".join(
                expected.itertext()
            ), f'EPUB mismatch: {path} chapter {c["number"]}'


def build(root=ROOT):
    root = Path(root)
    books = {v: read_chapters(root, v) for v in EDITIONS}
    modified = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    # Stage and verify everything before replacing generated output.
    with tempfile.TemporaryDirectory(prefix=".build-", dir=root) as temporary:
        out = Path(temporary) / "dist"
        shutil.copytree(root / "website", out)
        catalog = {}
        for v, rows in books.items():
            folder = out / "data" / v
            folder.mkdir(parents=True, exist_ok=True)
            catalog[v] = []
            for c in rows:
                path = f'data/{v}/{c["number"]}.json'
                (out / path).write_text(
                    json.dumps(
                        {"title": c["title"], "html": c["html"]}, ensure_ascii=False
                    ),
                    encoding="utf-8",
                )
                catalog[v].append(
                    {k: c[k] for k in ["number", "title", "words"]} | {"path": path}
                )
            build_epub(
                out / "assets" / f"{v}.epub",
                v,
                rows,
                out / "assets" / f"{v}.jpg",
                modified,
            )
            verify_epub(out / "assets" / f"{v}.epub", rows)
        (out / "data/catalog.json").write_text(
            json.dumps(catalog, ensure_ascii=False), encoding="utf-8"
        )
        cards = "".join(
            f'<a class="chapter-card" href="index.html#read/revised/{c["number"]}"><small>CHAPTER {c["number"]}</small><h3>{xml(c["title"])}</h3></a>'
            for c in books["revised"]
        )
        for page in ["index.html", "chapters.html"]:
            p = out / page
            s = p.read_text(encoding="utf-8")
            assert "<!-- CHAPTER_CARDS -->" in s
            s = (
                s.replace("<!-- CHAPTER_CARDS -->", cards)
                .replace("{{FIRST_COUNT}}", str(len(books["first"])))
                .replace("{{REVISED_COUNT}}", str(len(books["revised"])))
            )
            p.write_text(s, encoding="utf-8")
        p = out / "info.html"
        s = (
            p.read_text(encoding="utf-8")
            .replace("{{FIRST_COUNT}}", str(len(books["first"])))
            .replace("{{REVISED_COUNT}}", str(len(books["revised"])))
        )
        p.write_text(s, encoding="utf-8")
        # Version dynamic cover URLs too, so replacing an image refreshes both pages.
        cover_hash = hashlib.sha256(
            b"".join((out / "assets" / f"{v}.jpg").read_bytes() for v in EDITIONS)
        ).hexdigest()[:12]
        app = out / "app.js"
        app.write_text(
            re.sub(
                r"(assets/\$\{(?:version|v)\}\.jpg)(?=`)",
                lambda m: m.group(1) + "?v=" + cover_hash,
                app.read_text(encoding="utf-8"),
            ),
            encoding="utf-8",
        )
        # Content hashes prevent stale scripts/styles and covers after a new static deployment.
        for page in out.glob("*.html"):
            markup = page.read_text(encoding="utf-8")

            def version_asset(match):
                name = match.group(2)
                digest = hashlib.sha256((out / name).read_bytes()).hexdigest()[:12]
                return match.group(1) + name + "?v=" + digest + '"'

            markup = re.sub(
                r'((?:src|href)=")((?:assets/)?[A-Za-z0-9_-]+\.(?:js|css|jpg))"',
                version_asset,
                markup,
            )
            page.write_text(markup, encoding="utf-8")
        (out / "build-manifest.json").write_text(
            json.dumps(
                {
                    "built_at": modified,
                    "chapters": {
                        v: {str(c["number"]): c["source_sha256"] for c in rows}
                        for v, rows in books.items()
                    },
                    "epubs": {
                        v: hashlib.sha256(
                            (out / "assets" / f"{v}.epub").read_bytes()
                        ).hexdigest()
                        for v in EDITIONS
                    },
                },
                indent=2,
            )
            + "\n"
        )
        destination = root / "dist"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(out, destination)
    print(
        "Built website and EPUBs: "
        + ", ".join(f"{v}: {len(rows)} chapters" for v, rows in books.items())
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    build(args.root)
