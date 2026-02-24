"""
FastAPI Backend - AI Resume ATS Scanner & Job Compatibility Analyzer
"""

import asyncio
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from utils import setup_logging, generate_analysis_id, ensure_directory
from parser_resume import parse_resume
from parser_jd import parse_job_description
from formatting_checker import check_formatting
from scoring_engine import compute_full_ats_analysis
from report_generator import generate_ats_report
from ai_enhancer import ai_enhance_resume
from database import save_analysis, load_analysis, get_history

# Load env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(
    title="AI Resume ATS Scanner",
    description="Resume ATS compatibility and job matching analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
REPORT_DIR = Path(__file__).parent.parent / "reports"

ensure_directory(UPLOAD_DIR)
ensure_directory(REPORT_DIR)


@app.get("/")
def root():
    return {"message": "AI Resume ATS Scanner API", "version": "1.0.0"}


@app.get("/health")
def health():
    """Quick health check - use to verify backend is running."""
    return {"status": "ok"}


@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload resume PDF and return parsed structured data."""
    if not file.filename.casefold().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")
    
    analysis_id = generate_analysis_id()
    resume_path = UPLOAD_DIR / f"{analysis_id}_resume.pdf"
    
    try:
        with open(resume_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        resume_data = parse_resume(str(resume_path))
        return {
            "analysis_id": analysis_id,
            "resume_data": resume_data,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        if resume_path.exists():
            resume_path.unlink()
        raise HTTPException(500, str(e))


@app.post("/upload_job_description")
async def upload_job_description(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    """Upload JD PDF or receive pasted text."""
    if file and file.filename:
        if not file.filename.casefold().endswith(".pdf"):
            raise HTTPException(400, "Only PDF files allowed for JD")
        analysis_id = generate_analysis_id()
        jd_path = UPLOAD_DIR / f"{analysis_id}_jd.pdf"
        with open(jd_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        jd_data = parse_job_description("", is_pdf=True, pdf_path=str(jd_path))
        return {"analysis_id": analysis_id, "jd_data": jd_data, "source": "pdf"}
    
    if text and text.strip():
        jd_data = parse_job_description(text.strip(), is_pdf=False)
        return {"jd_data": jd_data, "source": "text"}
    
    raise HTTPException(400, "Provide either JD file or pasted text")


def _run_analysis(resume_path: str, jd_path: str, jd_text: str, analysis_id: str):
    """Run heavy analysis in thread (blocking)."""
    resume_data = parse_resume(resume_path)
    
    if jd_path:
        jd_data = parse_job_description("", is_pdf=True, pdf_path=jd_path)
    else:
        jd_data = parse_job_description(jd_text.strip(), is_pdf=False)
    
    formatting = check_formatting(resume_path, resume_data)
    formatting_score = formatting["ats_formatting_score"]
    
    analysis_result = compute_full_ats_analysis(
        resume_data, jd_data, formatting_score=formatting_score
    )
    
    ai_enhancement = ai_enhance_resume(resume_data, jd_data, analysis_result)
    
    return {
        "analysis_id": analysis_id,
        "resume_data": resume_data,
        "jd_data": jd_data,
        **analysis_result,
        "formatting_issues": formatting.get("issues", []),
        "formatting_suggestions": formatting.get("suggestions", []),
        "ai_enhancement": ai_enhancement,
        "improvement_recommendations": (
            formatting.get("suggestions", []) +
            [f"Add: {s}" for s in analysis_result.get("skill_analysis", {}).get("missing_skills", [])[:5]]
        ),
        "created_at": datetime.now().isoformat()
    }


@app.post("/analyze")
async def analyze(
    resume_file: UploadFile = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Form(None)
):
    """
    Full analysis: upload resume + JD (file or text), get ATS score and report.
    Runs in thread pool - first run may take 1-3 min (model loading).
    """
    if not resume_file.filename.casefold().endswith(".pdf"):
        raise HTTPException(400, "Resume must be PDF")
    
    analysis_id = generate_analysis_id()
    resume_path = UPLOAD_DIR / f"{analysis_id}_resume.pdf"
    jd_path = None
    
    try:
        with open(resume_path, "wb") as f:
            shutil.copyfileobj(resume_file.file, f)
        
        if jd_file and jd_file.filename:
            jd_path = UPLOAD_DIR / f"{analysis_id}_jd.pdf"
            with open(jd_path, "wb") as f:
                shutil.copyfileobj(jd_file.file, f)
        elif not (jd_text and jd_text.strip()):
            raise HTTPException(400, "Provide job description (file or text)")
        
        logger.info(f"Starting analysis {analysis_id}...")
        
        # Run heavy work in thread pool to avoid blocking
        full_result = await asyncio.to_thread(
            _run_analysis,
            str(resume_path),
            str(jd_path) if jd_path else "",
            jd_text or "",
            analysis_id
        )
        
        save_analysis(analysis_id, full_result)
        logger.info(f"Analysis {analysis_id} complete.")
        
        return full_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        if resume_path.exists():
            resume_path.unlink()
        if jd_path and Path(jd_path).exists():
            Path(jd_path).unlink()
        raise HTTPException(500, str(e))


@app.get("/download_report/{analysis_id}")
async def download_report(analysis_id: str):
    """Download PDF report for given analysis."""
    data = load_analysis(analysis_id)
    if not data:
        raise HTTPException(404, "Analysis not found")
    
    try:
        pdf_bytes = generate_ats_report(data, output_path=None)
        report_path = REPORT_DIR / f"{analysis_id}_report.pdf"
        with open(report_path, "wb") as f:
            f.write(pdf_bytes)
        return FileResponse(
            report_path,
            media_type="application/pdf",
            filename=f"ATS_Report_{analysis_id}.pdf"
        )
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(500, str(e))


@app.get("/history")
def history(limit: int = 20):
    """Get analysis history."""
    items = get_history(limit=limit)
    return {"history": items[:limit]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
