from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer

FONT = "HeiseiKakuGo-W5"


def build_meal_card(title, sections, shopping=()):
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    body = ParagraphStyle("meal-body", fontName=FONT, fontSize=11, leading=17, wordWrap="CJK")
    heading = ParagraphStyle("meal-heading", parent=body, fontSize=15, leading=21, textColor=colors.HexColor("#27543C"))
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, title=title, leftMargin=45, rightMargin=45)
    story = [Paragraph(escape(title), heading), Spacer(1, 12)]
    for name, details in sections:
        lines = [Paragraph(escape(name), heading)]
        lines.extend(Paragraph(escape(str(line)), body) for line in details)
        story.extend([KeepTogether(lines), Spacer(1, 12)])
    if shopping:
        story.extend([
            Paragraph("買い物リスト", heading),
            Paragraph(escape("、".join(shopping)), body),
            Spacer(1, 12),
            Paragraph("買い物や調理が難しいときは、お住まいの市区町村の福祉窓口へ。", body),
        ])
    document.build(story)
    return output.getvalue()
