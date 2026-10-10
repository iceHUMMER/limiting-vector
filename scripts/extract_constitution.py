"""Extract the supplied Constitution DOCX into Markdown using only stdlib."""

import argparse
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources" / "Predelnyy_Vektor_Konstituciya_v1.1.docx"
TARGET = ROOT / "docs" / "constitution-v1.1.md"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{" + NS["w"] + "}"


def paragraph_text(paragraph):
    return "".join(node.text or "" for node in paragraph.iter(W + "t"))


def render():
    with ZipFile(SOURCE) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    body = document.find("w:body", NS)
    if body is None:
        raise ValueError("DOCX has no document body")
    lines = []
    for child in body:
        if child.tag == W + "p":
            text = paragraph_text(child)
            if not text:
                continue
            if not lines:
                text = "# " + text
            elif text.startswith(("Преамбула.", "Часть ", "Заключение.")):
                text = "## " + text
            elif re.match(r"^\d+(?:[а-я]|[–-]\d+)?\. ", text):
                text = "### " + text
            lines.append(text)
        elif child.tag == W + "tbl":
            # The supplied v1.1 has no tables. Do not silently lose new content.
            raise ValueError("Table found: review extraction before using a new source")
    if not lines:
        raise ValueError("DOCX contains no extracted text")
    return "\n\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without writing")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != expected:
            parser.exit(1, "Constitution Markdown differs from source; regenerate and review.\n")
        print("OK: Constitution Markdown matches DOCX extraction.")
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(expected, encoding="utf-8", newline="\n")
        print("Written: docs/constitution-v1.1.md")


if __name__ == "__main__":
    main()
