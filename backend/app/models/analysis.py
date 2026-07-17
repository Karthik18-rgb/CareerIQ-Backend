"""
Analysis model — stores every resume analysis result with all AI fields.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=True)
    resume_filename = Column(String(255), nullable=False)
    resume_text = Column(Text, nullable=False)

    ats_score = Column(Float, nullable=True)
    ats_breakdown = Column(Text, nullable=True)          # JSON

    missing_skills = Column(Text, nullable=True)          # JSON
    resume_suggestions = Column(Text, nullable=True)      # JSON
    cover_letter = Column(Text, nullable=True)
    interview_questions = Column(Text, nullable=True)     # JSON

    # New enhanced AI fields
    hr_questions = Column(Text, nullable=True)            # JSON
    technical_questions = Column(Text, nullable=True)     # JSON
    career_suggestions = Column(Text, nullable=True)      # JSON
    learning_roadmap = Column(Text, nullable=True)        # JSON
    skill_gap_analysis = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="analyses")

    def __repr__(self):
        return f"<Analysis(id={self.id}, user_id={self.user_id}, ats_score={self.ats_score})>"
