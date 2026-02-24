"""
Similarity Engine for Job Title, Experience, and Education relevance.
Uses sentence-transformers/all-mpnet-base-v2 for semantic similarity.
"""

import logging
from typing import Any, Dict, List, Optional

_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        except Exception as e:
            logging.warning(f"SentenceTransformer not available: {e}")
    return _model


def compute_semantic_similarity(text1: str, text2: str) -> float:
    """
    Compute cosine similarity between two texts using SentenceTransformer.
    
    Returns:
        Similarity score between 0 and 1
    """
    model = _get_model()
    if not model or not text1 or not text2:
        return 0.0
    
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        emb1 = model.encode([text1])
        emb2 = model.encode([text2])
        return float(cosine_similarity(emb1, emb2)[0, 0])
    except Exception as e:
        logging.warning(f"Similarity computation failed: {e}")
        return 0.0


def job_title_similarity(resume_title: str, jd_title: str) -> float:
    """Compute job title similarity score (0-100)."""
    if not resume_title or not jd_title:
        return 0.0
    sim = compute_semantic_similarity(resume_title, jd_title)
    return round(sim * 100, 2)


def experience_relevance(
    resume_experience: List[Dict[str, Any]],
    jd_text: str,
    jd_title: str
) -> Dict[str, Any]:
    """
    Analyze experience relevance by comparing responsibilities with JD.
    
    Returns:
        Dict with relevance_score, relevant_experience_pct, missing_domain_suggestions
    """
    model = _get_model()
    if not model or not resume_experience:
        return {
            "relevance_score": 0,
            "relevant_experience_pct": 0,
            "missing_domain_suggestions": [],
            "details": []
        }
    
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        
        jd_emb = model.encode([jd_text[:4000]])  # Limit JD length
        
        total_sim = 0
        details = []
        
        for exp in resume_experience:
            title = exp.get("title", "")
            company = exp.get("company", "")
            responsibilities = exp.get("responsibilities", [])
            exp_text = f"{title} {company} " + " ".join(responsibilities)
            exp_text = exp_text[:2000]
            
            if not exp_text.strip():
                continue
            
            exp_emb = model.encode([exp_text])
            sim = float(cosine_similarity(exp_emb, jd_emb)[0, 0])
            total_sim += sim
            details.append({
                "title": title,
                "company": company,
                "relevance": round(sim * 100, 2)
            })
        
        avg_sim = (total_sim / len(resume_experience) * 100) if resume_experience else 0
        relevant_count = sum(1 for d in details if d["relevance"] > 50)
        relevant_pct = (relevant_count / len(details) * 100) if details else 0
        
        return {
            "relevance_score": round(avg_sim, 2),
            "relevant_experience_pct": round(relevant_pct, 2),
            "missing_domain_suggestions": [],
            "details": details
        }
    except Exception as e:
        logging.warning(f"Experience relevance failed: {e}")
        return {
            "relevance_score": 0,
            "relevant_experience_pct": 0,
            "missing_domain_suggestions": [],
            "details": []
        }


def education_relevance(
    resume_education: List[Dict[str, Any]],
    jd_degree_requirements: List[str],
    jd_text: str
) -> Dict[str, Any]:
    """
    Check education match with JD requirements.
    
    Returns:
        Dict with education_match_score, matched, details
    """
    if not resume_education:
        return {
            "education_match_score": 0,
            "matched": False,
            "details": []
        }
    
    if not jd_degree_requirements:
        return {
            "education_match_score": 80,
            "matched": True,
            "details": [{"degree": e.get("degree", ""), "institution": e.get("institution", ""), "match": "No degree requirement in JD"} for e in resume_education]
        }
    
    model = _get_model()
    best_score = 0
    
    for edu in resume_education:
        degree = edu.get("degree", "")
        institution = edu.get("institution", "")
        if not degree:
            continue
        
        for jd_deg in jd_degree_requirements:
            if model:
                sim = compute_semantic_similarity(degree, jd_deg)
                best_score = max(best_score, sim * 100)
            elif jd_deg.lower() in degree.lower():
                best_score = max(best_score, 90)
    
    return {
        "education_match_score": round(best_score, 2) if best_score else 50,
        "matched": best_score > 50,
        "details": [{"degree": e.get("degree", ""), "institution": e.get("institution", "")} for e in resume_education]
    }
