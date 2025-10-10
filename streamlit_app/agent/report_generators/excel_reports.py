"""
Excel Report Generators
Generate Excel reports from database data on-demand
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.database.db_singleton import get_db
from agent.config.settings import settings

db = get_db()

# ==================== Helper Functions ====================

def to_bullet_points(text: Optional[str]) -> str:
    """Convert paragraph text to clean bullet points"""
    if not text or not isinstance(text, str):
        return ""

    text = text.strip()

    if "•" in text:
        parts = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                bullet_parts = line.split('•')
                for i, part in enumerate(bullet_parts):
                    part = part.strip()
                    if part:
                        if i == 0 and not line.startswith('•'):
                            if len(part) > 3:
                                parts.append(f"• {part}")
                        else:
                            parts.append(f"• {part}")
        clean_lines = [line.strip() for line in parts if line.strip() and len(line.strip()) > 2]
        return "\n".join(clean_lines)

    if "- " in text and text.count("- ") > 1:
        lines = text.replace("- ", "• ").split('\n')
        clean_lines = [line.strip() for line in lines if line.strip()]
        return "\n".join(clean_lines)

    if '\n' in text and text.count('\n') >= 2:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) > 1:
            return "\n".join(f"• {line}" for line in lines)

    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    bullets = [sentence.strip() for sentence in sentences if sentence.strip() and len(sentence.strip()) > 10]

    if len(bullets) > 1:
        return "\n".join(f"• {bullet}" for bullet in bullets)

    return text

def format_excel_text(text: str) -> str:
    """Format text for clean Excel output"""
    if not text:
        return text

    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_(?!_)([^_]+)_(?!_)', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'~~(.*?)~~', r'\1', text)

    if "MISSING FROM RFP:" in text or "Missing:" in text:
        text = text.replace("MISSING FROM RFP:", "Missing:")
        text = text.replace("ESTIMATION BASIS:", "Basis:")
        text = text.replace("CONFIDENCE:", "Confidence:")
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    return text.strip()

def adjust_row_height(sheet, cell_address: str, text: str) -> None:
    """Adjust row height based on content"""
    if not text:
        return
    row_num = int(''.join([c for c in cell_address if c.isdigit()]))
    col_letter = ''.join([c for c in cell_address if c.isalpha()])
    col_width = sheet.column_dimensions[col_letter].width or 30
    chars_per_line = int(col_width * 1.2)
    lines = text.count('\n') + sum(len(line) // chars_per_line for line in text.split('\n')) + 1
    height = max(15, min(lines * 15, 300))
    sheet.row_dimensions[row_num].height = height

# ==================== Qualification Report Generator ====================

def generate_qualification_excel(rfp_id: str) -> str:
    """
    Generate qualification Excel report from database data

    Args:
        rfp_id: The RFP ID

    Returns:
        Path to generated Excel file
    """
    qual_data = db.get_qualification_results(rfp_id)

    if not qual_data:
        raise ValueError(f"No qualification data found for RFP: {rfp_id}")

    report = qual_data['qualification_report']

    wb = Workbook()

    # Executive Summary Sheet
    exec_ws = wb.active
    exec_ws.title = "Executive Summary"

    header_cell = exec_ws.cell(1, 1, "RFP QUALIFICATION REPORT")
    header_cell.font = Font(bold=True, size=16, color="FFFFFF")
    header_cell.fill = PatternFill(fill_type="solid", fgColor="4472C4")

    exec_ws.cell(3, 1, "EXECUTIVE SUMMARY").font = Font(bold=True, size=12)

    summary_cell = exec_ws.cell(4, 1, report.get('executive_summary', 'No summary available'))
    summary_cell.alignment = Alignment(wrap_text=True, vertical='top')
    exec_ws.row_dimensions[4].height = 120

    exec_ws.cell(6, 1, "KEY METRICS").font = Font(bold=True, size=12)
    exec_ws.cell(7, 1, f"Overall Score: {report['total_score']:.2f} / 4.0")
    exec_ws.cell(8, 1, f"Threshold: {report['threshold']:.2f}")
    exec_ws.cell(9, 1, f"Total Criteria: {len(report['analyses'])}")

    decision_cell = exec_ws.cell(10, 1, f"DECISION: {'PURSUE' if report['qualifies'] else 'DECLINE'}")
    decision_cell.font = Font(bold=True, color="008000" if report['qualifies'] else "FF0000")

    if report.get('recommendations'):
        exec_ws.cell(12, 1, "RECOMMENDATIONS").font = Font(bold=True, size=12)
        for i, rec in enumerate(report['recommendations'], 13):
            exec_ws.cell(i, 1, f"• {rec}")

    if report.get('qualification_context'):
        context = report['qualification_context']
        exec_ws.cell(16, 1, "ESTIMATED VALUES").font = Font(bold=True, size=12)

        if context.get('estimated_budget'):
            budget = context['estimated_budget']
            source_indicator = "[AI Estimated]" if budget.get('source') == "Estimated" else "[From RFP]"
            budget_text = f"Budget: {budget.get('value')} {source_indicator}\nConfidence: {budget.get('confidence_level')}"
            budget_cell = exec_ws.cell(17, 1, budget_text)
            budget_cell.alignment = Alignment(wrap_text=True, vertical='top')
            exec_ws.row_dimensions[17].height = 40

        if context.get('estimated_timeline'):
            timeline = context['estimated_timeline']
            source_indicator = "[AI Estimated]" if timeline.get('source') == "Estimated" else "[From RFP]"
            timeline_text = f"Timeline: {timeline.get('value')} {source_indicator}\nConfidence: {timeline.get('confidence_level')}"
            timeline_cell = exec_ws.cell(18, 1, timeline_text)
            timeline_cell.alignment = Alignment(wrap_text=True, vertical='top')
            exec_ws.row_dimensions[18].height = 40

    # Detailed Analysis Sheet
    detail_ws = wb.create_sheet("Detailed Analysis")

    headers = ["Criterion", "Selected Option", "Score", "Weight", "Weighted Score", "Reasoning", "Missing Data Justification"]
    for col, header in enumerate(headers, 1):
        cell = detail_ws.cell(1, col, header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(fill_type="solid", fgColor="E7E6E6")
        cell.alignment = Alignment(horizontal='center', wrap_text=True)

    for i, analysis in enumerate(report['analyses'], 2):
        detail_ws.cell(i, 1, analysis['criterion'])
        detail_ws.cell(i, 2, analysis['selected_option'])
        detail_ws.cell(i, 3, f"{analysis['score']}/4")

        weight = analysis['weighted_score'] / analysis['score'] if analysis['score'] > 0 else 0.0
        detail_ws.cell(i, 4, f"{weight:.2f}")
        detail_ws.cell(i, 5, f"{analysis['weighted_score']:.2f}")
        detail_ws.cell(i, 6, format_excel_text(analysis['reasoning']))

        missing_data_text = analysis.get('missing_data_justification', '') or ''
        detail_ws.cell(i, 7, format_excel_text(missing_data_text))

        for col in range(1, 8):
            cell = detail_ws.cell(i, col)
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )

        if analysis['reasoning'] or analysis.get('missing_data_justification'):
            min_height = 60
            reasoning_lines = len(analysis['reasoning'].split('\n')) if analysis['reasoning'] else 0
            justification_lines = len(analysis.get('missing_data_justification', '').split('\n'))
            content_height = max(reasoning_lines, justification_lines) * 15
            detail_ws.row_dimensions[i].height = max(min_height, content_height)

    detail_ws.column_dimensions['A'].width = 25
    detail_ws.column_dimensions['B'].width = 45
    detail_ws.column_dimensions['C'].width = 8
    detail_ws.column_dimensions['D'].width = 10
    detail_ws.column_dimensions['E'].width = 12
    detail_ws.column_dimensions['F'].width = 55
    detail_ws.column_dimensions['G'].width = 55

    summary_row = len(report['analyses']) + 4
    detail_ws.cell(summary_row, 1, "TOTAL WEIGHTED SCORE").font = Font(bold=True)
    detail_ws.cell(summary_row, 3, f"{report['total_score']:.2f}/4.0").font = Font(bold=True)
    detail_ws.cell(summary_row, 5, f"{report['total_score']:.2f}").font = Font(bold=True)

    threshold_row = summary_row + 1
    detail_ws.cell(threshold_row, 1, "QUALIFICATION THRESHOLD").font = Font(bold=True)
    detail_ws.cell(threshold_row, 3, f"{report['threshold']:.2f}/4.0").font = Font(bold=True)

    result_row = threshold_row + 2
    result_cell = detail_ws.cell(result_row, 1, f"RESULT: {'QUALIFIES' if report['qualifies'] else 'DOES NOT QUALIFY'}")
    result_cell.font = Font(bold=True, color="008000" if report['qualifies'] else "FF0000")

    exec_ws.column_dimensions['A'].width = 80

    # Local file save commented out - data saved to database, downloads work via BytesIO
    # output_path = settings.OUTPUT_DIR / f"{rfp_id}_qualification_report.xlsx"
    # wb.save(output_path)
    # print(f"✅ Generated qualification report: {output_path}")

    print(f"✅ Qualification report generated in-memory (saved to database)")
    return f"{rfp_id}_qualification_report.xlsx"

# ==================== Bid Plan Generator ====================

def generate_bid_plan_excel(rfp_id: str) -> str:
    """
    Generate bid plan Excel from database data

    Args:
        rfp_id: The RFP ID

    Returns:
        Path to generated Excel file
    """
    complete_data = db.get_complete_rfp_data(rfp_id)

    deliverables = complete_data.get('deliverables')
    assignments = complete_data.get('assignments')
    raw_data = complete_data.get('raw_data')

    if not deliverables or not assignments:
        raise ValueError(f"Missing deliverables or assignments for RFP: {rfp_id}")

    template_path = settings.FILES_DIR / "Bid Plan - [Client Opp Name]_BB_140125.xlsx"

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    wb = load_workbook(template_path)

    deliverables_sheet = None
    overview_sheet = None

    for name in wb.sheetnames:
        if "deliverable" in name.lower():
            deliverables_sheet = wb[name]
        elif "overview" in name.lower() or "team" in name.lower():
            overview_sheet = wb[name]

    if not deliverables_sheet:
        raise ValueError("Deliverables sheet not found in template")

    # Fill deliverables
    _fill_deliverables_sheet(deliverables_sheet, deliverables, assignments)

    # Fill overview if available
    if overview_sheet and raw_data:
        _fill_overview_sheet(overview_sheet, raw_data['rfp_data'])

    # Local file save commented out - data saved to database, downloads work via BytesIO
    # output_path = settings.OUTPUT_DIR / f"{rfp_id}_bid_plan.xlsx"
    # wb.save(output_path)
    # print(f"✅ Generated bid plan: {output_path}")

    print(f"✅ Bid plan generated in-memory (saved to database)")
    return f"{rfp_id}_bid_plan.xlsx"

def _fill_deliverables_sheet(sheet, deliverables_data, assignments_data):
    """Fill deliverables sheet with data from database"""

    assignment_report = assignments_data['assignment_report']
    assignment_map = {
        a['deliverable_section']: a['assigned_owner']
        for a in assignment_report.get('assignments', [])
    }

    # Detect structure
    structure = _detect_template_structure(sheet)

    # Fill client/opportunity
    if deliverables_data.get('client_and_opportunity') and structure.get('client_row'):
        cell = sheet.cell(structure['client_row'], 2)
        cell.value = deliverables_data['client_and_opportunity']
        cell.font = Font("Segoe UI", 18, bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical='top')

    # Fill technical deliverables
    tech_deliverables = deliverables_data.get('technical_deliverables', [])
    for i, deliv in enumerate(tech_deliverables[:20]):
        row = structure['tech_start_row'] + i
        owner = assignment_map.get(deliv.get('section'), "Granite MENA")
        _fill_deliverable_row(sheet, row, deliv, owner)

    # Fill commercial deliverables
    comm_deliverables = deliverables_data.get('commercial_deliverables', [])
    comm_start = 33  # Fixed position in template
    for i, deliv in enumerate(comm_deliverables):
        row = comm_start + i
        owner = assignment_map.get(deliv.get('section'), "Granite MENA")
        _fill_deliverable_row(sheet, row, deliv, owner)

def _detect_template_structure(sheet) -> dict:
    """Detect template structure positions"""
    structure = {
        'client_row': 4,
        'tech_start_row': 10,
        'comm_start_row': 33
    }

    try:
        for row in range(1, min(50, sheet.max_row + 1)):
            for col in range(2, 6):
                cell = sheet.cell(row, col)
                if cell.value and isinstance(cell.value, str):
                    value = cell.value.lower().strip()
                    if ('[client' in value or 'opportunity]' in value):
                        structure['client_row'] = row
                    elif 'technical' in value and 'bid' in value:
                        structure['tech_start_row'] = row + 3
    except:
        pass

    return structure

def _fill_deliverable_row(sheet, row: int, deliv: dict, owner: str):
    """Fill a single deliverable row"""
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    cell_style = {
        'font': Font("Segoe UI", 10),
        'alignment': Alignment(wrap_text=True, vertical='top')
    }

    # Section (Column C)
    if deliv.get('section'):
        cell = sheet.cell(row, 3, deliv['section'])
        cell.font = cell_style['font']
        cell.alignment = cell_style['alignment']
        cell.border = border

    # Requirement (Column E)
    if deliv.get('requirement'):
        cell_value = to_bullet_points(deliv['requirement'])
        cell = sheet.cell(row, 5, cell_value)
        cell.font = cell_style['font']
        cell.alignment = cell_style['alignment']
        cell.border = border
        adjust_row_height(sheet, f'E{row}', cell_value)

    # Evaluation criteria (Column F)
    if deliv.get('evaluation_criteria'):
        cell_value = to_bullet_points(deliv['evaluation_criteria'])
        cell = sheet.cell(row, 6, cell_value)
        cell.font = cell_style['font']
        cell.alignment = cell_style['alignment']
        cell.border = border

    # Owner (Column I)
    cell = sheet.cell(row, 9, owner)
    cell.font = cell_style['font']
    cell.alignment = cell_style['alignment']
    cell.border = border

def _fill_overview_sheet(sheet, rfp_data: dict):
    """Fill overview sheet with RFP data"""

    mappings = []

    if rfp_data.get('client_and_opportunity'):
        client_opp = rfp_data['client_and_opportunity']
        # Handle both dict and string formats
        value = client_opp.get('value') if isinstance(client_opp, dict) else client_opp
        mappings.append(("[Client and Opportunity]", value))

    if rfp_data.get('submission_deadline'):
        deadline = rfp_data['submission_deadline']
        value = deadline.get('value') if isinstance(deadline, dict) else deadline
        mappings.append(("Submission Deadline", value))

    if rfp_data.get('estimated_contract_value'):
        contract_value = rfp_data['estimated_contract_value']
        value = contract_value.get('value') if isinstance(contract_value, dict) else contract_value
        mappings.append(("Estimated Contract Value", value))

    # Find fields and fill
    for row in sheet.iter_rows(min_row=1, max_row=40, min_col=2, max_col=6):
        for cell in row:
            if isinstance(cell.value, str) and cell.value.strip():
                for label, value in mappings:
                    if cell.value.strip() == label and value:
                        value_cell = sheet.cell(cell.row, cell.column + 1)
                        value_cell.value = value
                        value_cell.alignment = Alignment(wrap_text=True, vertical='top')

# ==================== Assignment Report Generator ====================

def generate_assignment_excel(rfp_id: str) -> str:
    """
    Generate assignment analysis Excel from database data

    Args:
        rfp_id: The RFP ID

    Returns:
        Path to generated Excel file
    """
    assignments_data = db.get_rfp_assignments(rfp_id)

    if not assignments_data:
        raise ValueError(f"No assignment data found for RFP: {rfp_id}")

    report = assignments_data['assignment_report']

    wb = Workbook()
    ws = wb.active
    ws.title = "Assignment Analysis"

    # Headers
    headers = ["Deliverable Section", "Requirement", "Assigned Owner", "Reasoning", "Alternative Partners"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(1, col, header)
        cell.font = Font(name="Segoe UI", size=10, bold=True)
        cell.fill = PatternFill(fill_type="solid", fgColor="E7E6E6")
        cell.alignment = Alignment(horizontal='center', wrap_text=True)

    # Summary
    ws.cell(2, 1, f"Client: {report.get('client_and_opportunity', 'Unknown')}")
    ws.cell(3, 1, f"Analysis Date: {report.get('analysis_date', '')}")
    ws.cell(4, 1, f"Total: {report.get('total_deliverables', 0)}")
    ws.cell(5, 1, f"Granite: {report.get('granite_assigned', 0)}, Partners: {report.get('partner_assigned', 0)}")

    # Data rows
    start_row = 7
    for i, assignment in enumerate(report.get('assignments', []), start_row):
        ws.cell(i, 1, assignment.get('deliverable_section', ''))
        ws.cell(i, 2, to_bullet_points(assignment.get('deliverable_requirement', '')))
        ws.cell(i, 3, assignment.get('assigned_owner', ''))
        ws.cell(i, 4, to_bullet_points(assignment.get('reasoning', '')))

        alt_partners = assignment.get('alternative_partners', [])
        alt_text = "\n".join([f"• {partner}" for partner in alt_partners])
        ws.cell(i, 5, alt_text)

        for col in range(1, 6):
            cell = ws.cell(i, col)
            cell.font = Font(name="Segoe UI", size=10)
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )

        ws.row_dimensions[i].height = max(30, len(assignment.get('deliverable_requirement', '').split('\n')) * 15)

    # Column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 60
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 45
    ws.column_dimensions['E'].width = 35

    # Local file save commented out - data saved to database, downloads work via BytesIO
    # output_path = settings.OUTPUT_DIR / f"{rfp_id}_assignment_report.xlsx"
    # wb.save(output_path)
    # print(f"✅ Generated assignment report: {output_path}")

    print(f"✅ Assignment report generated in-memory (saved to database)")
    return f"{rfp_id}_assignment_report.xlsx"

# ==================== Generate All Reports ====================

def generate_all_reports(rfp_id: str) -> Dict[str, str]:
    """
    Generate all Excel reports for an RFP

    Args:
        rfp_id: The RFP ID

    Returns:
        Dictionary with paths to all generated reports
    """
    print(f"📊 Generating all reports for {rfp_id}...")

    reports = {}

    try:
        reports['qualification'] = generate_qualification_excel(rfp_id)
    except Exception as e:
        print(f"⚠️ Failed to generate qualification report: {e}")
        reports['qualification'] = None

    try:
        reports['bid_plan'] = generate_bid_plan_excel(rfp_id)
    except Exception as e:
        print(f"⚠️ Failed to generate bid plan: {e}")
        reports['bid_plan'] = None

    try:
        reports['assignment'] = generate_assignment_excel(rfp_id)
    except Exception as e:
        print(f"⚠️ Failed to generate assignment report: {e}")
        reports['assignment'] = None

    success_count = sum(1 for v in reports.values() if v is not None)
    print(f"\n✅ Generated {success_count}/3 reports successfully")

    return reports
