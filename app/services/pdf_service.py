import io
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

logger = logging.getLogger(__name__)

# ── Color Palette ──────────────────────────────────────────────────────────
BLUE        = colors.HexColor('#2D6CDF')
BLUE_LIGHT  = colors.HexColor('#EBF4FF')
BLUE_MID    = colors.HexColor('#DBEAFE')
TEAL        = colors.HexColor('#0EA5E9')
GREEN       = colors.HexColor('#10B981')
GREEN_LIGHT = colors.HexColor('#ECFDF5')
RED         = colors.HexColor('#EF4444')
RED_LIGHT   = colors.HexColor('#FEF2F2')
ORANGE      = colors.HexColor('#F59E0B')
GRAY_900    = colors.HexColor('#111827')
GRAY_700    = colors.HexColor('#374151')
GRAY_500    = colors.HexColor('#6B7280')
GRAY_300    = colors.HexColor('#D1D5DB')
GRAY_100    = colors.HexColor('#F3F4F6')
WHITE       = colors.white

# ── Styles ─────────────────────────────────────────────────────────────────
def _styles():
    return {
        'h_white': ParagraphStyle('h_white', fontName='Helvetica-Bold', fontSize=18,
                                   textColor=WHITE, leading=22),
        'sub_white': ParagraphStyle('sub_white', fontName='Helvetica', fontSize=9,
                                     textColor=colors.HexColor('#CBD5E1'), leading=13),
        'section_title': ParagraphStyle('section_title', fontName='Helvetica-Bold', fontSize=10,
                                         textColor=BLUE, leading=14, spaceBefore=4),
        'label': ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=7,
                                 textColor=GRAY_500, leading=10, spaceAfter=1),
        'value': ParagraphStyle('value', fontName='Helvetica-Bold', fontSize=11,
                                 textColor=GRAY_900, leading=14),
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=9,
                                textColor=GRAY_700, leading=13),
        'body_bold': ParagraphStyle('body_bold', fontName='Helvetica-Bold', fontSize=9,
                                     textColor=GRAY_900, leading=13),
        'bullet': ParagraphStyle('bullet', fontName='Helvetica', fontSize=9,
                                  textColor=GRAY_700, leading=14, leftIndent=10),
        'checklist': ParagraphStyle('checklist', fontName='Helvetica', fontSize=9,
                                     textColor=colors.HexColor('#065F46'), leading=14, leftIndent=10),
        'disclaimer': ParagraphStyle('disclaimer', fontName='Helvetica', fontSize=8,
                                      textColor=GRAY_500, leading=11, alignment=TA_CENTER),
        'test_name': ParagraphStyle('test_name', fontName='Helvetica-Bold', fontSize=9,
                                     textColor=GRAY_900, leading=12),
        'test_cat': ParagraphStyle('test_cat', fontName='Helvetica', fontSize=8,
                                    textColor=GRAY_500, leading=11),
    }

