"""
Database module - MongoDB or JSON fallback storage.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("resume_ats_scanner")

# MongoDB connection
_mongo_client = None
_db = None


def get_mongo_client():
    """Get MongoDB client if available."""
    global _mongo_client, _db
    if _mongo_client is not None:
        return _mongo_client, _db
    
    try:
        from pymongo import MongoClient
        import os
        uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        _mongo_client = MongoClient(uri)
        _db = _mongo_client.get_database("resume_ats_scanner")
        return _mongo_client, _db
    except Exception as e:
        logger.info(f"MongoDB not available: {e}. Using JSON fallback.")
        return None, None


def get_storage_path() -> Path:
    """Get path for JSON fallback storage."""
    return Path(__file__).parent.parent / "storage" / "analyses"


def save_analysis(analysis_id: str, data: Dict[str, Any]) -> bool:
    """Save analysis to MongoDB or JSON file."""
    client, db = get_mongo_client()
    
    if db is not None:
        try:
            collection = db["analyses"]
            data["_id"] = analysis_id
            collection.replace_one({"_id": analysis_id}, data, upsert=True)
            return True
        except Exception as e:
            logger.error(f"MongoDB save failed: {e}")
    
    # JSON fallback
    try:
        storage = get_storage_path()
        storage.mkdir(parents=True, exist_ok=True)
        file_path = storage / f"{analysis_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"JSON save failed: {e}")
        return False


def load_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Load analysis by ID."""
    client, db = get_mongo_client()
    
    if db is not None:
        try:
            doc = db["analyses"].find_one({"_id": analysis_id})
            if doc:
                doc.pop("_id", None)
                return doc
        except Exception as e:
            logger.error(f"MongoDB load failed: {e}")
    
    # JSON fallback
    try:
        file_path = get_storage_path() / f"{analysis_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"JSON load failed: {e}")
    
    return None


def get_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get analysis history."""
    client, db = get_mongo_client()
    
    if db is not None:
        try:
            cursor = db["analyses"].find().sort("created_at", -1).limit(limit)
            return [
                {k: v for k, v in doc.items() if k != "_id"}
                for doc in cursor
            ]
        except Exception as e:
            logger.error(f"MongoDB history failed: {e}")
    
    # JSON fallback
    try:
        storage = get_storage_path()
        if not storage.exists():
            return []
        files = sorted(storage.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        history = []
        for f in files[:limit]:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    data["analysis_id"] = f.stem
                    history.append(data)
            except Exception:
                pass
        return history
    except Exception as e:
        logger.error(f"JSON history failed: {e}")
        return []
