"""
Advanced Skill Matching Engine.
Combines exact, synonym, fuzzy, semantic, and TF-IDF matching.
"""

import logging
from typing import Any, Dict, List, Tuple

from utils import load_skills_ontology, normalize_text

logger = logging.getLogger("resume_ats_scanner")

# Lazy imports for optional dependencies
_sentence_transformer = None
_tfidf = None
_rapidfuzz = None


def _get_sentence_transformer():
    global _sentence_transformer
    if _sentence_transformer is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformer = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        except Exception as e:
            logger.warning(f"SentenceTransformer not available: {e}")
    return _sentence_transformer


def _get_rapidfuzz():
    global _rapidfuzz
    if _rapidfuzz is None:
        try:
            from rapidfuzz import fuzz
            _rapidfuzz = fuzz
        except ImportError:
            try:
                from fuzzywuzzy import fuzz
                _rapidfuzz = fuzz
            except ImportError:
                logger.warning("rapidfuzz/fuzzywuzzy not available for fuzzy matching")
    return _rapidfuzz


def _get_tfidf():
    global _tfidf
    if _tfidf is None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            _tfidf = TfidfVectorizer
        except ImportError:
            logger.warning("sklearn not available for TF-IDF")
    return _tfidf


def exact_match(resume_skills: List[str], jd_skills: List[str]) -> Tuple[List[Tuple[str, float]], List[str]]:
    """Exact matching (case-insensitive)."""
    resume_set = {normalize_text(s) for s in resume_skills}
    jd_set = {normalize_text(s) for s in jd_skills}
    
    matched = [(s, 1.0) for s in jd_skills if normalize_text(s) in resume_set]
    missing = [s for s in jd_skills if normalize_text(s) not in resume_set]
    
    return matched, missing


def synonym_match(resume_skills: List[str], jd_skills: List[str], synonyms: Dict[str, str]) -> Tuple[List[Tuple[str, float]], List[str]]:
    """Match via synonym mapping."""
    syn_inv = {v.lower(): k for k, v in synonyms.items()}
    resume_norm = {normalize_text(s): s for s in resume_skills}
    
    matched = []
    missing = []
    
    for jd_skill in jd_skills:
        jd_norm = normalize_text(jd_skill)
        found = False
        for syn, canonical in synonyms.items():
            if normalize_text(canonical) == jd_norm:
                if jd_norm in resume_norm or normalize_text(syn) in {normalize_text(r) for r in resume_skills}:
                    matched.append((jd_skill, 0.95))
                    found = True
                    break
        if not found:
            for res_skill in resume_skills:
                res_norm = normalize_text(res_skill)
                if res_norm == jd_norm:
                    matched.append((jd_skill, 1.0))
                    found = True
                    break
                if synonyms.get(res_skill, res_skill).lower() == jd_skill.lower():
                    matched.append((jd_skill, 0.95))
                    found = True
                    break
        if not found:
            missing.append(jd_skill)
    
    return matched, missing


def fuzzy_match(resume_skills: List[str], jd_skills: List[str], threshold: int = 85) -> Tuple[List[Tuple[str, float]], List[str]]:
    """Fuzzy string matching using rapidfuzz."""
    rf = _get_rapidfuzz()
    if not rf:
        return [], jd_skills
    
    matched = []
    missing = []
    
    for jd_skill in jd_skills:
        best_score = 0
        best_match = None
        for res_skill in resume_skills:
            score = rf.token_set_ratio(jd_skill.lower(), res_skill.lower())
            if score >= threshold and score > best_score:
                best_score = score
                best_match = res_skill
        if best_match:
            matched.append((jd_skill, best_score / 100.0))
        else:
            missing.append(jd_skill)
    
    return matched, missing


def semantic_match(resume_skills: List[str], jd_skills: List[str], threshold: float = 0.6) -> Tuple[List[Tuple[str, float]], List[str]]:
    """Semantic similarity using SentenceTransformer."""
    model = _get_sentence_transformer()
    if not model or not resume_skills or not jd_skills:
        return [], jd_skills
    
    try:
        resume_emb = model.encode(resume_skills)
        jd_emb = model.encode(jd_skills)
        
        from sklearn.metrics.pairwise import cosine_similarity
        sim = cosine_similarity(jd_emb, resume_emb)
        
        matched = []
        missing = []
        for i, jd_skill in enumerate(jd_skills):
            max_sim = float(sim[i].max())
            if max_sim >= threshold:
                matched.append((jd_skill, max_sim))
            else:
                missing.append(jd_skill)
        
        return matched, missing
    except Exception as e:
        logger.warning(f"Semantic matching failed: {e}")
        return [], jd_skills


