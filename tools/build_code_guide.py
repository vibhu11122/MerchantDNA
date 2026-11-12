"""Build docs/MerchantDNA_Code_Guide.pdf from the real source files + docs/code_guide/*.md.

Each annotation file looks like:

    source: merchantdna/sim/calendar.py
    sha1: 3f2a...            # of the source file when the notes were written
    title: Calendar
    mode: line              # "line" (every line explained) or "block"

    Free-text introduction until the first range heading.

    ### 1-3
    Explanation of lines 1-3.
    ### 4
    Explanation of line 4.

The builder refuses to run if a source file changed (sha1 mismatch) or if the ranges do
not cover every line exactly once, so the PDF can never silently drift from the code.

Usage: python tools/build_code_guide.py            # build
       python tools/build_code_guide.py --sha FILE # print the sha1 to paste into a note
"""
from __future__ import annotations

import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from fpdf import FPDF
from pygments import lex
from pygments.lexers import get_lexer_for_filename
from pygments.token import Comment, Keyword, Name, Number, Operator, String

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "docs" / "code_guide"
OUT = ROOT / "docs" / "MerchantDNA_Code_Guide.pdf"
FONTS = Path("/usr/share/fonts/truetype/dejavu")
CODE_WRAP = 108                       # characters per code line before wrapping
TOC_LINES_PER_PAGE = 46               # at 5.2 mm per line on A4 with our margins

TOKEN_COLOURS = {Keyword: (160, 30, 120), String: (0, 110, 60), Comment: (120, 120, 120),
                 Number: (30, 90, 170), Name.Function: (0, 70, 150), Name.Class: (0, 70, 150),
                 Name.Decorator: (120, 80, 0), Operator: (60, 60, 60)}


@dataclass
class Note:
    source: str
    sha1: str
    title: str
    mode: str
    intro: str
    sections: list[tuple[int, int, str]] = field(default_factory=list)   # (first, last, text)


# ----------------------------------------------------------------------------- parsing
def sha1_of(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:12]


def parse_note(path: Path) -> Note:
    """Read one annotation file into a Note."""
    text = path.read_text()
    header, _, body = text.partition("\n\n")
    meta = dict(re.match(r"(\w+):\s*(.*)", line).groups() for line in header.splitlines())   # type: ignore[union-attr]
    parts = re.split(r"^### (\d+)(?:-(\d+))?\s*$", body, flags=re.M)
    intro = parts[0].strip()
    sections = []
    for i in range(1, len(parts), 3):
        first, last, txt = int(parts[i]), int(parts[i + 1] or parts[i]), parts[i + 2].strip()
        sections.append((first, last, txt))
    return Note(meta["source"], meta["sha1"], meta["title"], meta.get("mode", "line"), intro, sections)


def validate(note: Note, n_lines: int, path: Path) -> None:
    """Hash must match and ranges must tile 1..n_lines exactly."""
    actual = sha1_of(path)
    if actual != note.sha1:
        sys.exit(f"{note.source}: source changed since notes were written (sha1 {actual}, notes say "
                 f"{note.sha1}). Re-check docs/code_guide and update the sha1.")
    expect = 1
    for first, last, _ in note.sections:
        if first != expect:
            sys.exit(f"{note.source}: notes jump from line {expect} to {first} (gap or overlap).")
        if last < first:
            sys.exit(f"{note.source}: bad range {first}-{last}.")
        expect = last + 1
    if expect != n_lines + 1:
        sys.exit(f"{note.source}: notes end at line {expect - 1}, file has {n_lines} lines.")


