"""
Analysis API router — resume upload, AI analysis, history.
"""

import logging

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile, Query
from sqlalchemy.orm import Session

from app.auth.service import get_current_user
from app.core.exceptions import UnauthorizedException
from app.database.connection import get_db
from app.models.user import User
from app.schemas.analysis import AnalysisListResponse, AnalysisResponse
from app.services.analysis_service import (
    create_analysis,
    delete_analysis,
    get_analysis_by_id,
    get_user_analyses,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


def _resolve_user(authorization: str, db: Session) -> User:
    """Extract and validate the current user from the Authorization header."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedException("Invalid authorization header format")
    return get_current_user(db=db, token=token)


@router.post("/upload", response_model=AnalysisResponse, status_code=201)
def upload_and_analyse(
    file: UploadFile = File(..., description="Resume PDF"),
    job_title: str = Form("", description="Job title"),
    company: str = Form("", description="Company name"),
    job_description: str = Form(..., description="Full job description"),
    authorization: str = Header(..., description="Bearer <access_token>"),
    db: Session = Depends(get_db),
):
    """
    Upload a resume PDF, provide a job description, and get AI-powered analysis.
    """
    user = _resolve_user(authorization, db)
    file_bytes = file.file.read()
    result = create_analysis(
        db=db,
        user_id=user.id,
        file_bytes=file_bytes,
        filename=file.filename or "resume.pdf",
        job_title=job_title,
        company=company,
        job_description=job_description,
    )
    return result


@router.get("/history", response_model=AnalysisListResponse)
def list_analyses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    authorization: str = Header(..., description="Bearer <access_token>"),
    db: Session = Depends(get_db),
):
    """Get paginated analysis history for the authenticated user."""
    user = _resolve_user(authorization, db)
    return get_user_analyses(db=db, user_id=user.id, skip=skip, limit=limit)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str,
    authorization: str = Header(..., description="Bearer <access_token>"),
    db: Session = Depends(get_db),
):
    """Get a single analysis by ID."""
    user = _resolve_user(authorization, db)
    return get_analysis_by_id(db=db, analysis_id=analysis_id, user_id=user.id)


@router.delete("/{analysis_id}", status_code=204)
def remove_analysis(
    analysis_id: str,
    authorization: str = Header(..., description="Bearer <access_token>"),
    db: Session = Depends(get_db),
):
    """Delete an analysis record."""
    user = _resolve_user(authorization, db)
    delete_analysis(db=db, analysis_id=analysis_id, user_id=user.id)