def tfidf_match(resume_text: str, jd_skills: List[str], threshold: float = 0.1) -> Tuple[List[Tuple[str, float]], List[str]]:
    """TF-IDF keyword matching against full resume text."""
    TfidfVectorizer = _get_tfidf()
    if not TfidfVectorizer or not jd_skills:
        return [], jd_skills
    
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        doc_matrix = vectorizer.fit_transform([resume_text] + jd_skills)
        sim = cosine_similarity(doc_matrix[0:1], doc_matrix[1:])
        
        matched = []
        missing = []
        for i, jd_skill in enumerate(jd_skills):
            score = float(sim[0, i])
            if score >= threshold:
                matched.append((jd_skill, min(1.0, score * 2)))
            else:
                missing.append(jd_skill)
        
        return matched, missing
    except Exception as e:
        logger.warning(f"TF-IDF matching failed: {e}")
        return [], jd_skills


def combine_matching_results(
    exact_m: List[Tuple[str, float]], exact_u: List[str],
    synonym_m: List[Tuple[str, float]], synonym_u: List[str],
    fuzzy_m: List[Tuple[str, float]], fuzzy_u: List[str],
    semantic_m: List[Tuple[str, float]], semantic_u: List[str],
    tfidf_m: List[Tuple[str, float]], tfidf_u: List[str],
) -> Tuple[Dict[str, float], List[str]]:
    """
    Combine all matching results into final matched (with confidence) and missing lists.
    """
    matched_dict = {}
    
    for skill, conf in exact_m + synonym_m:
        matched_dict[skill] = max(matched_dict.get(skill, 0), conf)
    
    for skill, conf in fuzzy_m:
        matched_dict[skill] = max(matched_dict.get(skill, 0), conf * 0.9)
    
    for skill, conf in semantic_m:
        matched_dict[skill] = max(matched_dict.get(skill, 0), conf * 0.95)
    
    for skill, conf in tfidf_m:
        matched_dict[skill] = max(matched_dict.get(skill, 0), conf * 0.85)
    
    all_missing = set(exact_u) & set(synonym_u) & set(fuzzy_u) & set(semantic_u) & set(tfidf_u)
    all_missing = set(exact_u)
    for s in synonym_u + fuzzy_u + semantic_u + tfidf_u:
        if s not in matched_dict:
            all_missing.add(s)
    
    return matched_dict, list(all_missing)


def extract_and_match_skills(
    resume_data: Dict[str, Any],
    jd_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main skill matching function.
    
    Returns:
        Dict with matched_skills, missing_skills, suggested_skills, scores
    """
    resume_skills = resume_data.get("skills", [])
    resume_text = resume_data.get("raw_text", "")
    jd_skills = jd_data.get("required_skills", []) + jd_data.get("tools_technologies", [])
    jd_skills = list(set(jd_skills))
    
    skills, synonyms = load_skills_ontology()
    
    # Run all matchers
    exact_m, exact_u = exact_match(resume_skills, jd_skills)
    synonym_m, synonym_u = synonym_match(resume_skills, jd_skills, synonyms)
    fuzzy_m, fuzzy_u = fuzzy_match(resume_skills, jd_skills)
    semantic_m, semantic_u = semantic_match(resume_skills, jd_skills)
    tfidf_m, tfidf_u = tfidf_match(resume_text, jd_skills)
    
    # Combine: if any matcher found it, it's matched
    matched_dict = {}
    for skill, conf in exact_m + synonym_m:
        matched_dict[skill] = max(matched_dict.get(skill, 0), conf)
    for skill, conf in fuzzy_m:
        if skill not in matched_dict:
            matched_dict[skill] = max(matched_dict.get(skill, 0), conf * 0.9)
    for skill, conf in semantic_m:
        if skill not in matched_dict:
            matched_dict[skill] = max(matched_dict.get(skill, 0), conf * 0.9)
    for skill, conf in tfidf_m:
        if skill not in matched_dict:
            matched_dict[skill] = max(matched_dict.get(skill, 0), min(1.0, conf))
    
    missing = [s for s in jd_skills if s not in matched_dict]
    
    matched_skills = [{"skill": k, "confidence": round(v, 2)} for k, v in matched_dict.items()]
    
    skill_match_score = (len(matched_dict) / len(jd_skills) * 100) if jd_skills else 100
    
    # Suggested skills to add (top missing)
    suggested = missing[:15]
    
    return {
        "matched_skills": matched_skills,
        "missing_skills": missing,
        "suggested_skills_to_add": suggested,
        "skill_match_score": round(skill_match_score, 2),
        "total_jd_skills": len(jd_skills),
        "total_matched": len(matched_dict),
    }
