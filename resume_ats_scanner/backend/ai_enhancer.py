"""
AI Resume Enhancement Mode.
Uses OpenAI API (optional) for resume improvement suggestions.
Safe fallback when API key not provided.
"""

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("resume_ats_scanner")


def get_openai_client():
    """Get OpenAI client if API key is available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        logger.warning("openai package not installed. pip install openai")
        return None


def enhance_bullet_point(bullet: str, jd_context: str, client: Optional[Any] = None) -> str:
    """
    Rewrite weak bullet point to ATS-friendly format.
    Uses OpenAI if available, else returns rule-based improvement.
    """
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Rewrite resume bullet points to be ATS-friendly: use strong action verbs, include metrics, be concise. Output only the rewritten bullet, no explanation."},
                    {"role": "user", "content": f"Original: {bullet}\n\nJob context: {jd_context[:500]}\n\nRewritten bullet:"}
                ],
                max_tokens=150,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI enhancement failed: {e}")
    
    # Fallback: simple improvements
    action_verbs = ["Developed", "Implemented", "Led", "Managed", "Optimized", "Designed", "Built", "Created"]
    bullet = bullet.strip()
    if bullet and not any(bullet.startswith(v) for v in action_verbs):
        # Suggest adding action verb
        return f"Consider starting with: {action_verbs[0]} - {bullet[:80]}..."
    return bullet


def suggest_action_verbs() -> List[str]:
    """Suggest strong action verbs for resume."""
    return [
        "Achieved", "Developed", "Implemented", "Led", "Managed", "Optimized",
        "Designed", "Built", "Created", "Improved", "Reduced", "Increased",
        "Streamlined", "Automated", "Collaborated", "Mentored", "Delivered",
        "Launched", "Transformed", "Spearheaded", "Architected", "Deployed"
    ]


def suggest_project_improvements(project: Dict[str, Any], jd_skills: List[str]) -> str:
    """Suggest improvements for project description."""
    desc = project.get("description", "")
    name = project.get("name", "")
    
    missing_in_desc = [s for s in jd_skills[:5] if s.lower() not in desc.lower()]
    if missing_in_desc:
        return f"Consider mentioning: {', '.join(missing_in_desc[:3])} in project '{name}'"
    return f"Project '{name}' looks good. Add quantifiable results if possible."


def ai_enhance_resume(
    resume_data: Dict[str, Any],
    jd_data: Dict[str, Any],
    analysis_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    AI Resume Enhancement Mode - generate improvement suggestions.
    
    Returns:
        Dict with enhanced_bullets, action_verbs, project_suggestions, skill_recommendations
    """
    client = get_openai_client()
    jd_text = jd_data.get("raw_text", "")[:1000]
    jd_skills = jd_data.get("required_skills", []) + jd_data.get("tools_technologies", [])
    
    enhanced_bullets = []
    for exp in resume_data.get("experience", [])[:3]:
        for resp in exp.get("responsibilities", [])[:2]:
            if resp:
                enhanced = enhance_bullet_point(resp, jd_text, client)
                enhanced_bullets.append({
                    "original": resp[:100] + "..." if len(resp) > 100 else resp,
                    "suggested": enhanced
                })
    
    project_suggestions = []
    for proj in resume_data.get("projects", [])[:3]:
        sug = suggest_project_improvements(proj, jd_skills)
        project_suggestions.append(sug)
    
    missing_skills = analysis_result.get("skill_analysis", {}).get("missing_skills", [])
    skill_recommendations = [f"Add skill: {s}" for s in missing_skills[:10]]
    
    return {
        "enhanced_bullets": enhanced_bullets,
        "action_verbs": suggest_action_verbs(),
        "project_suggestions": project_suggestions,
        "skill_recommendations": skill_recommendations,
        "ai_provider": "openai" if client else "fallback"
    }
