"""
Career Pathway Tool — generates structured, personalised career pathway
suggestions by matching a student's academic strengths and interests
against known career fields.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

# ---------------------------------------------------------------------------
# Subject → career field affinity map (self-contained, no external calls)
# ---------------------------------------------------------------------------
_SUBJECT_AFFINITIES: dict[str, List[str]] = {
    "mathematics": ["artificial intelligence", "data science", "finance", "engineering"],
    "physics": ["engineering", "renewable energy", "aerospace", "cloud computing"],
    "chemistry": ["healthcare", "pharmaceutical", "renewable energy", "materials science"],
    "biology": ["healthcare", "biotechnology", "environmental science"],
    "computer science": ["artificial intelligence", "cybersecurity", "cloud computing", "data science"],
    "statistics": ["data science", "finance", "artificial intelligence"],
    "economics": ["finance", "data science", "consulting"],
    "art": ["ux design", "game design", "animation", "architecture"],
    "design": ["ux design", "product design", "architecture"],
    "english": ["content writing", "marketing", "journalism", "law"],
    "history": ["law", "teaching", "public policy", "journalism"],
    "psychology": ["human resources", "ux design", "marketing", "counselling"],
    "business studies": ["finance", "entrepreneurship", "marketing", "consulting"],
}

_INTEREST_AFFINITIES: dict[str, List[str]] = {
    "coding": ["artificial intelligence", "cybersecurity", "cloud computing", "data science"],
    "design": ["ux design", "product design", "game design"],
    "helping people": ["healthcare", "teaching", "social work", "counselling"],
    "environment": ["renewable energy", "environmental science", "sustainability"],
    "problem solving": ["engineering", "data science", "artificial intelligence"],
    "communication": ["marketing", "journalism", "public relations"],
    "numbers": ["finance", "data science", "accounting"],
    "technology": ["artificial intelligence", "cloud computing", "cybersecurity"],
    "creativity": ["ux design", "game design", "content creation"],
    "science": ["healthcare", "research", "biotechnology"],
    "leadership": ["management", "entrepreneurship", "consulting"],
    "security": ["cybersecurity", "government", "defense"],
}


def _score_fields(subjects: List[dict], interests: List[str]) -> List[tuple]:
    """Score career fields based on academic performance + interests."""
    scores: dict[str, float] = {}

    for s in subjects:
        subj_key = s["subject"].lower()
        weight = s["score"] / 100.0  # normalise to 0-1
        for field in _SUBJECT_AFFINITIES.get(subj_key, []):
            scores[field] = scores.get(field, 0) + weight * 2  # subjects weighted x2

    for interest in interests:
        int_key = interest.lower()
        for field in _INTEREST_AFFINITIES.get(int_key, []):
            scores[field] = scores.get(field, 0) + 1.0

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class PathwayInput(BaseModel):
    """Input for generating career pathway suggestions."""

    student_name: str = Field(..., description="Student's full name.")
    subjects: List[dict] = Field(
        ...,
        description=(
            "List of subject dicts with keys 'subject' (str) and 'score' (float 0-100). "
            "E.g. [{'subject': 'Mathematics', 'score': 88.0}]"
        ),
    )
    interests: List[str] = Field(
        ...,
        description="Student's interests, e.g. ['coding', 'design', 'biology'].",
    )
    top_n: int = Field(
        default=3, ge=1, le=5, description="Number of top pathways to return (1–5)."
    )
    preferred_work_style: Optional[str] = Field(
        default=None,
        description="'collaborative', 'independent', or 'mixed'.",
    )


class CareerPathway(BaseModel):
    """A single career pathway recommendation."""

    rank: int = Field(..., description="Rank of this pathway (1 = best match).")
    field: str = Field(..., description="Career field name.")
    match_score: float = Field(..., description="Affinity score (higher = better match).")
    rationale: str = Field(..., description="Why this field suits the student.")
    first_steps: List[str] = Field(
        ..., description="Actionable first steps the student should take now."
    )


class PathwayOutput(BaseModel):
    """Output containing ranked career pathway suggestions."""

    student_name: str = Field(..., description="Student's name.")
    recommended_pathways: List[CareerPathway] = Field(
        ..., description="Ranked list of career pathway recommendations."
    )
    summary: str = Field(..., description="Short overall guidance summary.")


_FIRST_STEPS_MAP: dict[str, List[str]] = {
    "artificial intelligence": [
        "Complete Andrew Ng's Machine Learning Specialisation on Coursera.",
        "Build 2–3 end-to-end ML projects and publish on GitHub.",
        "Join IBM AI Student community and participate in hackathons.",
    ],
    "data science": [
        "Learn Python and SQL through free IBM SkillsBuild courses.",
        "Participate in Kaggle competitions to build a portfolio.",
        "Earn the IBM Data Science Professional Certificate.",
    ],
    "cybersecurity": [
        "Start with CompTIA Security+ or IBM Cybersecurity Analyst Certificate.",
        "Set up a home lab with Kali Linux and practice ethical hacking.",
        "Join Capture The Flag (CTF) competitions.",
    ],
    "cloud computing": [
        "Earn AWS Cloud Practitioner or IBM Cloud Essentials badge.",
        "Build and deploy a web app to the cloud.",
        "Learn DevOps basics: Docker, Kubernetes, and CI/CD pipelines.",
    ],
    "healthcare": [
        "Shadow a doctor or healthcare professional for one week.",
        "Prepare rigorously for medical entrance examinations.",
        "Volunteer at a local clinic or hospital.",
    ],
    "ux design": [
        "Learn Figma (free tier) and complete a UI design course.",
        "Redesign 3 existing apps and add them to a portfolio.",
        "Study Nielsen Norman Group UX guidelines.",
    ],
    "finance": [
        "Start with CFA Institute's free investment fundamentals course.",
        "Build a personal stock portfolio tracker using Excel.",
        "Network with finance professionals on LinkedIn.",
    ],
    "renewable energy": [
        "Study IEEE resources on solar and wind energy basics.",
        "Join your school's environmental club or sustainability committee.",
        "Intern with a local renewable energy company during summer.",
    ],
}

_DEFAULT_STEPS = [
    "Research the field thoroughly using industry reports.",
    "Connect with professionals in the field via LinkedIn.",
    "Find and enrol in an introductory online course.",
]


# Ensure Pydantic v2 models are fully built before @tool decorator runs
PathwayInput.model_rebuild()
CareerPathway.model_rebuild()
PathwayOutput.model_rebuild()


@tool(permission=ToolPermission.READ_ONLY)
def generate_career_pathways(input: PathwayInput) -> PathwayOutput:
    """
    Analyse a student's academic subject scores and personal interests to
    generate ranked, personalised career pathway recommendations with
    actionable next steps.

    Args:
        input (PathwayInput): Student data including subjects, scores, and interests.

    Returns:
        PathwayOutput: Ranked career pathways with rationale and first steps.
    """
    scored = _score_fields(input.subjects, input.interests)

    pathways: List[CareerPathway] = []
    for rank, (field, score) in enumerate(scored[: input.top_n], start=1):
        # Build a rationale sentence
        matching_subjects = [
            s["subject"]
            for s in input.subjects
            if s["subject"].lower() in _SUBJECT_AFFINITIES
            and field in _SUBJECT_AFFINITIES.get(s["subject"].lower(), [])
        ]
        matching_interests = [
            i for i in input.interests
            if field in _INTEREST_AFFINITIES.get(i.lower(), [])
        ]

        rationale_parts = []
        if matching_subjects:
            rationale_parts.append(
                f"strong performance in {', '.join(matching_subjects)}"
            )
        if matching_interests:
            rationale_parts.append(
                f"interests in {', '.join(matching_interests)}"
            )

        rationale = (
            f"{input.student_name}'s {' and '.join(rationale_parts)} align well with "
            f"a career in {field.title()}."
            if rationale_parts
            else f"{field.title()} is a strong fit based on overall profile."
        )

        steps = _FIRST_STEPS_MAP.get(field, _DEFAULT_STEPS)

        pathways.append(
            CareerPathway(
                rank=rank,
                field=field.title(),
                match_score=round(score, 2),
                rationale=rationale,
                first_steps=steps,
            )
        )

    if not pathways:
        return PathwayOutput(
            student_name=input.student_name,
            recommended_pathways=[],
            summary=(
                "Insufficient data to generate pathways. "
                "Please provide subject scores and interests."
            ),
        )

    top_field = pathways[0].field
    summary = (
        f"Based on {input.student_name}'s academic profile and interests, "
        f"{top_field} is the strongest career match, "
        f"followed by {', '.join(p.field for p in pathways[1:])}. "
        "Review the first steps for each pathway and discuss with your counsellor."
    )

    return PathwayOutput(
        student_name=input.student_name,
        recommended_pathways=pathways,
        summary=summary,
    )
