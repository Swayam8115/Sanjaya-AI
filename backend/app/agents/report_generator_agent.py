import os
import uuid
from typing import Dict, Any

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.units import cm

from .base_agent import BaseAgent


class ReportGeneratorAgent(BaseAgent):

    async def run(self, query: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:

        context = context or {}

        filename = f"report_{uuid.uuid4().hex}.pdf"
        path = f"./generated_reports/{filename}"
        os.makedirs("./generated_reports", exist_ok=True)

        # FIX: proper margins so table never cuts off
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )

        styles = getSampleStyleSheet()
        elements = []

        # ==========================
        # EXEC SUMMARY
        # ==========================
        elements.append(Paragraph("Executive Summary", styles["Title"]))
        elements.append(Paragraph(context.get("summary", ""), styles["BodyText"]))
        elements.append(Spacer(1, 16))

        # ==========================
        # TABLES (FULLY FIXED)
        # ==========================
        for tbl in context.get("tables", []):
            title = tbl.get("title", "")
            columns = tbl.get("columns", [])
            rows = tbl.get("rows", [])

            # Wrap columns + rows
            header = [Paragraph(str(c), styles["Heading4"]) for c in columns]

            wrapped_rows = []
            for row in rows:
                wrapped_rows.append([Paragraph(str(cell), styles["BodyText"]) for cell in row])

            data = [header] + wrapped_rows

            # FIX: auto column width (prevents overflow)
            usable_width = A4[0] - doc.leftMargin - doc.rightMargin
            col_width = usable_width / len(columns)
            col_widths = [col_width] * len(columns)

            table = Table(data, colWidths=col_widths)

            # FIX: VALID table styling (no errors + ey-friendly)
            table_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f4f4f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),

                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),

                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),

                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),

                # FIX: Proper alternating colors (VALID syntax)
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.whitesmoke, colors.lightgrey]),
            ])

            table.setStyle(table_style)

            elements.append(Paragraph(title, styles["Heading2"]))
            elements.append(table)
            elements.append(Spacer(1, 20))

        # ==========================
        # CHARTS
        # ==========================
        for chart in context.get("charts", []):
            drawing = Drawing(420, 220)
            bc = VerticalBarChart()

            bc.data = [chart.get("values", [])]
            bc.categoryAxis.categoryNames = chart.get("labels", [])
            bc.width = 380
            bc.height = 180
            bc.strokeColor = colors.black
            bc.barSpacing = 2

            drawing.add(bc)

            elements.append(Paragraph(chart["title"], styles["Heading2"]))
            elements.append(drawing)
            elements.append(Spacer(1, 20))

        # Build PDF
        doc.build(elements)

        return {
            "agent": "ReportGeneratorAgent",
            "output": {"file_path": path}
        }
