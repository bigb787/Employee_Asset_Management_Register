"""PDF generation for gatepass and IT exit clearance."""
from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

SYSTEM_ROWS = [
    ("Email Groups", "email_groups"),
    ("Infodesk QA/Dev", "infodesk_qa_dev"),
    ("Infodesk Prod", "infodesk_prod"),
    ("JIRA and Wiki", "jira_and_wiki"),
    ("MS Office", "ms_office"),
    ("Mongo Access", "mongo_access"),
    ("Azure Infodesk", "azure_infodesk"),
    ("Azure WN InfoDesk", "azure_wn_infodesk"),
    ("VPN", "vpn"),
    ("WN VPN", "wn_vpn"),
    ("Azure Devops", "azure_devops"),
    ("InfoAdmin", "info_admin"),
    ("Zabbix", "zabbix"),
    ("GitHub", "github"),
    ("InfoDesk Portal", "infodesk_portal"),
    ("Salesforce", "salesforce"),
]


def _parse_items(raw: Optional[str]) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return [{"description": str(raw), "unit": "", "qty": "", "remarks": ""}]
    if not isinstance(data, list):
        return [{"description": str(data), "unit": "", "qty": "", "remarks": ""}]
    out = []
    for it in data:
        if isinstance(it, dict):
            out.append(
                {
                    "description": it.get("description") or it.get("Description") or "",
                    "unit": it.get("unit") or it.get("Unit") or "",
                    "qty": it.get("qty") or it.get("Qty") or "",
                    "remarks": it.get("remarks") or it.get("Remarks") or "",
                }
            )
        else:
            out.append({"description": str(it), "unit": "", "qty": "", "remarks": ""})
    return out


def generate_gatepass_pdf(data: dict[str, Any]) -> bytes:
    buf = BytesIO()
    w, h = A5
    c = canvas.Canvas(buf, pagesize=A5)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(w / 2, h - 20 * mm, "InfoDesk India Private Limited")
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, h - 26 * mm, "12B Nutan Bharat Alkapuri, Vadodara")
    c.drawCentredString(w / 2, h - 31 * mm, "390007 Gujarat, India")

    box_y = h - 48 * mm
    c.setLineWidth(1)
    c.rect(w / 2 - 35 * mm, box_y, 70 * mm, 12 * mm)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, box_y + 3.5 * mm, "GATE PASS")

    c.setFont("Helvetica-Bold", 10)
    pt = str(data.get("pass_type") or "")
    c.drawCentredString(w / 2, box_y - 8 * mm, pt)

    y = box_y - 22 * mm
    c.setFont("Helvetica", 9)
    c.drawString(15 * mm, y, f"Issued to: {data.get('issued_to') or ''}")
    c.drawString(w / 2 - 5 * mm, y, f"Person: {data.get('person') or ''}")
    y -= 6 * mm
    c.drawString(15 * mm, y, f"No: {data.get('gatepass_no') or ''}")
    c.drawString(w / 2 - 5 * mm, y, f"Date: {data.get('gatepass_date') or ''}")
    y -= 6 * mm
    pass_type = str(data.get("pass_type") or "")
    if pass_type in ("Returnable", "Temporary"):
        c.drawString(
            15 * mm,
            y,
            f"Expected Return: {data.get('expected_return_date') or ''}",
        )

    items = _parse_items(data.get("asset_items"))
    rows = [["Sr.No", "Description", "Unit", "Qty", "Remarks"]]
    for i in range(6):
        if i < len(items):
            it = items[i]
            rows.append(
                [
                    str(i + 1),
                    str(it.get("description") or ""),
                    str(it.get("unit") or ""),
                    str(it.get("qty") or ""),
                    str(it.get("remarks") or ""),
                ]
            )
        else:
            rows.append([str(i + 1), "", "", "", ""])

    t = Table(rows, colWidths=[12 * mm, 55 * mm, 18 * mm, 14 * mm, 28 * mm])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
            ]
        )
    )
    tw, th = t.wrapOn(c, w, h)
    t.drawOn(c, 10 * mm, h - 115 * mm)

    y_sig = 28 * mm
    c.setFont("Helvetica", 8)
    c.drawString(15 * mm, y_sig, "Department Head")
    c.drawString(w / 2, y_sig, "Security Incharge")
    c.line(15 * mm, y_sig - 2 * mm, 55 * mm, y_sig - 2 * mm)
    c.line(w / 2, y_sig - 2 * mm, w / 2 + 40 * mm, y_sig - 2 * mm)
    y_sig -= 14 * mm
    c.drawString(15 * mm, y_sig, "Receiver's Sign")
    c.line(15 * mm, y_sig - 2 * mm, 70 * mm, y_sig - 2 * mm)

    c.setFont("Helvetica", 6)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawString(
        10 * mm,
        8 * mm,
        f"System generated document | ISO 27001 A.5.11 | {now}",
    )
    c.save()
    return buf.getvalue()


