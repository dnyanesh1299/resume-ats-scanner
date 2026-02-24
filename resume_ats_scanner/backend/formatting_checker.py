"""
ATS Formatting Checker - Advanced Resume Quality Audit.
Detects ATS problems: tables, images, layout, sections, etc.
"""

import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

logger = logging.getLogger("resume_ats_scanner")


def check_pdf_structure(pdf_path: str) -> Dict[str, Any]:
    """
    Analyze PDF structure for ATS compatibility issues.
    
    Returns:
        Dict with detected issues and formatting score
    """
    if not pdfplumber:
        return {"score": 70, "issues": ["pdfplumber not available for structure analysis"], "suggestions": []}
    
    issues = []
    suggestions = []
    score = 100
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # Check for tables
                tables = page.find_tables()
                if tables:
                    issues.append("Multi-column/tables detected - ATS may misparse content")
                    score -= 15
                    suggestions.append("Use single-column layout without tables")
                
                # Check for images (simplified: no direct image extraction in pdfplumber)
                # Images often result in empty or sparse text
                text = page.extract_text() or ""
                if len(text.strip()) < 50 and page.images:
                    issues.append("Heavy use of images/graphics detected")
                    score -= 20
                    suggestions.append("Minimize images; use text for important content")
                
                # Check character count
                if len(text) > 5000:
                    issues.append("Extremely long paragraphs or dense text")
                    score -= 5
                    suggestions.append("Use bullet points and shorter paragraphs")
    
    except Exception as e:
        logger.warning(f"PDF structure check failed: {e}")
        issues.append("Could not analyze PDF structure")
        score = 70
    
    return {
        "score": max(0, min(100, score)),
        "issues": list(set(issues)),
        "suggestions": list(set(suggestions))
    }


def check_resume_content(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check resume content for ATS compatibility.
    """
    issues = []
    suggestions = []
    score = 100
    
    # Contact details
    if not resume_data.get("email"):
        issues.append("Missing email address")
        score -= 15
        suggestions.append("Add your email address in the header")
    
    if not resume_data.get("phone") and not resume_data.get("linkedin"):
        issues.append("Missing phone or LinkedIn")
        score -= 5
        suggestions.append("Add at least phone or LinkedIn for contact")
    
    # Sections
    required_sections = ["skills", "experience", "education"]
    for sec in required_sections:
        if sec not in [s.lower() for s in resume_data.get("sections", [])]:
            if sec == "skills" and not resume_data.get("skills"):
                issues.append("Missing Skills section")
                score -= 10
                suggestions.append("Add a dedicated Skills section")
            elif sec == "experience" and not resume_data.get("experience"):
                issues.append("Missing Experience section")
                score -= 15
                suggestions.append("Add Work Experience section")
            elif sec == "education" and not resume_data.get("education"):
                issues.append("Missing Education section")
                score -= 10
                suggestions.append("Add Education section")
    
    # Bullet points
    raw_text = resume_data.get("raw_text", "")
    bullet_chars = ["•", "●", "-", "*"]
    bullet_count = sum(raw_text.count(c) for c in bullet_chars)
    if len(raw_text) > 500 and bullet_count < 3:
        issues.append("Few or no bullet points - hard to scan")
        score -= 10
        suggestions.append("Use bullet points for responsibilities and achievements")
    
    # Paragraph length
    paragraphs = [p for p in raw_text.split("\n\n") if len(p) > 200]
    if len(paragraphs) > 2:
        issues.append("Long paragraphs detected")
        score -= 5
        suggestions.append("Keep paragraphs under 3-4 lines; use bullets")
    
    # File length
    if len(raw_text) > 4000:
        suggestions.append("Consider keeping resume to 1-2 pages for ATS")
    
    return {
        "score": max(0, min(100, score)),
        "issues": issues,
        "suggestions": suggestions
    }


def check_formatting(pdf_path: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combined ATS formatting check.
    
    Returns:
        Dict with ats_formatting_score, issues, suggestions
    """
    structure = check_pdf_structure(pdf_path)
    content = check_resume_content(resume_data)
    
    # Combine scores (weighted)
    struct_score = structure["score"]
    content_score = content["score"]
    final_score = (struct_score * 0.4 + content_score * 0.6)
    
    all_issues = structure["issues"] + content["issues"]
    all_suggestions = structure["suggestions"] + content["suggestions"]
    
    return {
        "ats_formatting_score": round(final_score, 2),
        "structure_score": struct_score,
        "content_score": content_score,
        "issues": list(set(all_issues)),
        "suggestions": list(set(all_suggestions)),
    }
