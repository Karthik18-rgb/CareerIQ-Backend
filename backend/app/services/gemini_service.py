"""
Gemini AI service for comprehensive resume analysis.
Produces ATS score, missing skills, suggestions, cover letter,
interview questions, strengths/weaknesses, keyword suggestions,
career suggestions, learning roadmap, and skill gap analysis.

Gracefully handles missing API key by returning demo data.
"""

import json
import logging
from typing import Any, Dict, List, Tuple

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Only configure Gemini if API key is available
_has_gemini = bool(settings.GEMINI_API_KEY)
_model = None

if _has_gemini:
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    _model = genai.GenerativeModel(settings.GEMINI_MODEL)
    logger.info("Gemini AI configured with model: %s", settings.GEMINI_MODEL)
else:
    logger.warning("GEMINI_API_KEY not set — AI analysis will return demo data")

SYSTEM_PROMPT = """You are an expert ATS analyst, career coach, and HR strategist.
Analyse the provided RESUME against the JOB DESCRIPTION and return ONLY valid JSON with these keys:

1. `ats_score` — float 0-100 overall match.
2. `ats_breakdown` — object with:
   - `keyword_match` (0-100)
   - `skills_alignment` (0-100)
   - `experience_relevance` (0-100)
   - `format_quality` (0-100)
   - `strengths` — list of 2-3 resume strengths
   - `weaknesses` — list of 2-3 resume weaknesses
   - `keyword_suggestions` — list of 5-10 keywords to add
3. `missing_skills` — list of important skills from the JD absent/weak in the resume.
4. `resume_suggestions` — list of 5 actionable improvement tips.
5. `cover_letter` — full professional cover letter (3-4 paragraphs).
6. `interview_questions` — list of 5 likely interview questions.
7. `hr_questions` — list of 3 HR-specific questions.
8. `technical_questions` — list of 3 role-specific technical questions.
9. `career_suggestions` — list of 3 career growth suggestions.
10. `learning_roadmap` — list of 5 learning steps to close the skill gap.
11. `skill_gap_analysis` — string summarising the gap between current and required skills.

Return ONLY valid JSON. No markdown, no code fences."""


def _demo_result() -> Tuple[float, Dict[str, Any], List[str], List[str], str, List[str], List[str], List[str], List[str], List[str], str]:
    """Return realistic demo data when Gemini is unavailable."""
    return (
        78.5,
        {
            "keyword_match": 72,
            "skills_alignment": 80,
            "experience_relevance": 75,
            "format_quality": 85,
            "strengths": ["Strong technical background", "Clear career progression"],
            "weaknesses": ["Missing some keywords", "Format could be improved"],
            "keyword_suggestions": ["Kubernetes", "AWS", "Microservices", "CI/CD", "Terraform"],
        },
        ["Kubernetes", "AWS Lambda", "Microservices Architecture"],
        ["Add quantifiable achievements", "Include a professional summary", "Use more action verbs", "Tailor skills to job description", "Add links to portfolio/work"],
        "Dear Hiring Manager,\n\nI am writing to express my strong interest in the position. With my background in software engineering and a proven track record of delivering results, I am confident that my skills align well with the requirements of this role.\n\nThroughout my career, I have focused on building scalable systems and leading cross-functional teams. My experience includes designing microservices architectures, implementing CI/CD pipelines, and mentoring junior developers.\n\nI am particularly excited about this opportunity because it combines my passion for technology with my desire to solve meaningful problems. I look forward to the possibility of contributing to your team.\n\nBest regards,\nCandidate",
        ["Tell me about yourself", "Why do you want this role?", "Describe a challenging project you worked on", "How do you handle tight deadlines?", "Where do you see yourself in 5 years?"],
        ["What are your salary expectations?", "Why are you leaving your current role?", "What is your availability to start?"],
        ["Explain REST APIs and how they work", "How would you design a scalable system?", "Describe your experience with cloud infrastructure"],
        ["Consider cloud certifications (AWS/Azure/GCP)", "Build a portfolio project showcasing your skills", "Network with industry professionals"],
        ["Learn Docker & Kubernetes", "Study system design patterns", "Practice coding interviews on LeetCode", "Contribute to open source projects", "Take a course on cloud architecture"],
        "Your resume shows strong fundamentals but could benefit from more cloud-native technologies and quantifiable achievements.",
    )


def _build_prompt(resume_text: str, job_title: str, company: str, job_description: str) -> str:
    parts = [SYSTEM_PROMPT, "\n\n--- JOB DETAILS ---"]
    if job_title:
        parts.append(f"Job Title: {job_title}")
    if company:
        parts.append(f"Company: {company}")
    parts.extend([
        f"\n--- JOB DESCRIPTION ---\n{job_description}",
        f"\n--- RESUME ---\n{resume_text}",
    ])
    return "\n".join(parts)


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0].strip()
    if raw.startswith("json"):
        raw = raw[4:].strip()
    return raw


def analyse_resume(
    resume_text: str,
    job_title: str = "",
    company: str = "",
    job_description: str = "",
) -> Tuple[float, Dict[str, Any], List[str], List[str], str, List[str], List[str], List[str], List[str], List[str], str]:
    """
    Full AI analysis returning all 11 result fields.
    Falls back to demo data if Gemini API key is not configured.
    """
    if not _has_gemini:
        logger.info("Gemini not configured — returning demo analysis data")
        return _demo_result()

    prompt = _build_prompt(resume_text, job_title, company, job_description)

    try:
        logger.info("Gemini prompt length=%d chars", len(prompt))
        response = _model.generate_content(prompt)
        raw = _clean_json(response.text)
        data = json.loads(raw)

        ats_score = float(data.get("ats_score", 0))
        ats_breakdown = data.get("ats_breakdown", {})
        missing_skills = data.get("missing_skills", [])
        resume_suggestions = data.get("resume_suggestions", [])
        cover_letter = data.get("cover_letter", "")
        interview_questions = data.get("interview_questions", [])
        hr_questions = data.get("hr_questions", [])
        technical_questions = data.get("technical_questions", [])
        career_suggestions = data.get("career_suggestions", [])
        learning_roadmap = data.get("learning_roadmap", [])
        skill_gap_analysis = data.get("skill_gap_analysis", "")

        logger.info("ATS=%.1f skills=%d questions=%d", ats_score, len(missing_skills), len(interview_questions))

        return (
            ats_score, ats_breakdown, missing_skills, resume_suggestions,
            cover_letter, interview_questions, hr_questions, technical_questions,
            career_suggestions, learning_roadmap, skill_gap_analysis,
        )
    except json.JSONDecodeError as e:
        logger.error("Gemini JSON error: %s — raw: %s", e, raw[:300])
        raise ValueError("AI returned an invalid format. Try again.")
    except Exception as e:
        logger.error("Gemini API error: %s — falling back to demo data", str(e))
        return _demo_result()