def _calc_progress(c: dict[str, Any]) -> tuple[int, int, int]:
    systems = [k for _, k in SYSTEM_ROWS]
    done = sum(
        1
        for s in systems
        if str(c.get(s) or "").strip() in ("Revoked", "N/A")
    )
    hw = 1 if str(c.get("hw_handed_over") or "").strip() == "Yes" else 0
    ev = 1 if c.get("evidence_file_s3_key") or c.get("evidence_file_url") else 0
    total = len(systems) + 2
    pct = round((done + hw + ev) / total * 100) if total else 0
    return done + hw + ev, total, pct


def generate_it_exit_pdf(
    leaver: dict[str, Any], checklist: Optional[dict[str, Any]] = None
) -> bytes:
    c = checklist if checklist is not None else leaver
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("InfoDesk India Private Limited", styles["Title"]))
    story.append(Paragraph("IT EXIT CLEARANCE CHECKLIST", styles["Heading2"]))
    story.append(
        Paragraph(
            "ISO 27001 Control Reference: A.6.5, A.5.11, A.8.1",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 8 * mm))

    hdr = f"""
    <b>Employee Name:</b> {c.get('employee_name') or ''} &nbsp;&nbsp;
    <b>Date of Leaving:</b> {c.get('date_of_leaving') or ''}<br/>
    <b>Department:</b> {c.get('department') or ''} &nbsp;&nbsp;
    <b>Line Manager:</b> {c.get('line_manager') or ''}<br/>
    <b>Email Address:</b> {c.get('email_address') or ''}
    """
    story.append(Paragraph(hdr, styles["Normal"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("<b>SECTION 1 — SYSTEM ACCESS REVOCATION</b>", styles["Heading3"]))

    sys_data = [["System Name", "Status"]]
    for label, key in SYSTEM_ROWS:
        sys_data.append([label, str(c.get(key) or "")])
    t1 = Table(sys_data, hAlign="LEFT")
    t1.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(t1)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("<b>SECTION 2 — HARDWARE</b>", styles["Heading3"]))
    hw_txt = f"""
    <b>HW Handed Over:</b> {c.get('hw_handed_over') or ''} &nbsp;&nbsp;
    <b>Location:</b> {c.get('hw_inventory_location') or ''}<br/>
    <b>Evidence File:</b> {c.get('evidence_file_name') or ''}
    """
    story.append(Paragraph(hw_txt, styles["Normal"]))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("<b>SECTION 3 — SIGN-OFFS</b>", styles["Heading3"]))
    sig = [
        ["Sign-off", "Name", "Status", "Date"],
        [
            "IT Peer Review",
            str(c.get("it_peer_reviewer") or ""),
            str(c.get("it_peer_review") or ""),
            str(c.get("it_peer_review_date") or ""),
        ],
        [
            "Reporting Manager",
            str(c.get("reporting_manager_name") or ""),
            str(c.get("reporting_manager") or ""),
            str(c.get("reporting_manager_date") or ""),
        ],
        [
            "Confirmation Audit",
            str(c.get("confirmation_audit_by") or ""),
            str(c.get("confirmation_audit") or ""),
            str(c.get("confirmation_audit_date") or ""),
        ],
    ]
    t2 = Table(sig, hAlign="LEFT")
    t2.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(t2)
    story.append(Spacer(1, 6 * mm))

    story.append(
        Paragraph(
            f"<b>GitHub Ticket:</b> {c.get('communication_github_ticket') or ''}",
            styles["Normal"],
        )
    )
    done, total, pct = _calc_progress(c)
    story.append(
        Paragraph(
            f"<b>Completion:</b> {pct}% ({done}/{total} items completed)",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 10 * mm))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(
        Paragraph(
            f"Confidential | ISO 27001 A.6.5 | Generated: {now}<br/>"
            "This document is part of the ISO 27001 asset management process.",
            styles["Italic"],
        )
    )
    doc.build(story)
    return buf.getvalue()
