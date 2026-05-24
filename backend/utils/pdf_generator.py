# utils/pdf_generator.py
"""
PDF report generator using ReportLab Platypus.
Fixes applied (v3):
- Footer uses plain ASCII to avoid black-square Unicode rendering
- _md_inline() applied to all plain-English bullet text
- "*(if any)*" stripped from headings
- Diagnosis extraction handles bullet-style "- **Condition:** ..." format
- Empty sections/headings suppressed
"""

from __future__ import annotations

import re
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
BRAND_BLUE   = colors.HexColor("#1E3A5F")
BRAND_ACCENT = colors.HexColor("#2E86AB")
SECTION_BG   = colors.HexColor("#F0F4F8")
RED_FLAG_BG  = colors.HexColor("#FFF0F0")
RED_FLAG_FG  = colors.HexColor("#C0392B")
PLAIN_BG     = colors.HexColor("#F0FFF4")
PLAIN_ACCENT = colors.HexColor("#27AE60")
TABLE_HEADER = colors.HexColor("#2E86AB")
TABLE_ALT    = colors.HexColor("#F7FAFC")
MUTED        = colors.HexColor("#718096")

# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _build_styles() -> dict:
    base = getSampleStyleSheet()

    def S(name, **kw) -> ParagraphStyle:
        parent = kw.pop("parent", "Normal")
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        "doc_title": S(
            "doc_title",
            fontSize=26, leading=32, textColor=BRAND_BLUE,
            alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=4,
        ),
        "doc_subtitle": S(
            "doc_subtitle",
            fontSize=11, textColor=MUTED,
            alignment=TA_CENTER, spaceAfter=20,
        ),
        "section_heading": S(
            "section_heading",
            fontSize=13, leading=18, textColor=BRAND_BLUE,
            fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4,
        ),
        "sub_heading": S(
            "sub_heading",
            fontSize=11, leading=15, textColor=BRAND_ACCENT,
            fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=3,
        ),
        "body": S(
            "body",
            fontSize=10, leading=15, alignment=TA_JUSTIFY, spaceAfter=4,
        ),
        "bullet": S(
            "bullet",
            fontSize=10, leading=14, leftIndent=16, spaceAfter=3,
            bulletIndent=6,
        ),
        "red_flag_text": S(
            "red_flag_text",
            fontSize=10, leading=14, textColor=RED_FLAG_FG,
            leftIndent=14, spaceAfter=3,
        ),
        "plain_heading": S(
            "plain_heading",
            fontSize=14, leading=20, textColor=PLAIN_ACCENT,
            fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=6,
            alignment=TA_CENTER,
        ),
        "plain_body": S(
            "plain_body",
            fontSize=10, leading=16, alignment=TA_JUSTIFY,
            spaceAfter=6, textColor=colors.HexColor("#2D3748"),
        ),
        "disclaimer": S(
            "disclaimer",
            fontSize=8, leading=12, textColor=MUTED,
            alignment=TA_CENTER, spaceBefore=10,
        ),
        "table_header_style": S(
            "table_header_style",
            fontSize=9, leading=12, textColor=colors.white,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
        ),
        "table_cell": S(
            "table_cell",
            fontSize=9, leading=12, textColor=colors.HexColor("#2D3748"),
        ),
    }


# ---------------------------------------------------------------------------
# Text sanitisation
# ---------------------------------------------------------------------------
_SUBSCRIPT_MAP  = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

_MEDICAL_SUB_PATTERNS = [
    ("SpO₂", "SpO<sub rise='1' size='7'>2</sub>"),
    ("SaO₂", "SaO<sub rise='1' size='7'>2</sub>"),
    ("FiO₂", "FiO<sub rise='1' size='7'>2</sub>"),
    ("CO₂",  "CO<sub rise='1' size='7'>2</sub>"),
    ("O₂",   "O<sub rise='1' size='7'>2</sub>"),
    ("H₂O",  "H<sub rise='1' size='7'>2</sub>O"),
    ("SpO2", "SpO<sub rise='1' size='7'>2</sub>"),
    ("SaO2", "SaO<sub rise='1' size='7'>2</sub>"),
    ("FiO2", "FiO<sub rise='1' size='7'>2</sub>"),
    ("CO2",  "CO<sub rise='1' size='7'>2</sub>"),
]

