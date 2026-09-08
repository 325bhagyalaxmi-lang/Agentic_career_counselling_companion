"""
Skill Gap Analysis Tool — compares a student's current skills against
the requirements of a target career field and returns a structured gap report.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

# ---------------------------------------------------------------------------
# Required skills per career field
# ---------------------------------------------------------------------------
_REQUIRED_SKILLS: dict[str, List[str]] = {
    "artificial intelligence": [
        "Python", "Statistics", "Linear Algebra", "Machine Learning", "Deep Learning",
        "Data Wrangling", "SQL", "Version Control (Git)", "Cloud Basics",
    ],
    "data science": [
        "Python", "SQL", "Statistics", "Data Visualisation", "Excel",
        "Machine Learning Basics", "Communication", "Business Acumen",
    ],
    "cybersecurity": [
        "Networking Fundamentals", "Linux", "Python or Scripting",
        "Encryption Basics", "Risk Assessment", "Ethical Hacking Concepts",
        "Incident Response",
    ],
    "cloud computing": [
        "Linux", "Networking", "AWS/Azure/GCP Basics", "Docker", "Kubernetes",
        "CI/CD Pipelines", "Scripting (Bash/Python)", "Infrastructure as Code",
    ],
    "healthcare": [
        "Biology", "Chemistry", "Physics", "Empathy & Communication",
        "Medical Ethics", "Anatomy Basics", "Clinical Decision Making",
    ],
    "ux design": [
        "Figma", "User Research Methods", "Wireframing", "Prototyping",
        "Design Thinking", "Typography", "Usability Testing",
    ],
    "finance": [
        "Accounting Principles", "Excel / Spreadsheets", "Financial Modelling",
        "Economics", "Risk Analysis", "Statistics", "Communication",
    ],
    "renewable energy": [
        "Electrical Engineering Basics", "Physics", "Mathematics",
        "Energy Systems", "AutoCAD", "Project Management", "Environmental Science",
    ],
}


def _normalise(skill: str) -> str:
    return skill.lower().strip()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class SkillGapInput(BaseModel):
    """Input for skill gap analysis."""

    student_name: str = Field(..., description="Student's full name.")
    target_career_field: str = Field(
        ...,
        description=(
            "Target career field, e.g. 'artificial intelligence', "
            "'data science', 'cybersecurity', 'cloud computing', "
            "'healthcare', 'ux design', 'finance', 'renewable energy'."
        ),
    )
    current_skills: List[str] = Field(
        ...,
        description=(
            "Skills the student already has, e.g. "
            "['Python', 'Statistics', 'SQL']."
        ),
    )
    certifications: Optional[List[str]] = Field(
        default=None,
        description="Any certifications the student already holds.",
    )


class SkillGapOutput(BaseModel):
    """Result of the skill gap analysis."""

    student_name: str = Field(..., description="Student's name.")
    target_field: str = Field(..., description="The target career field.")
    skills_present: List[str] = Field(
        ..., description="Skills the student already has that match the target."
    )
    skills_missing: List[str] = Field(
        ..., description="Required skills the student still needs to develop."
    )
    readiness_percentage: float = Field(
        ..., description="Percentage of required skills already acquired (0–100)."
    )
    priority_learning_items: List[str] = Field(
        ...,
        description=(
            "Top 3 skills to focus on first, based on impact and frequency."
        ),
    )
    recommended_resources: List[str] = Field(
        ..., description="Free or low-cost learning resources for the missing skills."
    )
    overall_assessment: str = Field(
        ..., description="Short plain-English assessment of the student's readiness."
    )


_RESOURCES: dict[str, str] = {
    "Python": "IBM SkillsBuild — Python for Data Science (free)",
    "Machine Learning": "Coursera — Machine Learning Specialization by Andrew Ng",
    "SQL": "Mode Analytics SQL Tutorial (free)",
    "Statistics": "Khan Academy — Statistics & Probability (free)",
    "Networking Fundamentals": "Cisco NetAcad — Networking Basics (free)",
    "Linux": "Linux Foundation — Introduction to Linux (edX, free audit)",
    "Docker": "Play with Docker (free interactive labs)",
    "Kubernetes": "Kubernetes.io interactive tutorials (free)",
    "Figma": "Figma Design School (free)",
    "User Research Methods": "Nielsen Norman Group UX Research Methods (free articles)",
    "Financial Modelling": "CFI — Free Financial Modelling Courses",
    "Biology": "Khan Academy — Biology (free)",
    "Chemistry": "Khan Academy — Chemistry (free)",
    "Electrical Engineering Basics": "MIT OpenCourseWare — Circuits & Electronics (free)",
    "Deep Learning": "fast.ai — Practical Deep Learning for Coders (free)",
    "Data Visualisation": "Tableau Public Learning Resources (free)",
    "Cloud Basics": "IBM Cloud Essentials Badge (free on IBM SkillsBuild)",
    "Version Control (Git)": "GitHub Skills (free)",
    "Encryption Basics": "Cybrary — Encryption Fundamentals (free tier)",
    "Ethical Hacking Concepts": "TryHackMe — Learning Paths (freemium)",
    "Design Thinking": "IDEO Design Thinking online course (free)",
    "Usability Testing": "Nielsen Norman Group — free UX articles and guides",
    "AutoCAD": "Autodesk Design Academy (free student access)",
    "Project Management": "PMI — free introductory PM resources",
}

_DEFAULT_RESOURCE = "Search IBM SkillsBuild or Coursera for a free introductory course."


# Ensure Pydantic v2 models are fully built before @tool decorator runs
SkillGapInput.model_rebuild()
SkillGapOutput.model_rebuild()


@tool(permission=ToolPermission.READ_ONLY)
def analyse_skill_gap(input: SkillGapInput) -> SkillGapOutput:
    """
    Compare a student's current skills against those required for a target
    career field and return a prioritised gap analysis with actionable
    learning recommendations.

    Args:
        input (SkillGapInput): Student name, target field, and current skills.

    Returns:
        SkillGapOutput: Structured gap report with readiness score and resources.
    """
    field_key = input.target_career_field.lower().strip()
    required = _REQUIRED_SKILLS.get(field_key, [])

    # If not found, try partial match
    if not required:
        for key in _REQUIRED_SKILLS:
            if key in field_key or field_key in key:
                required = _REQUIRED_SKILLS[key]
                field_key = key
                break

    if not required:
        return SkillGapOutput(
            student_name=input.student_name,
            target_field=input.target_career_field,
            skills_present=[],
            skills_missing=[],
            readiness_percentage=0.0,
            priority_learning_items=[],
            recommended_resources=[
                "No data available for this field. "
                "Consult IBM SkillsBuild for relevant courses."
            ],
            overall_assessment=(
                f"Career field '{input.target_career_field}' is not in the database. "
                "Try: artificial intelligence, data science, cybersecurity, "
                "cloud computing, healthcare, ux design, finance, or renewable energy."
            ),
        )

    normalised_current = {_normalise(s) for s in input.current_skills}
    if input.certifications:
        normalised_current.update(_normalise(c) for c in input.certifications)

    present = [r for r in required if _normalise(r) in normalised_current]
    missing = [r for r in required if _normalise(r) not in normalised_current]

    readiness = round(len(present) / len(required) * 100, 1) if required else 0.0

    # Priority: first 3 missing skills
    priority = missing[:3]

    # Gather resources for missing skills
    resources = []
    for skill in missing:
        resource = _RESOURCES.get(skill, _DEFAULT_RESOURCE)
        resources.append(f"{skill}: {resource}")

    # Assessment text
    if readiness >= 80:
        assessment = (
            f"{input.student_name} is well-prepared for {field_key.title()} "
            f"with {readiness}% of required skills already acquired. "
            "Focus on the remaining gaps to be fully job-ready."
        )
    elif readiness >= 50:
        assessment = (
            f"{input.student_name} has a solid foundation ({readiness}% of required skills) "
            f"for {field_key.title()}. Dedicated effort on priority gaps will close the distance."
        )
    else:
        assessment = (
            f"{input.student_name} is at an early stage ({readiness}% of required skills) "
            f"for {field_key.title()}. A structured 6–12 month learning plan is recommended."
        )

    return SkillGapOutput(
        student_name=input.student_name,
        target_field=field_key.title(),
        skills_present=present,
        skills_missing=missing,
        readiness_percentage=readiness,
        priority_learning_items=priority,
        recommended_resources=resources,
        overall_assessment=assessment,
    )
