"""
Professional ATS Report PDF Generator using reportlab.
"""

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, ListFlowable, ListItem
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger("resume_ats_scanner")


def generate_ats_report(
    analysis_result: Dict[str, Any],
    output_path: Optional[str] = None
) -> bytes:
    """
    Generate professional ATS report PDF.
    
    Args:
        analysis_result: Full analysis from scoring_engine
        output_path: Optional file path to save PDF
        
    Returns:
        PDF as bytes
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab required. Install with: pip install reportlab")
    
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=12,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        name="CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("ATS Compatibility Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Candidate & Job Info
    resume_data = analysis_result.get("resume_data", {})
    jd_data = analysis_result.get("jd_data", {})
    
    info_data = [
        ["Candidate:", resume_data.get("name", "N/A")],
        ["Email:", resume_data.get("email", "N/A")],
        ["Job Analyzed:", jd_data.get("job_title", "N/A")],
        ["Report Date:", datetime.now().strftime("%Y-%m-%d %H:%M")],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Overall ATS Score
    total_score = analysis_result.get("total_ats_score", 0)
    score_hex = "#22c55e" if total_score >= 70 else ("#f59e0b" if total_score >= 50 else "#ef4444")
    
    elements.append(Paragraph("Overall ATS Compatibility Score", heading_style))
    elements.append(Paragraph(
        f'<font size="24" color="{score_hex}">{total_score}%</font>',
        styles["Normal"]
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Score Breakdown
    elements.append(Paragraph("Score Breakdown", heading_style))
    breakdown = analysis_result.get("score_breakdown", [])
    breakdown_data = [["Component", "Score", "Weight", "Explanation"]]
    for b in breakdown:
        breakdown_data.append([
            b.get("component", ""),
            f"{b.get('score', 0)}%",
            f"{b.get('weight', 0)}%",
            b.get("explanation", "")[:80] + "..." if len(b.get("explanation", "")) > 80 else b.get("explanation", "")
        ])
    
    btable = Table(breakdown_data, colWidths=[1.5*inch, 0.8*inch, 0.7*inch, 2.5*inch])
    btable.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
    ]))
    elements.append(btable)
    elements.append(Spacer(1, 0.3*inch))
    
    # Matched Skills
    skill_analysis = analysis_result.get("skill_analysis", {})
    matched = skill_analysis.get("matched_skills", [])
    elements.append(Paragraph("Matched Skills", heading_style))
    if matched:
        items = [ListItem(Paragraph(f"{s.get('skill', '')} (confidence: {s.get('confidence', 0)})", styles["Normal"])) for s in matched[:20]]
        elements.append(ListFlowable(items))
    else:
        elements.append(Paragraph("No skills matched.", styles["Normal"]))
    elements.append(Spacer(1, 0.2*inch))
    
    # Missing Skills
    missing = skill_analysis.get("missing_skills", [])
    elements.append(Paragraph("Missing Skills", heading_style))
    if missing:
        items = [ListItem(Paragraph(s, styles["Normal"])) for s in missing[:15]]
        elements.append(ListFlowable(items))
    else:
        elements.append(Paragraph("All required skills are present.", styles["Normal"]))
    elements.append(Spacer(1, 0.2*inch))
    
    # Experience Relevance
    exp_analysis = analysis_result.get("experience_analysis", {})
    elements.append(Paragraph("Experience Relevance", heading_style))
    elements.append(Paragraph(
        f"Relevance Score: {exp_analysis.get('relevance_score', 0)}% | "
        f"Relevant Experience: {exp_analysis.get('relevant_experience_pct', 0)}%",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    # Education
    edu_analysis = analysis_result.get("education_analysis", {})
    elements.append(Paragraph("Education Match", heading_style))
    elements.append(Paragraph(
        f"Education Score: {edu_analysis.get('education_match_score', 0)}% | "
        f"Matched: {edu_analysis.get('matched', False)}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Formatting Feedback
    elements.append(Paragraph("Formatting Feedback", heading_style))
    issues = analysis_result.get("formatting_issues", [])
    suggestions = analysis_result.get("formatting_suggestions", [])
    
    if issues:
        elements.append(Paragraph("Issues:", styles["Normal"]))
        for i in issues[:5]:
            elements.append(Paragraph(f"• {i}", styles["Normal"]))
    if suggestions:
        elements.append(Paragraph("Improvement Suggestions:", styles["Normal"]))
        for s in suggestions[:5]:
            elements.append(Paragraph(f"• {s}", styles["Normal"]))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Final Recommendations
    elements.append(Paragraph("Improvement Recommendations", heading_style))
    recs = analysis_result.get("improvement_recommendations", [])
    if recs:
        for r in recs[:8]:
            elements.append(Paragraph(f"• {r}", styles["Normal"]))
    else:
        elements.append(Paragraph("• Add missing skills to your resume", styles["Normal"]))
        elements.append(Paragraph("• Tailor bullet points to match job requirements", styles["Normal"]))
        elements.append(Paragraph("• Use ATS-friendly formatting (single column, standard fonts)", styles["Normal"]))
    
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    
    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"Report saved to {output_path}")
    
    return pdf_bytes
