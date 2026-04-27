import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

def generate_pdf_report(course, stats, insights, prediction):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=1, textColor=colors.HexColor('#009EDB'))
    story.append(Paragraph(f"Evaluation Report: {course.code} - {course.name}", title_style))
    story.append(Spacer(1, 0.15*inch))

    # Course info
    story.append(Paragraph(f"<b>Semester:</b> {course.semester} {course.academic_year}", styles['Normal']))
    story.append(Paragraph(f"<b>Lecturer:</b> {stats.get('lecturer', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"<b>Number of responses:</b> {stats['num_responses']}", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))

    # Overall statistics
    if stats['overall_mean'] is not None:
        story.append(Paragraph(f"<b>Overall mean:</b> {stats['overall_mean']:.2f} / 5.0", styles['Normal']))
        if 'college_mean' in stats and stats['college_mean'] is not None:
            story.append(Paragraph(f"<b>College mean:</b> {stats['college_mean']:.2f}", styles['Normal']))
        story.append(Spacer(1, 0.15*inch))

    # Key Insights
    story.append(Paragraph("<b>Key Insights</b>", styles['Heading2']))
    for line in insights:
        story.append(Paragraph(f"• {line}", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))

    # Section-wise table
    if stats['sections']:
        story.append(Paragraph("<b>Section Averages</b>", styles['Heading2']))
        data = [['Section', 'Mean', 'Std Dev']]
        for sec in stats['sections']:
            if sec['section_mean'] is not None:
                data.append([sec['title'][:50], f"{sec['section_mean']:.2f}", f"{sec['section_std']:.2f}" if sec['section_std'] else '-'])
        if len(data) > 1:
            table = Table(data, colWidths=[4*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#009EDB')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (1,1), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.15*inch))

    # Frequency distribution for first section Likert questions (as sample)
    if stats['sections'] and stats['sections'][0]['likert_questions']:
        story.append(Paragraph("<b>Frequency Distribution (first section)</b>", styles['Heading2']))
        qdata = [['Question', 'Mean', '1', '2', '3', '4', '5', 'Total']]
        for q in stats['sections'][0]['likert_questions']:
            freq = q['frequency']
            qdata.append([
                q['text'][:60],
                f"{q['mean']:.2f}" if q['mean'] is not None else '-',
                str(freq.get(1,0)), str(freq.get(2,0)), str(freq.get(3,0)), str(freq.get(4,0)), str(freq.get(5,0)),
                str(q['count'])
            ])
        table = Table(qdata, colWidths=[3.5*inch, 0.8*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.15*inch))

    # Prediction
    story.append(Paragraph("<b>Prediction</b>", styles['Heading2']))
    story.append(Paragraph(prediction, styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()