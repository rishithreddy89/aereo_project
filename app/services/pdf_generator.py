import uuid
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER


def generate_certificate_pdf(
    file_path: Path,
    certificate_number: str,
    recipient_name: str,
    event_name: str,
    certificate_title: str,
    description: str,
    issue_date: str,
) -> None:
    """Render a certificate PDF to file_path using ReportLab."""
    width, height = landscape(A4)
    c = canvas.Canvas(str(file_path), pagesize=landscape(A4))

    # Background
    c.setFillColor(colors.HexColor("#FAFAFA"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Outer border
    c.setStrokeColor(colors.HexColor("#B8860B"))
    c.setLineWidth(6)
    c.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm, fill=0, stroke=1)

    # Inner border
    c.setLineWidth(2)
    c.rect(1.4 * cm, 1.4 * cm, width - 2.8 * cm, height - 2.8 * cm, fill=0, stroke=1)

    # Title
    c.setFont("Times-Bold", 36)
    c.setFillColor(colors.HexColor("#B8860B"))
    c.drawCentredString(width / 2, height - 4 * cm, certificate_title)

    # Subtitle line
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(width / 2, height - 5.2 * cm, "This is proudly presented to")

    # Recipient name — handle long names by scaling font
    name_font_size = 40 if len(recipient_name) <= 30 else max(24, 40 - (len(recipient_name) - 30))
    c.setFont("Times-BoldItalic", name_font_size)
    c.setFillColor(colors.HexColor("#1A1A2E"))
    c.drawCentredString(width / 2, height - 7 * cm, recipient_name)

    # Decorative line under name
    c.setStrokeColor(colors.HexColor("#B8860B"))
    c.setLineWidth(1.5)
    c.line(width / 2 - 8 * cm, height - 7.6 * cm, width / 2 + 8 * cm, height - 7.6 * cm)

    # Description — wrap long text
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#333333"))
    _draw_wrapped_text(c, description, width / 2, height - 9 * cm, width - 8 * cm, 13)

    # Event name
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(colors.HexColor("#1A1A2E"))
    c.drawCentredString(width / 2, height - 10.5 * cm, event_name)

    # Issue date
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(width / 2, height - 11.5 * cm, f"Date of Issue: {issue_date}")

    # Signature section
    sig_y = 3.5 * cm
    c.setStrokeColor(colors.HexColor("#333333"))
    c.setLineWidth(1)
    c.line(width / 2 - 5 * cm, sig_y, width / 2 + 5 * cm, sig_y)
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(width / 2, sig_y - 0.5 * cm, "Authorized Signature")

    # Certificate number (bottom left)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#999999"))
    c.drawString(1.8 * cm, 1.8 * cm, f"Certificate No: {certificate_number}")

    c.save()


def _draw_wrapped_text(c: canvas.Canvas, text: str, cx: float, y: float, max_width: float, font_size: int) -> None:
    """Draw centered, word-wrapped text."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if c.stringWidth(test, "Helvetica", font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_height = font_size * 1.4
    for i, line in enumerate(lines):
        c.drawCentredString(cx, y - i * line_height, line)