# All Unicode black/white square variants that render as boxes in some fonts
_BLACK_SQUARES = re.compile(r"[■□▪▫◾◽◼◻\u25A0-\u25FF]")


def _fix_text(text: str) -> str:
    """Sanitise a string for ReportLab Paragraph."""
    text = _BLACK_SQUARES.sub("", text)
    for raw, tagged in _MEDICAL_SUB_PATTERNS:
        text = text.replace(raw, tagged)
    text = text.translate(_SUBSCRIPT_MAP)
    text = text.translate(_SUPERSCRIPT_MAP)
    return text


def _md_inline(text: str) -> str:
    """Convert **bold** and *italic* Markdown to ReportLab XML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    return text


def _clean_heading(text: str) -> str:
    """Strip Markdown italic/bold decoration and *(if any)* from headings."""
    text = re.sub(r"\*\(if any\)\*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(if any\)",     "", text, flags=re.IGNORECASE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*",     r"\1", text)
    return text.strip()


def _para(text: str, style, fix: bool = True) -> Paragraph:
    if fix:
        text = _fix_text(text)
    return Paragraph(text, style)


# ---------------------------------------------------------------------------
# Markdown → ReportLab story parser
# ---------------------------------------------------------------------------

class _MarkdownToStory:
    def __init__(self, styles: dict):
        self.S = styles
        self.story: List = []
        self._table_rows: List[List[str]] = []
        self._in_table = False
        # Buffer pending heading until we know the section has content
        self._pending_heading: Optional[str] = None
        self._pending_heading_level: int = 0

    def _flush_pending_heading(self):
        """Emit the buffered heading now that we know content follows."""
        if self._pending_heading is None:
            return
        text = self._pending_heading
        level = self._pending_heading_level
        self._pending_heading = None
        self._pending_heading_level = 0

        if level == 2:
            self.story.append(Spacer(1, 6))
            self.story.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE))
            self.story.append(_para(text, self.S["section_heading"]))
        else:
            self.story.append(_para(text, self.S["sub_heading"]))

    def _flush_table(self):
        if not self._table_rows:
            return
        S = self.S
        rows = [r for r in self._table_rows
                if not all(re.fullmatch(r"-+:?|:?-+", c.strip()) for c in r)]
        if not rows:
            self._table_rows = []
            self._in_table = False
            return

        self._flush_pending_heading()

        header = rows[0]
        data   = rows[1:]
        available = A4[0] - 4 * cm
        n_cols = max(len(r) for r in rows)
        col_widths = [available / n_cols] * n_cols

        table_data = [[
            _para(_fix_text(_md_inline(h)), S["table_header_style"], fix=False)
            for h in header
        ]]
        for row in data:
            table_data.append([
                _para(_fix_text(_md_inline(c)), S["table_cell"], fix=False)
                for c in row
            ])

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), TABLE_HEADER),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUND", (0, 1), (-1, -1), [colors.white, TABLE_ALT]),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        self.story.append(Spacer(1, 4))
        self.story.append(tbl)
        self.story.append(Spacer(1, 8))
        self._table_rows = []
        self._in_table = False

    def _parse_table_row(self, line: str) -> List[str]:
        return [c.strip() for c in line.strip().strip("|").split("|")]

    def feed(self, markdown_text: str):
        S = self.S
        lines = markdown_text.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i]

            # Fenced code blocks
            if line.strip().startswith("```"):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    self._flush_pending_heading()
                    self.story.append(_para(lines[i], S["body"]))
                    i += 1
                i += 1
                continue

            # Pipe table
            if line.strip().startswith("|"):
                if not self._in_table:
                    self._in_table = True
                self._table_rows.append(self._parse_table_row(line))
                i += 1
                continue
            else:
                if self._in_table:
                    self._flush_table()

            stripped = line.strip()

            # H1 — skip (we draw our own title)
            if re.match(r"^#\s+(?!#)", stripped):
                i += 1
                continue

            # H2
            elif stripped.startswith("## "):
                # Buffer the heading; emit only when content follows
                self._pending_heading = _clean_heading(stripped[3:])
                self._pending_heading_level = 2

            # H3
            elif stripped.startswith("### "):
                self._pending_heading = _clean_heading(stripped[4:])
                self._pending_heading_level = 3

            # Advisory box
            elif stripped.startswith("⚠"):
                self._flush_pending_heading()
                box_text = _fix_text(_md_inline(stripped))
                self.story.append(Spacer(1, 4))
                self.story.append(Table(
                    [[_para(box_text, S["red_flag_text"], fix=False)]],
                    colWidths=[A4[0] - 4 * cm],
                    style=TableStyle([
                        ("BACKGROUND",    (0, 0), (-1, -1), RED_FLAG_BG),
                        ("BOX",           (0, 0), (-1, -1), 1, RED_FLAG_FG),
                        ("TOPPADDING",    (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                    ]),
                ))
                self.story.append(Spacer(1, 4))

            # Bullet / numbered items
            elif stripped.startswith("- ") or stripped.startswith("* "):
                self._flush_pending_heading()
                text = stripped[2:].strip()
                self.story.append(_para("• " + _fix_text(_md_inline(text)), S["bullet"], fix=False))

            elif re.match(r"^\d+\.\s", stripped):
                self._flush_pending_heading()
                text = re.sub(r"^\d+\.\s", "", stripped)
                self.story.append(_para("• " + _fix_text(_md_inline(text)), S["bullet"], fix=False))

            # Blank line
            elif stripped == "":
                self.story.append(Spacer(1, 4))

            # Plain paragraph
            else:
                self._flush_pending_heading()
                self.story.append(_para(_fix_text(_md_inline(stripped)), S["body"], fix=False))

            i += 1

        if self._in_table:
            self._flush_table()

        return self.story


# ---------------------------------------------------------------------------
# Plain-English section
# ---------------------------------------------------------------------------
def clean_text_for_pdf(text: str) -> str:
    """Replaces unmappable Unicode characters with standard ASCII equivalents."""
    replacements = {
        "–": "-",  # Replace en-dash with standard hyphen
        "—": "-",  # Replace em-dash with standard hyphen
        "‑": "-",  # Replace non-breaking hyphen (U+2011)
        "−": "-",  # Replace minus sign (U+2212)
        "‒": "-",  # Replace figure dash (U+2012)
        "―": "-",  # Replace horizontal bar (U+2015)
        "“": '"',  # Replace smart left quote with standard quote
        "”": '"',  # Replace smart right quote with standard quote
        "‘": "'",  # Replace smart left single quote
        "’": "'",  # Replace smart right single quote
        "•": "-",  # Replace standard bullet points with hyphens
        "…": "..."  # Replace ellipsis character with three dots
    }

    for fancy_char, standard_char in replacements.items():
        text = text.replace(fancy_char, standard_char)

    # Optional: Force encoding to drop any other unsupported characters safely
    # text = text.encode('latin-1', 'ignore').decode('latin-1')

    return text

def _extract_section(heading_pattern: str, text: str) -> str:
    m = re.search(
        rf"##\s+{heading_pattern}(.*?)(?=\n##\s|\Z)",
        text, re.IGNORECASE | re.DOTALL,
    )
    return m.group(1).strip() if m else ""


def _bullets_from(section_text: str) -> List[str]:
    items = re.findall(r"^[-*]\s+(.+)$", section_text, re.MULTILINE)
    # Strip any remaining **bold** markers from bullet text
    return [re.sub(r"\*\*(.+?)\*\*", r"\1", i).strip() for i in items if i.strip()]


def _plain_english_section(markdown_text: str, styles: dict) -> List:
    S = styles
    story: List = []

    story.append(PageBreak())

    banner = Table(
        [[_para("Understanding Your Report — In Plain Language", S["plain_heading"], fix=False)]],
        colWidths=[A4[0] - 4 * cm],
        style=TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), PLAIN_BG),
            ("BOX",           (0, 0), (-1, -1), 1.5, PLAIN_ACCENT),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]),
    )
    story.append(banner)
    story.append(Spacer(1, 10))
    story.append(_para(
        "This section explains your diagnostic report in everyday language. "
        "It is intended to help you understand what your results mean — "
        "<b>it does not replace the advice of a qualified doctor.</b>",
        S["plain_body"],
    ))
    story.append(Spacer(1, 8))

    # ── 1. What might be wrong ──────────────────────────────────────────────
    diagnosis_section = _extract_section(r"Probable Diagnosis", markdown_text)

    # Match "- **Condition:** ..." or "**Condition:** ..." or "Condition: ..."
    condition_m = re.search(
        r"(?:^[-*]\s+)?\*{0,2}Condition\*{0,2}[:\s]+(.+)",
        diagnosis_section, re.IGNORECASE | re.MULTILINE,
    )
    confidence_m = re.search(
        r"(?:^[-*]\s+)?\*{0,2}Confidence\*{0,2}[:\s]+([\d]+)",
        diagnosis_section, re.IGNORECASE | re.MULTILINE,
    )
    reasoning_m = re.search(
        r"(?:^[-*]\s+)?\*{0,2}Reasoning\*{0,2}[:\s]+(.+?)(?=\n[-*]|\n\*\*|\Z)",
        diagnosis_section, re.IGNORECASE | re.DOTALL,
    )

    if condition_m:
        story.append(_para("🔍 <b>What might be causing your symptoms?</b>", S["plain_body"]))
        cond = _fix_text(re.sub(r"\*\*(.+?)\*\*", r"\1", condition_m.group(1).strip()))
        conf = confidence_m.group(1).strip() if confidence_m else "?"
        story.append(_para(
            f"Based on your symptoms, the AI's best assessment is <b>{cond}</b> "
            "This is a preliminary finding — a doctor still "
            "needs to examine you and review any tests before a final diagnosis is made.",
            S["plain_body"],
        ))
        if reasoning_m:
            raw_reason = _fix_text(
                re.sub(r"\*\*(.+?)\*\*", r"\1",
                       reasoning_m.group(1).strip().split("\n")[0])
            )
            story.append(_para(f"<i>Why?</i> {raw_reason}", S["plain_body"]))
        story.append(Spacer(1, 8))

    # ── 2. Red flags ────────────────────────────────────────────────────────
    red_section = _extract_section(r"Red[‑\-]?Flag Alert", markdown_text)
    red_items   = _bullets_from(red_section)
    if red_items:
        story.append(_para("🚨 <b>Things to watch out for (Red Flags)</b>", S["plain_body"]))
        story.append(_para(
            "The following were noticed in your results that need prompt attention:",
            S["plain_body"],
        ))
        for item in red_items:
            story.append(_para("• " + _fix_text(item), S["plain_body"]))
        story.append(Spacer(1, 8))

    # ── 3. Tests ────────────────────────────────────────────────────────────
    # Required Investigations is a TABLE in the Markdown, not bullet list.
    # Extract test names from the table rows instead.
    inv_section = _extract_section(r"Required Investigations", markdown_text)
    # Pull first column of each non-header, non-separator table row
    table_rows = re.findall(r"^\|\s*([^|]+?)\s*\|", inv_section, re.MULTILINE)
    test_items = [
        r for r in table_rows
        if r.strip() and not re.fullmatch(r"[-: ]+", r) and r.lower() != "test"
    ]
    # Fallback: bullets (when LLM outputs a list instead of table)
    if not test_items:
        test_items = _bullets_from(inv_section)

    if test_items:
        story.append(_para("🧪 <b>Tests you may need</b>", S["plain_body"]))
        story.append(_para(
            "Your doctor may ask you to get the following tests done. "
            "Each test helps confirm or rule out possible causes:",
            S["plain_body"],
        ))
        for item in test_items[:8]:
            story.append(_para("• " + _fix_text(item), S["plain_body"]))
        if len(test_items) > 8:
            story.append(_para(
                f"  … and {len(test_items) - 8} more tests listed in the clinical section above.",
                S["plain_body"],
            ))
        story.append(Spacer(1, 8))

    # ── 4. Medications ──────────────────────────────────────────────────────
    med_section = _extract_section(r"Suggested Medications", markdown_text)
    med_items   = _bullets_from(med_section)
    # Drop the disclaimer bullet if present
    med_items = [m for m in med_items if "disclaimer" not in m.lower() and "physician" not in m.lower()]
    if med_items:
        story.append(_para("💊 <b>Possible treatments</b>", S["plain_body"]))
        story.append(_para(
            "These treatments may be considered by your doctor. "
            "<b>Do not take any medication without a doctor's prescription.</b>",
            S["plain_body"],
        ))
        for item in med_items[:6]:
            story.append(_para("• " + _fix_text(item), S["plain_body"]))
        story.append(Spacer(1, 8))

    # ── 5. Differentials ────────────────────────────────────────────────────
    diff_section = _extract_section(r"Differential Diagnoses", markdown_text)
    diff_items   = _bullets_from(diff_section)
    if diff_items:
        story.append(_para("🤔 <b>Other possibilities the doctor will consider</b>", S["plain_body"]))
        story.append(_para(
            "Medicine isn't always black and white. Here are other conditions "
            "that have similar symptoms and may be explored:",
            S["plain_body"],
        ))
        for item in diff_items[:5]:
            story.append(_para("• " + _fix_text(item), S["plain_body"]))
        story.append(Spacer(1, 8))

    # ── 6. What to do next ──────────────────────────────────────────────────
    story.append(_para("✅ <b>What should you do next?</b>", S["plain_body"]))
    story.append(_para(
        "1. Share this report with a qualified doctor as soon as possible. "
        "The AI has highlighted areas of concern but cannot replace a physical examination.<br/>"
        "2. Get the recommended tests done and bring the results to your appointment.<br/>"
        "3. If you experience worsening symptoms — especially difficulty breathing, "
        "severe pain, or high fever — go to an emergency room immediately.<br/>"
        "4. Do not self-medicate based on this report alone.",
        S["plain_body"],
    ))

    # Disclaimer
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    story.append(_para(
        "This plain-language summary is auto-generated for informational purposes only. "
        "It is not a substitute for professional medical advice, diagnosis, or treatment. "
        "Always seek the advice of a qualified healthcare provider with any questions "
        "you may have regarding a medical condition.",
        S["disclaimer"],
    ))

    return story


# ---------------------------------------------------------------------------
# Header / footer
# ---------------------------------------------------------------------------

def _make_header_footer(title: str = "ClinicaFlow - Diagnostic Summary Report"):
    def on_page(canvas, doc):
        canvas.saveState()
        w, h = A4

        # Header bar
        canvas.setFillColor(BRAND_BLUE)
        canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(1.5 * cm, h - 18, title)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - 1.5 * cm, h - 18, f"Page {doc.page}")

        # Footer bar — plain ASCII only (no Unicode in canvas text)
        canvas.setFillColor(SECTION_BG)
        canvas.rect(0, 0, w, 20, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica-Oblique", 7)
        canvas.drawCentredString(
            w / 2, 6,
            "[!] AI-generated report - for clinical reference only. "
            "A qualified physician must make all final decisions.",
        )

        canvas.restoreState()

    return on_page


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_pdf_report(
    markdown_text: str,
    filename: str = "generated_reports/diagnostic_report.pdf",
) -> Optional[str]:
    try:
        styles = _build_styles()

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            topMargin=2 * cm,
            bottomMargin=1.5 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
        )

        story: List = []

        story.append(Spacer(1, 8))
        story.append(_para("ClinicaFlow", styles["doc_title"]))
        story.append(_para("AI Diagnostic Summary Report", styles["doc_subtitle"]))
        story.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT))
        story.append(Spacer(1, 10))

        clean_markdown = clean_text_for_pdf(markdown_text)

        parser = _MarkdownToStory(styles)
        story.extend(parser.feed(clean_markdown))

        story.extend(_plain_english_section(clean_markdown, styles))

        doc.build(
            story,
            onFirstPage=_make_header_footer(),
            onLaterPages=_make_header_footer(),
        )

        print(f"--- PDF successfully generated: {filename} ---")
        return filename

    except Exception as exc:
        import traceback
        print(f"--- PDF generation error: {exc} ---")
        traceback.print_exc()
        return None