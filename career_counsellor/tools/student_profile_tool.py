"""
Student Profile Tool — captures, stores (in-memory), and retrieves
a student's academic performance, interests, and learning style.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

# ---------------------------------------------------------------------------
# Simple in-process store (resets per session — suitable for demo use)
# ---------------------------------------------------------------------------
_PROFILES: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class SubjectScore(BaseModel):
    """Score for a single academic subject."""

    subject: str = Field(..., description="Subject name, e.g. 'Mathematics'.")
    score: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage score (0–100)."
    )
    grade: Optional[str] = Field(
        default=None, description="Letter grade, e.g. 'A', 'B+'."
    )


class StudentProfileInput(BaseModel):
    """Input for creating or updating a student profile."""

    student_id: str = Field(..., description="Unique student identifier.")
    name: str = Field(..., description="Full name of the student.")
    age: int = Field(..., ge=10, le=30, description="Student's age.")
    current_grade: str = Field(
        ...,
        description="Current grade/class, e.g. '10th Grade', 'Undergraduate Year 2'.",
    )
    subjects: List[SubjectScore] = Field(
        ..., description="List of academic subject scores."
    )
    interests: List[str] = Field(
        ...,
        description=(
            "Student's stated interests, e.g. ['coding', 'design', 'biology']."
        ),
    )
    preferred_work_style: Optional[str] = Field(
        default=None,
        description=(
            "Preferred work style: 'collaborative', 'independent', or 'mixed'."
        ),
    )
    career_aspirations: Optional[List[str]] = Field(
        default=None,
        description="Any career roles the student has already considered.",
    )


class StudentProfileOutput(BaseModel):
    """Result after storing the student profile."""

    student_id: str = Field(..., description="The student ID that was stored.")
    message: str = Field(..., description="Confirmation message.")
    top_subjects: List[str] = Field(
        ..., description="Top 3 subjects by score for quick reference."
    )


class ProfileLookupInput(BaseModel):
    """Input to retrieve a stored student profile."""

    student_id: str = Field(..., description="Unique student identifier to look up.")


class ProfileLookupOutput(BaseModel):
    """The retrieved student profile."""

    found: bool = Field(..., description="Whether the profile was found.")
    profile_summary: str = Field(
        ..., description="Human-readable summary of the student profile."
    )


# Ensure Pydantic v2 models are fully built before @tool decorators run
SubjectScore.model_rebuild()
StudentProfileInput.model_rebuild()
StudentProfileOutput.model_rebuild()
ProfileLookupInput.model_rebuild()
ProfileLookupOutput.model_rebuild()


@tool(permission=ToolPermission.READ_WRITE)
def save_student_profile(input: StudentProfileInput) -> StudentProfileOutput:
    """
    Save or update a student's academic profile including subjects, scores,
    interests, and career aspirations. Call this at the beginning of a
    counselling session.

    Args:
        input (StudentProfileInput): Full student profile data.

    Returns:
        StudentProfileOutput: Confirmation with top-performing subjects.
    """
    _PROFILES[input.student_id] = input.model_dump()

    sorted_subjects = sorted(
        input.subjects, key=lambda s: s.score, reverse=True
    )
    top_three = [s.subject for s in sorted_subjects[:3]]

    return StudentProfileOutput(
        student_id=input.student_id,
        message=f"Profile saved successfully for {input.name}.",
        top_subjects=top_three,
    )


@tool(permission=ToolPermission.READ_ONLY)
def get_student_profile(input: ProfileLookupInput) -> ProfileLookupOutput:
    """
    Retrieve a previously saved student profile by student ID.

    Args:
        input (ProfileLookupInput): Student ID to look up.

    Returns:
        ProfileLookupOutput: Human-readable profile summary or not-found message.
    """
    data = _PROFILES.get(input.student_id)
    if not data:
        return ProfileLookupOutput(
            found=False,
            profile_summary=f"No profile found for student ID '{input.student_id}'.",
        )

    subjects_str = ", ".join(
        f"{s['subject']} ({s['score']}%)" for s in data["subjects"]
    )
    interests_str = ", ".join(data.get("interests", []))
    aspirations_str = ", ".join(data.get("career_aspirations") or ["Not specified"])

    summary = (
        f"Student: {data['name']} (ID: {data['student_id']}), "
        f"Age: {data['age']}, Grade: {data['current_grade']}. "
        f"Subjects: {subjects_str}. "
        f"Interests: {interests_str}. "
        f"Career aspirations: {aspirations_str}."
    )
    return ProfileLookupOutput(found=True, profile_summary=summary)
