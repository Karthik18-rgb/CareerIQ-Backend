"""
Analysis service — orchestrates resume upload, PDF extraction, Gemini AI, and persistence.
"""

import json
import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisResponse, AnalysisListResponse
from app.services.gemini_service import analyse_resume
from app.utils.pdf_extractor import extract_text_from_pdf

logger = logging.getLogger(__name__)


def _analysis_to_response(a: Analysis) -> AnalysisResponse:
    return AnalysisResponse(
        id=a.id,
        job_title=a.job_title,
        company=a.company,
        job_description=a.job_description,
        resume_filename=a.resume_filename,
        ats_score=a.ats_score,
        ats_breakdown=json.loads(a.ats_breakdown) if a.ats_breakdown else None,
        missing_skills=json.loads(a.missing_skills) if a.missing_skills else None,
        resume_suggestions=json.loads(a.resume_suggestions) if a.resume_suggestions else None,
        cover_letter=a.cover_letter,
        interview_questions=json.loads(a.interview_questions) if a.interview_questions else None,
        hr_questions=json.loads(a.hr_questions) if a.hr_questions else None,
        technical_questions=json.loads(a.technical_questions) if a.technical_questions else None,
        career_suggestions=json.loads(a.career_suggestions) if a.career_suggestions else None,
        learning_roadmap=json.loads(a.learning_roadmap) if a.learning_roadmap else None,
        skill_gap_analysis=a.skill_gap_analysis,
        created_at=a.created_at,
    )


def _save_upload(file_bytes: bytes, filename: str) -> str:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = upload_dir / unique_name
    file_path.write_bytes(file_bytes)
    logger.info("Saved uploaded file to %s", file_path)
    return str(file_path)


def create_analysis(
    db: Session,
    user_id: str,
    file_bytes: bytes,
    filename: str,
    job_title: str,
    company: str,
    job_description: str,
) -> AnalysisResponse:
    if not filename.lower().endswith(".pdf"):
        raise BadRequestException("Only PDF files are supported.")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise BadRequestException(f"File size exceeds the maximum of {settings.MAX_UPLOAD_SIZE_MB} MB.")

    file_path = _save_upload(file_bytes, filename)

    try:
        resume_text = extract_text_from_pdf(file_path)
    except ValueError as e:
        Path(file_path).unlink(missing_ok=True)
        raise BadRequestException(str(e))

    try:
        (ats_score, ats_breakdown, missing_skills, resume_suggestions,
         cover_letter, interview_questions, hr_questions, technical_questions,
         career_suggestions, learning_roadmap, skill_gap_analysis) = analyse_resume(
            resume_text=resume_text,
            job_title=job_title or "",
            company=company or "",
            job_description=job_description,
        )
    except ValueError as e:
        Path(file_path).unlink(missing_ok=True)
        raise BadRequestException(str(e))

    analysis = Analysis(
        user_id=user_id,
        job_title=job_title,
        company=company,
        job_description=job_description,
        resume_filename=filename,
        resume_text=resume_text,
        ats_score=ats_score,
        ats_breakdown=json.dumps(ats_breakdown),
        missing_skills=json.dumps(missing_skills),
        resume_suggestions=json.dumps(resume_suggestions),
        cover_letter=cover_letter,
        interview_questions=json.dumps(interview_questions),
        hr_questions=json.dumps(hr_questions),
        technical_questions=json.dumps(technical_questions),
        career_suggestions=json.dumps(career_suggestions),
        learning_roadmap=json.dumps(learning_roadmap),
        skill_gap_analysis=skill_gap_analysis,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    logger.info("Analysis created: id=%s for user=%s", analysis.id, user_id)
    return _analysis_to_response(analysis)


def get_user_analyses(db: Session, user_id: str, skip: int = 0, limit: int = 20) -> AnalysisListResponse:
    total = db.query(Analysis).filter(Analysis.user_id == user_id).count()
    rows = (
        db.query(Analysis)
        .filter(Analysis.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return AnalysisListResponse(analyses=[_analysis_to_response(a) for a in rows], total=total)


def get_analysis_by_id(db: Session, analysis_id: str, user_id: str) -> AnalysisResponse:
    a = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user_id).first()
    if not a:
        raise NotFoundException("Analysis not found")
    return _analysis_to_response(a)


def delete_analysis(db: Session, analysis_id: str, user_id: str) -> None:
    a = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user_id).first()
    if not a:
        raise NotFoundException("Analysis not found")
    db.delete(a)
    db.commit()
    logger.info("Analysis deleted: id=%s", analysis_id)
