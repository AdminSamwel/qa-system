import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch

PURPLE  = colors.HexColor('#673ab7')
TEAL    = colors.HexColor('#009EDB')
GREEN   = colors.HexColor('#1e8e3e')
ORANGE  = colors.HexColor('#f57c00')
RED     = colors.HexColor('#d93025')
GREY    = colors.HexColor('#5f6368')
LIGHT   = colors.HexColor('#f8f9fa')


def _qei_colour(qei):
    if qei is None:
        return GREY
    if qei >= 0.80:
        return GREEN
    if qei >= 0.60:
        return TEAL
    if qei >= 0.40:
        return ORANGE
    return RED


def generate_pdf_report(course, stats, insights, prediction):
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                               topMargin=0.6*inch, bottomMargin=0.6*inch)
    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                 fontSize=18, alignment=1, textColor=PURPLE)
    h2_style    = ParagraphStyle('H2', parent=styles['Heading2'],
                                 fontSize=13, textColor=PURPLE, spaceAfter=4)
    normal      = styles['Normal']
    small       = ParagraphStyle('Small', parent=normal, fontSize=9, textColor=GREY)

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph(f"Evaluation Report: {course.code} — {course.name}", title_style))
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        f"<b>Semester:</b> {course.semester or '—'} {course.academic_year or ''} &nbsp;|&nbsp; "
        f"<b>Lecturer:</b> {stats.get('lecturer', 'N/A')} &nbsp;|&nbsp; "
        f"<b>Responses:</b> {stats['num_responses']}",
        normal
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=PURPLE,
                             spaceAfter=0.1*inch, spaceBefore=0.1*inch))

    # ── QEI Summary ───────────────────────────────────────────────────────────
    overall_qei  = stats.get('overall_qei')
    overall_mean = stats.get('overall_mean')
    qei_label    = stats.get('qei_label', '—')

    qei_data = [
        ['Overall Mean', 'QEI Score', 'QEI Status'],
        [
            f"{overall_mean:.2f} / 5.00" if overall_mean else '—',
            f"{overall_qei:.3f}"         if overall_qei  is not None else '—',
            qei_label,
        ]
    ]
    qei_table = Table(qei_data, colWidths=[2*inch, 2*inch, 2.5*inch])
    qei_table.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0), PURPLE),
        ('TEXTCOLOR',   (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
        ('GRID',        (0, 0), (-1, -1), 0.5, colors.grey),
        ('TEXTCOLOR',   (1, 1), (1, 1), _qei_colour(overall_qei)),
        ('FONTNAME',    (1, 1), (1, 1), 'Helvetica-Bold'),
        ('FONTSIZE',    (1, 1), (1, 1), 14),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT]),
    ]))
    story.append(qei_table)
    story.append(Spacer(1, 0.15*inch))

    # ── NACTVET Compliance ────────────────────────────────────────────────────
    nactvet = stats.get('nactvet_compliance')
    if nactvet:
        story.append(Paragraph("NACTVET Compliance (Section 3.5 Criteria)", h2_style))
        story.append(Paragraph(
            f"<b>{nactvet['met']}/{nactvet['total']}</b> criteria met — "
            f"<b>{nactvet['compliance_pct']}%</b> — <b>{nactvet['status']}</b>",
            normal
        ))
        story.append(Spacer(1, 0.06*inch))

        crit_data = [['Criterion', 'NAQS', 'QEI', 'Status']]
        for key, crit in nactvet['criteria'].items():
            qei_str = f"{crit['qei']:.2f}" if crit['qei'] is not None else '—'
            status  = 'Met' if crit['compliant'] else ('No Data' if crit['qei'] is None else 'Not Met')
            crit_data.append([crit['label'], crit['naqs'], qei_str, status])

        crit_table = Table(crit_data, colWidths=[2.8*inch, 1.4*inch, 0.8*inch, 1.2*inch])
        style_cmds = [
            ('BACKGROUND',  (0, 0), (-1, 0), PURPLE),
            ('TEXTCOLOR',   (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, 0), 9),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE',    (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ]
        for i, (key, crit) in enumerate(nactvet['criteria'].items(), start=1):
            col = GREEN if crit['compliant'] else (GREY if crit['qei'] is None else RED)
            style_cmds.append(('TEXTCOLOR', (3, i), (3, i), col))
            style_cmds.append(('FONTNAME',  (3, i), (3, i), 'Helvetica-Bold'))
        crit_table.setStyle(TableStyle(style_cmds))
        story.append(crit_table)
        story.append(Spacer(1, 0.15*inch))

    # ── Section Averages with QEI ─────────────────────────────────────────────
    if stats['sections']:
        story.append(Paragraph("Section QEI Breakdown", h2_style))
        data = [['Section', 'Mean', 'Ideal', 'QEI', 'Status']]
        for sec in stats['sections']:
            if sec['section_mean'] is not None:
                data.append([
                    sec['title'][:52],
                    f"{sec['section_mean']:.2f}",
                    f"{sec.get('ideal_score', 5.0):.1f}",
                    f"{sec['section_qei']:.2f}" if sec.get('section_qei') is not None else '—',
                    sec.get('qei_label', '—'),
                ])
        if len(data) > 1:
            table = Table(data, colWidths=[3.2*inch, 0.8*inch, 0.7*inch, 0.8*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND',  (0, 0), (-1, 0), PURPLE),
                ('TEXTCOLOR',   (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN',       (1, 0), (-1, -1), 'CENTER'),
                ('GRID',        (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE',    (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.15*inch))

    # ── Key Insights ──────────────────────────────────────────────────────────
    story.append(Paragraph("Key Insights", h2_style))
    for line in insights:
        story.append(Paragraph(f"• {line}", normal))
    story.append(Spacer(1, 0.1*inch))

    # ── Strengths / Weaknesses ────────────────────────────────────────────────
    strengths  = stats.get('strengths', [])
    weaknesses = stats.get('weaknesses', [])
    if strengths or weaknesses:
        sw_data = [['Strengths (mean ≥ 4.0)', 'Score', 'Areas for Improvement (mean ≤ 2.5)', 'Score']]
        max_rows = max(len(strengths), len(weaknesses))
        for i in range(max_rows):
            s = strengths[i]  if i < len(strengths)  else None
            w = weaknesses[i] if i < len(weaknesses) else None
            sw_data.append([
                s['text'][:45] if s else '',
                f"{s['mean']:.2f}" if s else '',
                w['text'][:45] if w else '',
                f"{w['mean']:.2f}" if w else '',
            ])
        sw_table = Table(sw_data, colWidths=[2.8*inch, 0.7*inch, 2.8*inch, 0.7*inch])
        sw_table.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (1, 0), GREEN),
            ('BACKGROUND',  (2, 0), (3, 0), RED),
            ('TEXTCOLOR',   (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE',    (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ]))
        story.append(sw_table)
        story.append(Spacer(1, 0.1*inch))

    # ── Prediction ────────────────────────────────────────────────────────────
    story.append(Paragraph("Prediction & Recommendation", h2_style))
    story.append(Paragraph(prediction, normal))
    story.append(Spacer(1, 0.1*inch))

    # ── QEI Scale Footer ──────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.5, color=GREY,
                             spaceAfter=0.06*inch, spaceBefore=0.06*inch))
    story.append(Paragraph(
        "<b>QEI Scale:</b> ≥0.80 Excellent | ≥0.60 Satisfactory (Compliant) | "
        "≥0.40 Needs Improvement | &lt;0.40 Unsatisfactory &nbsp;|&nbsp; "
        "QEI = Mean Score / Ideal Score (5.0) — NACTVET Standard",
        small
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
