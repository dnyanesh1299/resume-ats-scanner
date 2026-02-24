"""
Job Description Parser Module.
Extracts structured data from JD text or PDF.
"""

import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from utils import load_skills_ontology, normalize_text

logger = logging.getLogger("resume_ats_scanner")


def extract_text_from_jd_pdf(pdf_path: str) -> str:
    """Extract text from JD PDF."""
    if not pdfplumber:
        raise ImportError("pdfplumber required for JD PDF parsing")
    
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_jd_from_text(text: str) -> str:
    """Use text as-is (for pasted JD)."""
    return text.strip()


def extract_job_title(text: str) -> str:
    """Extract job title from JD (usually in first few lines)."""
    lines = text.split("\n")
    for i, line in enumerate(lines[:15]):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        # Skip common prefixes
        if re.match(r"^(about|company|location|job|position|role|department):?", line, re.I):
            continue
        # Likely title: Title case, not too long
        if 5 <= len(line) <= 80 and not line.startswith("http"):
            return line
    return "Job Title"


def extract_skills_from_jd(text: str) -> List[str]:
    """Extract required/preferred skills from JD using ontology + pattern matching."""
    skills, synonyms = load_skills_ontology()
    ontology_set = {normalize_text(s) for s in skills}
    synonym_map = {normalize_text(k): v for k, v in synonyms.items()}
    
    found_skills = []
    text_lower = text.lower()
    
    # Direct ontology match
    for skill in skills:
        if skill.lower() in text_lower or f" {skill.lower()} " in text_lower:
            found_skills.append(skill)
    
    # Synonym expansion
    for syn, canonical in synonym_map.items():
        if syn in text_lower and canonical not in found_skills:
            found_skills.append(canonical)
    
    # Pattern: "X years of Y", "experience with Y", "knowledge of Y"
    patterns = [
        r"(?:experience|knowledge|proficiency|expertise)\s+(?:with|in|of)\s+([A-Za-z0-9\s\.\#\+\-]+?)(?:\.|,|$|\n)",
        r"([A-Za-z0-9\s\.\#\+]+)\s+(?:experience|skills?|knowledge)",
        r"(?:required|preferred|must have)\s*[:\-]?\s*([A-Za-z0-9\s,\.\/\-]+)",
        r"(?:Python|Java|JavaScript|C\+\+|SQL|React|AWS|Docker|Kubernetes|ML|NLP|TensorFlow|PyTorch)",
    ]
    
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            candidate = m.group(1).strip() if m.lastindex else m.group(0).strip()
            candidate = re.sub(r"\s+", " ", candidate).strip()
            if 2 <= len(candidate) <= 50:
                if candidate in skills:
                    found_skills.append(candidate)
                elif normalize_text(candidate) in ontology_set:
                    found_skills.append(candidate)
    
    return list(set(found_skills))


def extract_years_experience(text: str) -> Optional[str]:
    """Extract years of experience required."""
    patterns = [
        r"(\d+)\+?\s*years?\s*(?:of)?\s*(?:experience|exp)",
        r"(?:experience|exp)\s*[:\-]?\s*(\d+)\+?\s*years?",
        r"(\d+)\s*-\s*(\d+)\s*years",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            if m.lastindex >= 2:
                return f"{m.group(1)}-{m.group(2)} years"
            return f"{m.group(1)}+ years"
    return None


def extract_degree_requirement(text: str) -> List[str]:
    """Extract degree requirements."""
    degree_patterns = [
        r"Bachelor['\s]*(?:s|'s)?\s*(?:degree|in)?",
        r"B\.?S\.?|B\.?A\.?|B\.?Tech",
        r"Master['\s]*(?:s|'s)?\s*(?:degree|in)?",
        r"M\.?S\.?|M\.?A\.?|MBA|M\.?Tech",
        r"PhD|Ph\.?D\.?|Doctorate",
        r"Associate\s*(?:degree)?",
        r"High\s*School|Diploma",
    ]
    found = []
    for p in degree_patterns:
        if re.search(p, text, re.IGNORECASE):
            found.append(re.search(p, text, re.IGNORECASE).group(0).strip())
    return found


def extract_domain_keywords(text: str) -> List[str]:
    """Extract domain keywords (AI, Cloud, Security, etc.)."""
    domains = ["AI", "Machine Learning", "Cloud", "Security", "Data", "Web", "Mobile", "DevOps", "Backend", "Frontend"]
    found = [d for d in domains if d.lower() in text.lower()]
    return found


def extract_tools_technologies(text: str) -> List[str]:
    """Extract tools and technologies mentioned."""
    skills, _ = load_skills_ontology()
    found = []
    for s in skills:
        if s in text or s.lower() in text.lower():
            found.append(s)
    return list(set(found))


def parse_job_description(
    content: str,
    is_pdf: bool = False,
    pdf_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse job description from text or PDF.
    
    Args:
        content: Pasted text content (if is_pdf False) or ignored (if is_pdf True)
        is_pdf: Whether input is PDF
        pdf_path: Path to JD PDF (required if is_pdf True)
        
    Returns:
        Structured JD data as dict
    """
    if is_pdf and pdf_path:
        raw_text = extract_text_from_jd_pdf(pdf_path)
    else:
        raw_text = extract_jd_from_text(content)
    
    if not raw_text:
        raise ValueError("No content in job description")
    
    result = {
        "job_title": extract_job_title(raw_text),
        "raw_text": raw_text,
        "required_skills": extract_skills_from_jd(raw_text),
        "years_experience": extract_years_experience(raw_text),
        "degree_requirements": extract_degree_requirement(raw_text),
        "domain_keywords": extract_domain_keywords(raw_text),
        "tools_technologies": extract_tools_technologies(raw_text),
    }
    
    logger.info(f"Parsed JD: {result['job_title']} with {len(result['required_skills'])} skills")
    return result
