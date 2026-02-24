"""
Utility functions for the Resume ATS Scanner.
Handles logging, file operations, and common helpers.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return application logger.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger("resume_ats_scanner")
    return logger


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def load_json_file(file_path: str) -> Any:
    """
    Load JSON file safely.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON content or empty dict/list on error
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"Failed to load JSON from {file_path}: {e}")
        return {} if "synonyms" in file_path else []


def load_skills_ontology() -> tuple[List[str], Dict[str, str]]:
    """
    Load skills and synonyms from dataset folder.
    
    Returns:
        Tuple of (skills_list, synonyms_dict)
    """
    project_root = get_project_root()
    skills_path = project_root / "dataset" / "skills.json"
    synonyms_path = project_root / "dataset" / "synonyms.json"
    
    skills = load_json_file(str(skills_path))
    synonyms = load_json_file(str(synonyms_path))
    
    if not isinstance(skills, list):
        skills = []
    if not isinstance(synonyms, dict):
        synonyms = {}
        
    return skills, synonyms


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from filename."""
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
    return "".join(c for c in filename if c in safe_chars) or "unnamed"


def ensure_directory(path: str) -> Path:
    """Create directory if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_analysis_id() -> str:
    """Generate unique analysis ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + os.urandom(4).hex()


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison: lowercase, strip, collapse whitespace.
    """
    if not text or not isinstance(text, str):
        return ""
    return " ".join(text.lower().split())


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text using regex."""
    import re
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))


def extract_phones(text: str) -> List[str]:
    """Extract phone numbers from text."""
    import re
    pattern = r'[\+]?[(]?[0-9]{2,4}[)]?[-\s\.]?[0-9]{2,4}[-\s\.]?[0-9]{2,9}'
    return list(set(re.findall(pattern, text)))


def extract_urls(text: str) -> List[str]:
    """Extract URLs (LinkedIn, GitHub, etc.) from text."""
    import re
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return list(set(re.findall(pattern, text)))
