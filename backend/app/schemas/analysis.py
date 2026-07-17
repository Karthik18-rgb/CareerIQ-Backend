"""
Pydantic schemas for resume analysis — includes all AI result fields.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    job_title: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    job_description: str = Field(..., description="Full job description text")


class AnalysisResponse(BaseModel):
    """All fields from the analysis, including enhanced AI results."""
    id: str
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None
    resume_filename: str
    ats_score: Optional[float] = None
    ats_breakdown: Optional[Dict[str, Any]] = None
    missing_skills: Optional[List[str]] = None
    resume_suggestions: Optional[List[str]] = None
    cover_letter: Optional[str] = None
    interview_questions: Optional[List[str]] = None
    hr_questions: Optional[List[str]] = None
    technical_questions: Optional[List[str]] = None
    career_suggestions: Optional[List[str]] = None
    learning_roadmap: Optional[List[str]] = None
    skill_gap_analysis: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    analyses: List[AnalysisResponse]
    total: int


class ATSResult(BaseModel):
    ats_score: float = Field(..., ge=0, le=100)
    ats_breakdown: Dict[str, Any]
    missing_skills: List[str]
    resume_suggestions: List[str]
    cover_letter: str
    interview_questions: List[str]
    hr_questions: List[str]
    technical_questions: List[str]
    career_suggestions: List[str]
    learning_roadmap: List[str]
    skill_gap_analysis: str
