import io
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.inspection import Inspection

def generate_inspection_pdf(inspection: Inspection) -> bytes:
    """
    Generates an enterprise-grade PDF report for a single road inspection.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom color palette matching RoadGuard theme
    c_primary = colors.HexColor("#0B1120")
    c_accent = colors.HexColor("#0891B2")
    c_slate = colors.HexColor("#1E293B")
    c_text_dark = colors.HexColor("#0F172A")
    c_text_muted = colors.HexColor("#475569")
    c_border = colors.HexColor("#CBD5E1")
    
    severity_colors = {
        "HIGH": colors.HexColor("#DC2626"),
        "MEDIUM": colors.HexColor("#D97706"),
        "LOW": colors.HexColor("#059669"),
        "UNKNOWN": colors.HexColor("#64748B")
    }
    sev_color = severity_colors.get(inspection.effective_severity, colors.HexColor("#475569"))

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_accent
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_slate,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_text_dark
    )
    meta_label_style = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=c_text_muted
    )

    story = []

    # Header Banner
    header_data = [
        [
            Paragraph("<b>ROADGUARD AI</b>", title_style),
            Paragraph(f"<b>REPORT GENERATED:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ParagraphStyle('RightMeta', parent=body_style, alignment=2, textColor=c_text_muted))
        ],
        [
            Paragraph("Intelligent Road Damage Detection and Risk Mapping Platform", subtitle_style),
            Paragraph(f"<b>Inspection ID:</b> {inspection.id[:13]}...", ParagraphStyle('RightMeta2', parent=body_style, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[4.0 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=c_accent, spaceBefore=4, spaceAfter=14))

    # Inspection Overview Table
    story.append(Paragraph("1. Executive Inspection Summary", heading_style))
    summary_data = [
        [Paragraph("Inspection Title", meta_label_style), Paragraph(str(inspection.title), body_style)],
        [Paragraph("Original Filename", meta_label_style), Paragraph(str(inspection.original_filename), body_style)],
        [Paragraph("Capture Date / Created", meta_label_style), Paragraph(inspection.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), body_style)],
        [Paragraph("Effective Severity Tier", meta_label_style), Paragraph(f"<b><font color='{sev_color.hexval()}'>{inspection.effective_severity}</font></b> (AI Estimate: {inspection.ai_severity})", body_style)],
        [Paragraph("Verification Status", meta_label_style), Paragraph(f"<b>{inspection.status}</b>", body_style)],
        [Paragraph("Damage Instances Detected", meta_label_style), Paragraph(f"<b>{inspection.damage_count}</b> defect(s)", body_style)],
        [Paragraph("Severity Rationale", meta_label_style), Paragraph(str(inspection.severity_rationale or 'N/A'), body_style)],
        [Paragraph("Reviewer Notes", meta_label_style), Paragraph(str(inspection.reviewer_notes or 'No human reviewer notes recorded.'), body_style)]
    ]
    summary_table = Table(summary_data, colWidths=[2.2 * inch, 5.3 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # Geospatial Intelligence Table
    story.append(Paragraph("2. Geospatial & Location Intelligence", heading_style))
    coords_str = f"{inspection.latitude:.6f}, {inspection.longitude:.6f}" if (inspection.latitude and inspection.longitude) else "No GPS coordinates recorded (Unmapped)"
    geo_data = [
        [Paragraph("Location / Road Corridor", meta_label_style), Paragraph(str(inspection.location_name or 'Unspecified Location'), body_style)],
        [Paragraph("Geographic Coordinates (WGS84)", meta_label_style), Paragraph(coords_str, body_style)],
        [Paragraph("Coordinate Source", meta_label_style), Paragraph(f"<b>{inspection.location_source}</b>", body_style)]
    ]
    geo_table = Table(geo_data, colWidths=[2.2 * inch, 5.3 * inch])
    geo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(geo_table)
    story.append(Spacer(1, 14))

    # AI Model Telemetry
    story.append(Paragraph("3. AI Detection Telemetry", heading_style))
    model_data = [
        [Paragraph("Detection Engine", meta_label_style), Paragraph(str(inspection.model_identifier), body_style)],
        [Paragraph("Inference Duration", meta_label_style), Paragraph(f"{inspection.inference_ms:.1f} ms", body_style)],
        [Paragraph("Image Resolution", meta_label_style), Paragraph(f"{inspection.image_width} x {inspection.image_height} px ({inspection.file_size_bytes // 1024} KB)", body_style)]
    ]
    model_table = Table(model_data, colWidths=[2.2 * inch, 5.3 * inch])
    model_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(model_table)
    story.append(Spacer(1, 14))

    # Defects Breakdown Table
    story.append(Paragraph(f"4. Detected Surface Defect Manifest ({len(inspection.detections)} Total)", heading_style))
    if inspection.detections:
        defect_rows = [
            [
                Paragraph("<b>#</b>", meta_label_style),
                Paragraph("<b>Classification</b>", meta_label_style),
                Paragraph("<b>Confidence</b>", meta_label_style),
                Paragraph("<b>Surface Area %</b>", meta_label_style),
                Paragraph("<b>Norm. Bounding Box [x1, y1, x2, y2]</b>", meta_label_style)
            ]
        ]
        for idx, d in enumerate(inspection.detections, 1):
            bbox_str = f"[{d.x_min:.3f}, {d.y_min:.3f}, {d.x_max:.3f}, {d.y_max:.3f}]"
            defect_rows.append([
                Paragraph(str(idx), body_style),
                Paragraph(f"<b>{d.class_name}</b>", body_style),
                Paragraph(f"{d.confidence * 100:.1f}%", body_style),
                Paragraph(f"{d.area_ratio * 100:.2f}%", body_style),
                Paragraph(bbox_str, body_style)
            ])
        defect_table = Table(defect_rows, colWidths=[0.4 * inch, 2.1 * inch, 1.2 * inch, 1.2 * inch, 2.6 * inch])
        defect_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(defect_table)
    else:
        story.append(Paragraph("<i>No surface distress defects detected above confidence threshold.</i>", body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph("ROADGUARD AI Smart Infrastructure Intelligence System — Confidential Engineering Report", ParagraphStyle('Foot', parent=body_style, alignment=1, fontSize=8, textColor=c_text_muted)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_inspections_csv(inspections: List[Inspection]) -> str:
    """Generates CSV dataset of inspections."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Inspection ID",
        "Title",
        "Original Filename",
        "Created Date UTC",
        "AI Severity",
        "Manual Severity",
        "Effective Severity",
        "Status",
        "Damage Count",
        "Latitude",
        "Longitude",
        "Location Name",
        "Location Source",
        "Model Identifier",
        "Inference Duration (ms)",
        "Image Resolution",
        "Reviewer Notes"
    ])

    for ins in inspections:
        writer.writerow([
            ins.id,
            ins.title,
            ins.original_filename,
            ins.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ins.ai_severity,
            ins.manual_severity or "",
            ins.effective_severity,
            ins.status,
            ins.damage_count,
            ins.latitude if ins.latitude is not None else "",
            ins.longitude if ins.longitude is not None else "",
            ins.location_name or "",
            ins.location_source,
            ins.model_identifier,
            f"{ins.inference_ms:.2f}",
            f"{ins.image_width}x{ins.image_height}",
            ins.reviewer_notes or ""
        ])

    return output.getvalue()