# ----------------------------------------------------------------------------- rendering
class Guide(FPDF):
    def __init__(self) -> None:
        super().__init__(format="A4")
        for family, style, file in [("Sans", "", "DejaVuSans.ttf"), ("Sans", "B", "DejaVuSans-Bold.ttf"),
                                    ("Sans", "I", "DejaVuSans-Oblique.ttf"), ("Mono", "", "DejaVuSansMono.ttf"),
                                    ("Mono", "B", "DejaVuSansMono-Bold.ttf")]:
            self.add_font(family, style, str(FONTS / file))
        self.set_auto_page_break(True, margin=14)
        self.set_margins(14, 14, 14)

    def footer(self) -> None:
        self.set_y(-10)
        self.set_font("Sans", "", 7.5)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, f"MerchantDNA code guide  ·  page {self.page_no()}", align="C")

    # ---- prose (tiny markdown: headings, bullets, code fences, bold)
    def prose(self, md: str, size: float = 9.5) -> None:
        in_code = False
        for raw in md.splitlines():
            if raw.strip().startswith("```"):
                in_code = not in_code
                self.ln(1)
                continue
            if in_code:
                self.set_font("Mono", "", 7.6); self.set_text_color(40, 40, 40)
                self.multi_cell(0, 3.9, raw.rstrip() or " ", new_x="LMARGIN", new_y="NEXT")
                continue
            line = raw.rstrip()
            if line.startswith("# "):
                self.ln(2); self.set_font("Sans", "B", 16); self.set_text_color(20, 20, 20)
                self.multi_cell(0, 8, line[2:], new_x="LMARGIN", new_y="NEXT"); self.ln(1)
            elif line.startswith("## "):
                self.ln(2); self.set_font("Sans", "B", 12.5); self.set_text_color(20, 20, 20)
                self.multi_cell(0, 6.5, line[3:], new_x="LMARGIN", new_y="NEXT")
            elif line.startswith("### "):
                self.ln(1); self.set_font("Sans", "B", 10.5); self.set_text_color(20, 20, 20)
                self.multi_cell(0, 5.5, line[4:], new_x="LMARGIN", new_y="NEXT")
            elif line.startswith("- "):
                self.set_font("Sans", "", size); self.set_text_color(30, 30, 30)
                self.set_x(18)
                self.multi_cell(0, 4.8, "•  " + self._inline(line[2:]), new_x="LMARGIN", new_y="NEXT", markdown=True)
            elif line:
                self.set_font("Sans", "", size); self.set_text_color(30, 30, 30)
                self.multi_cell(0, 4.8, self._inline(line), new_x="LMARGIN", new_y="NEXT", markdown=True)
            else:
                self.ln(2.2)

    @staticmethod
    def _inline(s: str) -> str:
        """fpdf markdown understands **bold**; render `code` as plain text."""
        return s.replace("`", "")

    # ---- code block with line numbers and token colours
    def code(self, lines: list[str], first: int, lexer) -> None:
        self.set_fill_color(246, 246, 248)
        for offset, line in enumerate(lines):
            n = first + offset
            pieces = self._wrap(line.rstrip("\n"))
            for k, piece in enumerate(pieces):
                if self.get_y() > self.h - 20:
                    self.add_page()
                self.set_font("Mono", "", 7.3)
                self.rect(self.l_margin, self.get_y(), self.w - self.l_margin - self.r_margin, 3.9, "F")
                self.set_text_color(150, 150, 150)
                self.cell(9, 3.9, f"{n:4d}" if k == 0 else "")
                for ttype, value in lex(piece, lexer):
                    colour = (30, 30, 30)
                    for t, c in TOKEN_COLOURS.items():
                        if ttype in t:
                            colour = c
                            break
                    self.set_text_color(*colour)
                    self.cell(self.get_string_width(value), 3.9, value.replace("\n", ""))
                self.cell(0, 3.9, "", new_x="LMARGIN", new_y="NEXT")
        self.ln(1.2)

    @staticmethod
    def _wrap(line: str) -> list[str]:
        if len(line) <= CODE_WRAP:
            return [line]
        out, indent = [], len(line) - len(line.lstrip()) + 8
        while len(line) > CODE_WRAP:
            out.append(line[:CODE_WRAP])
            line = " " * indent + line[CODE_WRAP:]
        return out + [line]

    def explanation(self, text: str, first: int, last: int) -> None:
        label = f"Line {first}" if first == last else f"Lines {first}-{last}"
        self.set_font("Sans", "B", 8.5); self.set_text_color(90, 60, 140)
        self.cell(0, 4.5, label, new_x="LMARGIN", new_y="NEXT")
        self.prose(text, size=9)
        self.ln(1.5)


def render_toc(pdf: Guide, outline) -> None:
    pdf.set_font("Sans", "B", 16); pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, "Contents", new_x="LMARGIN", new_y="NEXT")
    for sec in outline:
        indent = 4 * sec.level
        pdf.set_font("Sans", "B" if sec.level == 0 else "", 10 if sec.level == 0 else 9)
        pdf.set_x(14 + indent)
        txt = sec.name
        dots = "." * max(2, int((170 - indent - pdf.get_string_width(txt)) / pdf.get_string_width(".")) - 4)
        pdf.cell(0, 5.2, f"{txt} {dots} {sec.page_number}", new_x="LMARGIN", new_y="NEXT")


def build() -> None:
    notes = sorted(NOTES.glob("*.md"))
    if not notes:
        sys.exit("no notes in docs/code_guide")
    pdf = Guide()
    pdf.add_page()
    pdf.set_font("Sans", "B", 26); pdf.set_text_color(20, 20, 20)
    pdf.ln(60); pdf.cell(0, 14, "MerchantDNA", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Sans", "", 15)
    pdf.cell(0, 10, "A line-by-line guide to the code", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6); pdf.set_font("Sans", "", 10); pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 5.5, "Generated from the actual source files. Every annotation is checked against the "
                   "file it describes (content hash and complete line coverage), so what you read here is "
                   "what runs.", align="C")
    pdf.add_page()
    toc_pages = -(-(len(notes) + 2) // TOC_LINES_PER_PAGE)           # ceiling division
    pdf.insert_toc_placeholder(render_toc, pages=toc_pages)

    for path in notes:
        if path.name.startswith("00_"):                       # free prose chapters
            text = path.read_text()
            title = text.splitlines()[0].lstrip("# ").strip()
            pdf.add_page(); pdf.start_section(title, 0)
            pdf.prose(text)
            continue
        note = parse_note(path)
        src = ROOT / note.source
        lines = src.read_text().splitlines()
        validate(note, len(lines), src)
        lexer = get_lexer_for_filename(src.name) if src.suffix else get_lexer_for_filename("Makefile")
        pdf.add_page()
        pdf.start_section(f"{note.source}  —  {note.title}", 0)
        pdf.set_font("Sans", "B", 15); pdf.set_text_color(20, 20, 20)
        pdf.multi_cell(0, 7.5, note.title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Mono", "", 8.5); pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 5, f"{note.source}   ({len(lines)} lines, {note.mode} by {note.mode})", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.prose(note.intro)
        pdf.ln(2)
        for first, last, txt in note.sections:
            if pdf.get_y() > pdf.h - 40:
                pdf.add_page()
            pdf.code(lines[first - 1:last], first, lexer)
            pdf.explanation(txt, first, last)
    pdf.output(str(OUT))
    print(f"wrote {OUT.relative_to(ROOT)}  ({pdf.pages_count} pages, {len(notes)} chapters)")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--sha":
        print(sha1_of(ROOT / sys.argv[2]))
    else:
        build()
