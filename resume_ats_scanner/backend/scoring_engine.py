"""
Weighted ATS Scoring System.
Industry-style weighted components for final ATS score.
"""

import logging
from typing import Any, Dict, List

from skill_extractor import extract_and_match_skills
from similarity_engine import job_title_similarity, experience_relevance, education_relevance

logger = logging.getLogger("resume_ats_scanner")

# Weight configuration (must sum to 100)
WEIGHTS = {
    "skill_match": 40,
    "keyword_match": 20,
    "experience_relevance": 20,
    "education_match": 10,
    "formatting_score": 10,
}


def compute_keyword_match_score(resume_text: str, jd_skills: List[str]) -> float:
    """TF-IDF based keyword match score (0-100)."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        if not jd_skills or not resume_text:
            return 80.0
        
        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        jd_doc = " ".join(jd_skills)
        matrix = vectorizer.fit_transform([resume_text, jd_doc])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0, 0]
        return round(min(100, max(0, sim * 150)), 2)
    except Exception as e:
        logger.warning(f"Keyword scoring failed: {e}")
        return 50.0


def compute_full_ats_analysis(
    resume_data: Dict[str, Any],
    jd_data: Dict[str, Any],
    formatting_score: float = 75.0,
) -> Dict[str, Any]:
    """
    Compute full ATS analysis with weighted scoring.
    
    Args:
        resume_data: Parsed resume from parser_resume
        jd_data: Parsed JD from parser_jd
        formatting_score: Score from formatting_checker (0-100)
        
    Returns:
        Complete analysis dict with scores and breakdown
    """
    # Skill matching
    skill_result = extract_and_match_skills(resume_data, jd_data)
    skill_match_score = skill_result["skill_match_score"]
    
    # Keyword match
    jd_skills = jd_data.get("required_skills", []) + jd_data.get("tools_technologies", [])
    keyword_score = compute_keyword_match_score(resume_data.get("raw_text", ""), jd_skills)
    
    # Experience relevance
    exp_result = experience_relevance(
        resume_data.get("experience", []),
        jd_data.get("raw_text", ""),
        jd_data.get("job_title", "")
    )
    experience_score = exp_result["relevance_score"]
    
    # Education relevance
    edu_result = education_relevance(
        resume_data.get("education", []),
        jd_data.get("degree_requirements", []),
        jd_data.get("raw_text", "")
    )
    education_score = edu_result["education_match_score"]
    
    # Job title similarity
    resume_titles = [e.get("title", "") for e in resume_data.get("experience", [])]
    best_title = resume_titles[0] if resume_titles else resume_data.get("name", "")
    job_title_score = job_title_similarity(best_title, jd_data.get("job_title", ""))
    
    # Weighted total
    total = (
        (skill_match_score * WEIGHTS["skill_match"] / 100) +
        (keyword_score * WEIGHTS["keyword_match"] / 100) +
        (experience_score * WEIGHTS["experience_relevance"] / 100) +
        (education_score * WEIGHTS["education_match"] / 100) +
        (formatting_score * WEIGHTS["formatting_score"] / 100)
    )
    
    breakdown = [
        {
            "component": "Skill Match Score",
            "score": skill_match_score,
            "weight": WEIGHTS["skill_match"],
            "explanation": f"Matched {skill_result['total_matched']} of {skill_result['total_jd_skills']} required skills from job description."
        },
        {
            "component": "Keyword Match Score",
            "score": keyword_score,
            "weight": WEIGHTS["keyword_match"],
            "explanation": "TF-IDF similarity between resume keywords and job description requirements."
        },
        {
            "component": "Experience Relevance Score",
            "score": experience_score,
            "weight": WEIGHTS["experience_relevance"],
            "explanation": f"Semantic similarity between your experience and JD. {exp_result['relevant_experience_pct']}% of experience is relevant."
        },
        {
            "component": "Education Match Score",
            "score": education_score,
            "weight": WEIGHTS["education_match"],
            "explanation": "Match between your education and degree requirements in the job description."
        },
        {
            "component": "ATS Formatting Score",
            "score": formatting_score,
            "weight": WEIGHTS["formatting_score"],
            "explanation": "Resume structure and formatting compatibility with ATS systems."
        },
    ]
    
    return {
        "total_ats_score": round(total, 2),
        "skill_match_score": skill_match_score,
        "keyword_match_score": keyword_score,
        "experience_relevance_score": experience_score,
        "education_match_score": education_score,
        "job_title_similarity_score": job_title_score,
        "ats_formatting_score": formatting_score,
        "score_breakdown": breakdown,
        "weights": WEIGHTS,
        "skill_analysis": skill_result,
        "experience_analysis": exp_result,
        "education_analysis": edu_result,
    }
