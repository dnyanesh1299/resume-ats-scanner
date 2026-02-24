"""
Resume PDF Parser Module.
Extracts structured data from resume PDFs using pdfplumber and OCR fallback.
"""

import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pytesseract
    from pdf2image import convert_from_path
except ImportError:
    pytesseract = None
    convert_from_path = None

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_lg")
        except (ImportError, OSError) as e:
            logging.getLogger("resume_ats_scanner").warning(f"spaCy not available: {e}")
    return _nlp

from utils import extract_emails, extract_phones, extract_urls, normalize_text

logger = logging.getLogger("resume_ats_scanner")


# Common resume section headers (case-insensitive)
RESUME_SECTIONS = [
    "summary", "objective", "profile", "experience", "work experience",
    "employment", "education", "skills", "technical skills", "competencies",
    "projects", "certifications", "certification", "achievements", "awards",
    "honors", "publications", "references", "languages", "interests",
    "professional experience", "work history", "academic", "qualifications"
]


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using pdfplumber. Fallback to OCR if needed.
    
    Args:
        pdf_path: Path to resume PDF file
        
    Returns:
        Extracted text string
    """
    if not pdfplumber:
        raise ImportError("pdfplumber is required. Install with: pip install pdfplumber")
    
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    # OCR fallback for scanned/image-based PDFs
                    if pytesseract and convert_from_path:
                        images = convert_from_path(pdf_path, first_page=page.page_number, last_page=page.page_number)
                        for img in images:
                            text += pytesseract.image_to_string(img) + "\n"
                    else:
                        logger.warning("OCR fallback not available. Install pytesseract and pdf2image for scanned PDFs.")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise
    
    return text.strip()


def detect_sections(text: str) -> Dict[str, str]:
    """
    Segment resume text into sections based on common headings.
    
    Returns:
        Dict mapping section name to section content
    """
    sections = {}
    lines = text.split("\n")
    current_section = "header"
    current_content = []
    
    section_pattern = re.compile(
        r"^[" + "".join(re.escape(c) for c in "•●◆▪▸►➤-*#") + r"]?\s*"
        r"([A-Za-z][A-Za-z\s&\/]+?)\s*[:]?\s*$",
        re.IGNORECASE
    )
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        match = section_pattern.match(line_stripped)
        detected_section = None
        if match:
            candidate = normalize_text(match.group(1))
            for known in RESUME_SECTIONS:
                if known in candidate or candidate in known:
                    detected_section = known
                    break
            if not detected_section and len(candidate) < 30:
                for known in RESUME_SECTIONS:
                    if known.startswith(candidate) or candidate.startswith(known):
                        detected_section = known
                        break
        
        if detected_section:
            if current_section != "header":
                sections[current_section] = "\n".join(current_content).strip()
            current_section = detected_section
            current_content = []
        else:
            current_content.append(line_stripped)
    
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()
    
    return sections


def extract_entities_with_spacy(text: str) -> Dict[str, List[str]]:
    """Extract named entities using spaCy NER."""
    nlp = _get_nlp()
    if not nlp:
        return {"persons": [], "orgs": [], "dates": []}
    
    entities = {"persons": [], "orgs": [], "dates": []}
    doc = nlp(text[:100000])  # Limit for performance
    
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["persons"].append(ent.text.strip())
        elif ent.label_ in ("ORG", "GPE"):
            entities["orgs"].append(ent.text.strip())
        elif ent.label_ == "DATE":
            entities["dates"].append(ent.text.strip())
    
    return {k: list(set(v)) for k, v in entities.items()}


def parse_experience(section_text: str) -> List[Dict[str, Any]]:
    """Parse work experience section into structured entries."""
    experiences = []
    blocks = re.split(r"\n(?=\d{4}|\d{1,2}/\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})", section_text, flags=re.IGNORECASE)
    
    date_pattern = re.compile(
        r"(\d{1,2}/\d{4}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*[-–—to]+\s*"
        r"(\d{1,2}/\d{4}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|Present|Current)",
        re.IGNORECASE
    )
    
    for block in blocks:
        block = block.strip()
        if len(block) < 20:
            continue
        
        dates = date_pattern.search(block)
        start_date = dates.group(1) if dates else ""
        end_date = dates.group(2) if dates else ""
        
        lines = block.split("\n")
        title = lines[0].strip() if lines else ""
        company = ""
        for line in lines[1:3]:
            if line and not re.match(r"^[\d\-/]+", line):
                company = line.strip()
                break
        
        bullet_points = [l.strip().lstrip("•●▪-*").strip() for l in lines if l.strip().startswith(("•", "●", "-", "*"))]
        
        experiences.append({
            "title": title,
            "company": company,
            "start_date": start_date,
            "end_date": end_date,
            "duration": f"{start_date} - {end_date}",
            "responsibilities": bullet_points if bullet_points else [l for l in lines[2:] if len(l) > 20]
        })
    
    return experiences


def parse_education(section_text: str) -> List[Dict[str, Any]]:
    """Parse education section."""
    educations = []
    blocks = re.split(r"\n(?=[A-Z])", section_text)
    
    degree_pattern = re.compile(
        r"(Bachelor|B\.?S\.?|B\.?A\.?|Master|M\.?S\.?|M\.?A\.?|MBA|PhD|Ph\.?D\.?|B\.?Tech|M\.?Tech|Associate|Diploma)"
        r"[^\n]*?(?:in|of)?\s*([A-Za-z\s&,]+?)(?:\s*[-–,]\s*|\s*$)",
        re.IGNORECASE
    )
    
    for block in blocks:
        block = block.strip()
        if len(block) < 10:
            continue
        
        match = degree_pattern.search(block)
        degree = match.group(0).split(",")[0].strip() if match else ""
        institution = ""
        year = ""
        
        year_match = re.search(r"\b(19|20)\d{2}\b", block)
        if year_match:
            year = year_match.group(0)
        
        lines = block.split("\n")
        if lines:
            institution = lines[0] if not degree else (lines[1] if len(lines) > 1 else "")
        
        educations.append({
            "degree": degree or lines[0] if lines else "",
            "institution": institution,
            "year": year,
            "details": block
        })
    
    return educations


def parse_skills(section_text: str) -> List[str]:
    """Extract skills from skills section (comma, pipe, line separated)."""
    skills = []
    text = section_text.replace("|", ",").replace(";", ",").replace("\n", ",")
    parts = re.split(r"[,/\n]+", text)
    
    for part in parts:
        skill = part.strip().strip("•●▪-*").strip()
        if skill and len(skill) > 1 and len(skill) < 80:
            skills.append(skill)
    
    return list(set(skills))


def parse_projects(section_text: str) -> List[Dict[str, Any]]:
    """Parse projects section."""
    projects = []
    blocks = re.split(r"\n(?=[A-Z\*•])", section_text)
    
    for block in blocks:
        block = block.strip()
        if len(block) < 15:
            continue
        
        lines = block.split("\n")
        name = lines[0].strip().strip("•●-*") if lines else ""
        desc = " ".join(lines[1:]) if len(lines) > 1 else block
        
        projects.append({
            "name": name,
            "description": desc
        })
    
    return projects


def parse_certifications(section_text: str) -> List[str]:
    """Parse certifications section."""
    certs = []
    lines = [l.strip().lstrip("•●▪-*").strip() for l in section_text.split("\n") if l.strip()]
    for line in lines:
        if len(line) > 3:
            certs.append(line)
    return certs


def parse_resume(pdf_path: str) -> Dict[str, Any]:
    """
    Main resume parsing function. Returns structured JSON.
    
    Args:
        pdf_path: Path to resume PDF
        
    Returns:
        Structured resume data as dict
    """
    logger.info(f"Parsing resume: {pdf_path}")
    
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        raise ValueError("No text could be extracted from PDF")
    
    sections = detect_sections(raw_text)
    entities = extract_entities_with_spacy(raw_text)
    
    # Contact info from full text
    emails = extract_emails(raw_text)
    phones = extract_phones(raw_text)
    urls = extract_urls(raw_text)
    
    linkedin = [u for u in urls if "linkedin" in u.lower()]
    github = [u for u in urls if "github" in u.lower()]
    
    # Name: first person entity or first line
    name = ""
    if entities["persons"]:
        name = entities["persons"][0]
    elif raw_text:
        first_line = raw_text.split("\n")[0].strip()
        if len(first_line) < 50 and not first_line.startswith("http"):
            name = first_line
    
    # Skills - from section or extract from entire resume
    skills = []
    for key in ["skills", "technical skills", "competencies"]:
        if key in sections:
            skills.extend(parse_skills(sections[key]))
    
    if not skills:
        skills = parse_skills(raw_text)
    
    # Experience
    experience = []
    for key in ["experience", "work experience", "employment", "professional experience"]:
        if key in sections:
            experience = parse_experience(sections[key])
            break
    
    # Education
    education = []
    for key in ["education", "academic", "qualifications"]:
        if key in sections:
            education = parse_education(sections[key])
            break
    
    # Projects
    projects = []
    if "projects" in sections:
        projects = parse_projects(sections["projects"])
    
    # Certifications
    certifications = []
    if "certifications" in sections or "certification" in sections:
        cert_text = sections.get("certifications", "") or sections.get("certification", "")
        certifications = parse_certifications(cert_text)
    
    # Achievements
    achievements = []
    for key in ["achievements", "awards", "honors"]:
        if key in sections:
            achievements.extend([l.strip().lstrip("•●-*") for l in sections[key].split("\n") if l.strip()])
    
    result = {
        "name": name or "Unknown",
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "linkedin": linkedin[0] if linkedin else "",
        "github": github[0] if github else "",
        "skills": list(set(skills)),
        "experience": experience,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
        "raw_text": raw_text,
        "sections": list(sections.keys()),
    }
    
    logger.info(f"Parsed resume for {result['name']} with {len(skills)} skills")
    return result