# ── Watermark ──────────────────────────────────────────────────────────────
def _watermark(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica-Bold', 55)
    canvas_obj.setFillColor(colors.Color(0.18, 0.42, 0.87, alpha=0.04))
    canvas_obj.translate(A4[0] / 2, A4[1] / 2)
    canvas_obj.rotate(40)
    canvas_obj.drawCentredString(0, 0, "AMRUTHA AI")
    canvas_obj.restoreState()

# ── Card helper ────────────────────────────────────────────────────────────
def _card(content_rows, bg=None, border_color=None, col_widths=None):
    """Wrap content in a styled Table acting as a card."""
    bg = bg or GRAY_100
    border_color = border_color or GRAY_300
    col_widths = col_widths or [160 * mm]
    tbl = Table(content_rows, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 0.8, border_color),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return tbl

# ── Main PDF Generator ─────────────────────────────────────────────────────
class PDFService:
    def generate_report(
        self,
        patient_data: Dict[str, Any],
        medical_analysis: Dict[str, Any],
        appointment_details: Dict[str, Any],
    ) -> bytes:
        """
        Generate a premium A4 PDF report and return as bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        S = _styles()
        W = A4[0] - 30 * mm  # usable width
        story = []

        report_id = appointment_details.get('appointment_id', f'RPT-{uuid.uuid4().hex[:8].upper()}')
        gen_date  = datetime.now().strftime('%b %d, %Y')
        urgency   = appointment_details.get('urgency', medical_analysis.get('doctor_recommendation', {}).get('urgency', 'Moderate'))

        # ── HEADER GRADIENT BAND ──────────────────────────────────────────
        header_data = [[
            Paragraph('Appointment &amp; Health Summary<br/>'
                      f'<font size="9" color="#CBD5E1">Report ID: #{report_id} &nbsp;•&nbsp; {gen_date}</font>',
                      S['h_white']),
            Paragraph('Print / Download PDF', ParagraphStyle(
                'btn', fontName='Helvetica-Bold', fontSize=9,
                textColor=WHITE, alignment=TA_RIGHT
            )),
        ]]
        header_tbl = Table(header_data, colWidths=[W * 0.72, W * 0.28])
        header_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BLUE),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [8, 8, 0, 0]),
        ]))
        story.append(header_tbl)
        story.append(Spacer(1, 6))

        # ── SPECIALIST + APPOINTMENT CARDS (side by side) ─────────────────
        dr_rec      = medical_analysis.get('doctor_recommendation', {})
        doctor_name = (
            dr_rec.get('doctor_name') or
            appointment_details.get('doctor_name') or
            appointment_details.get('doctor_specialist', 'Dr. Amrutha AI')
        )
        specialist  = (
            dr_rec.get('doctor_expertise') or
            dr_rec.get('specialist_type') or
            appointment_details.get('doctor_specialist', 'General Physician')
        )
        appt_time   = (
            dr_rec.get('appointment_slot') or
            appointment_details.get('appointment_time', 'TBD')
        )

        # Parse date/time
        try:
            dt = datetime.strptime(appt_time, '%Y-%m-%d %H:%M')
            appt_date_str = dt.strftime('%b %d, %Y')
            appt_time_str = dt.strftime('%I:%M %p')
        except Exception:
            appt_date_str = appt_time
            appt_time_str = ''

        specialist_cell = [
            Paragraph('ASSIGNED SPECIALIST', S['label']),
            Spacer(1, 4),
            Paragraph(f'<b>{doctor_name}</b>', S['value']),
            Paragraph(f'<font color="#2D6CDF">{specialist}</font>', ParagraphStyle(
                'spec', fontName='Helvetica', fontSize=9, textColor=BLUE, leading=12)),
            Paragraph('MD, FACC • 10+ Years Exp.', S['body']),
        ]

        appt_cell = [
            Paragraph('APPOINTMENT TIME', S['label']),
            Spacer(1, 4),
            Paragraph(f'<b>{appt_date_str}</b>', S['value']),
            Paragraph(f'<b>{appt_time_str}</b>', ParagraphStyle(
                'time', fontName='Helvetica-Bold', fontSize=13, textColor=GRAY_900, leading=16)),
            Paragraph('<font color="#2D6CDF">📅 Add to Calendar</font>',
                      ParagraphStyle('cal', fontName='Helvetica', fontSize=8, textColor=BLUE, leading=11)),
        ]

        cards_data = [[
            Table([[item] for item in specialist_cell],
                  colWidths=[(W * 0.48)]),
            Table([[item] for item in appt_cell],
                  colWidths=[(W * 0.48)]),
        ]]
        cards_tbl = Table(cards_data, colWidths=[W * 0.50, W * 0.50])
        cards_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), WHITE),
            ('BACKGROUND', (1, 0), (1, 0), WHITE),
            ('BOX', (0, 0), (0, 0), 0.8, GRAY_300),
            ('BOX', (1, 0), (1, 0), 0.8, GRAY_300),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('COLUMNPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(cards_tbl)
        story.append(Spacer(1, 6))

        # ── PATIENT SUMMARY ROW ───────────────────────────────────────────
        p = patient_data
        pat_name   = p.get('name', 'N/A')
        pat_age    = p.get('age') or p.get('dob', 'N/A')
        pat_gender = p.get('gender', 'N/A')
        pat_blood  = p.get('blood_group', 'N/A')

        urgency_cell = ''
        if urgency == 'High':
            urgency_cell = Paragraph('⚠ HIGH URGENCY', ParagraphStyle(
                'urg', fontName='Helvetica-Bold', fontSize=8,
                textColor=RED, backColor=RED_LIGHT, leading=12,
                borderPadding=(3, 6, 3, 6), alignment=TA_RIGHT
            ))

        pat_row_data = [[
            Table([
                [Paragraph('PATIENT', S['label']),
                 Paragraph('AGE/SEX', S['label']),
                 Paragraph('BLOOD', S['label'])],
                [Paragraph(f'<b>{pat_name}</b>', S['value']),
                 Paragraph(f'<b>{pat_age} / {pat_gender}</b>', S['value']),
                 Paragraph(f'<b>{pat_blood}</b>', S['value'])],
            ], colWidths=[W * 0.28, W * 0.28, W * 0.22]),
            urgency_cell or Paragraph('', S['body']),
        ]]
        pat_tbl = Table(pat_row_data, colWidths=[W * 0.80, W * 0.20])
        pat_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), WHITE),
            ('BOX', (0, 0), (-1, -1), 0.8, GRAY_300),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(pat_tbl)
        story.append(Spacer(1, 6))

        # ── AI DIAGNOSTIC SUMMARY ─────────────────────────────────────────
        ai_diag = medical_analysis.get('ai_diagnostic_summary') or {}
        explanation   = ai_diag.get('explanation') or medical_analysis.get('patient_summary', '')
        conditions    = ai_diag.get('possible_conditions') or []
        risk_interp   = ai_diag.get('risk_interpretation') or medical_analysis.get('health_assessment', {}).get('current_condition', '')

        diag_content = [
            [Paragraph('✦ AI DIAGNOSTIC SUMMARY', S['section_title'])],
            [Spacer(1, 4)],
        ]
        if explanation:
            diag_content.append([Paragraph(f'"{explanation}"', ParagraphStyle(
                'quote', fontName='Helvetica-Oblique', fontSize=9,
                textColor=GRAY_700, leading=14))])
        if conditions:
            diag_content.append([Spacer(1, 4)])
            diag_content.append([Paragraph(
                '<b>Possible Conditions:</b> ' + ', '.join(conditions), S['body'])])
        if risk_interp:
            diag_content.append([Spacer(1, 4)])
            diag_content.append([Paragraph(f'<b>Risk Interpretation:</b> {risk_interp}', S['body'])])

        diag_tbl = _card(diag_content, bg=BLUE_LIGHT, border_color=BLUE_MID, col_widths=[W])
        story.append(diag_tbl)
        story.append(Spacer(1, 6))

        # ── BASIC TESTS + SAFETY (two columns) ───────────────────────────
        # Tests
        rec_tests = (
            medical_analysis.get('recommended_basic_tests') or
            _flatten_tests(medical_analysis.get('recommended_tests', {}))
        )

        test_rows = [[Paragraph('🔬 BASIC TESTS TO BE DONE', S['section_title'])], [Spacer(1, 4)]]
        if rec_tests:
            for t in rec_tests:
                name = t.get('test_name', str(t)) if isinstance(t, dict) else str(t)
                cat  = t.get('category', '') if isinstance(t, dict) else ''
                test_rows.append([Table([
                    [Paragraph(name, S['test_name']),
                     Paragraph(cat.upper(), ParagraphStyle(
                         'cat', fontName='Helvetica', fontSize=7,
                         textColor=GRAY_500, alignment=TA_RIGHT, leading=10))],
                    [HRFlowable(width='100%', thickness=0.5, color=GRAY_300), ''],
                ], colWidths=[W * 0.27, W * 0.17])])
        else:
            test_rows.append([Paragraph('No specific tests recommended.', S['body'])])

        tests_tbl = _card(test_rows, bg=WHITE, border_color=GRAY_300, col_widths=[W * 0.48])

        # Safety & Precautions
        precautions = (
            medical_analysis.get('safety_precautions') or
            medical_analysis.get('precautions') or []
        )
        lifestyle = medical_analysis.get('lifestyle_recommendations') or []

        safety_rows = [[Paragraph('🛡 SAFETY &amp; PRECAUTIONS', S['section_title'])], [Spacer(1, 4)]]
        for item in (precautions + lifestyle)[:6]:
            safety_rows.append([Paragraph(f'• {item}', S['bullet'])])
        if not precautions and not lifestyle:
            safety_rows.append([Paragraph('No specific precautions noted.', S['body'])])

        safety_tbl = _card(safety_rows, bg=WHITE, border_color=GRAY_300, col_widths=[W * 0.48])

        two_col = Table([[tests_tbl, safety_tbl]], colWidths=[W * 0.50, W * 0.50])
        two_col.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('COLUMNPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(two_col)
        story.append(Spacer(1, 6))

        # ── NEXT STEPS CHECKLIST ──────────────────────────────────────────
        checklist = (
            medical_analysis.get('next_steps_checklist') or
            medical_analysis.get('appointment_details', {}).get('preparation') or
            ['Complete blood work before appointment',
             'Share medical history with doctor',
             'Monitor symptoms and log daily']
        )

        checklist_rows = [
            [Paragraph('NEXT STEPS CHECKLIST', ParagraphStyle(
                'cl_title', fontName='Helvetica-Bold', fontSize=10,
                textColor=colors.HexColor('#065F46'), leading=14))],
            [Spacer(1, 4)],
        ]
        for item in checklist:
            checklist_rows.append([Paragraph(f'☐  {item}', S['checklist'])])

        checklist_tbl = _card(
            checklist_rows,
            bg=GREEN_LIGHT,
            border_color=colors.HexColor('#A7F3D0'),
            col_widths=[W]
        )
        story.append(checklist_tbl)
        story.append(Spacer(1, 10))

        # ── FOOTER DISCLAIMER ─────────────────────────────────────────────
        disclaimer = (
            medical_analysis.get('disclaimer') or
            'This is a digitally generated health summary for informational purposes. '
            'In case of emergency, please visit the nearest hospital.'
        )
        # Truncate very long disclaimers to fit PDF
        if len(disclaimer) > 300:
            disclaimer = disclaimer[:297] + '...'
        story.append(HRFlowable(width='100%', thickness=0.5, color=GRAY_300))
        story.append(Spacer(1, 4))
        story.append(Paragraph(disclaimer, S['disclaimer']))

        # ── BUILD ─────────────────────────────────────────────────────────
        doc.build(story, onFirstPage=_watermark, onLaterPages=_watermark)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        logger.info(f'Premium PDF generated, size={len(pdf_bytes)} bytes')
        return pdf_bytes


def _flatten_tests(rec_tests_dict: dict) -> list:
    """Flatten the nested recommended_tests dict into a flat list."""
    result = []
    for category_key, tests in rec_tests_dict.items():
        if isinstance(tests, list):
            for t in tests:
                if isinstance(t, dict):
                    result.append({
                        'test_name': t.get('test_name', ''),
                        'category': t.get('reason', category_key.replace('_', ' ').title()),
                    })
                else:
                    result.append({'test_name': str(t), 'category': ''})
    return result


# Singleton
pdf_service = PDFService()
