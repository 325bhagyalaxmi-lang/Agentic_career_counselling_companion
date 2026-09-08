"""
Skill Gap Coaching Flow — takes a target career field and a student's
current skills, performs a gap analysis, and uses IBM Granite to
generate a personalised study roadmap.

Flow: START → analyse_gap (LLM prompt) → END
"""
from typing import Optional
from pydantic import BaseModel, Field

from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class SkillGapFlowInput(BaseModel):
    """Input for the skill gap coaching flow."""

    student_name: str = Field(..., description="Student's full name.")
    target_career_field: str = Field(
        ...,
        description=(
            "The career field the student wants to enter, "
            "e.g. 'artificial intelligence', 'cybersecurity', 'healthcare'."
        ),
    )
    current_skills: str = Field(
        ...,
        description=(
            "Comma-separated list of skills the student currently has, "
            "e.g. 'Python, SQL, Statistics'."
        ),
    )
    timeline_months: Optional[int] = Field(
        default=6,
        description="How many months the student has to close the skill gap (default 6).",
    )
    learning_hours_per_week: Optional[int] = Field(
        default=10,
        description="Available study hours per week (default 10).",
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="skill_gap_coaching_flow",
    display_name="Skill Gap Coaching Flow",
    description=(
        "Analyses the gap between a student's current skills and the target career "
        "requirements, then generates a personalised study roadmap using IBM Granite."
    ),
    input_schema=SkillGapFlowInput,
)
def build_skill_gap_coaching_flow(aflow: Flow) -> Flow:
    """
    Build the skill gap coaching flow.

    Steps:
    1. IBM Granite LLM produces a detailed, time-boxed skill gap study plan.

    Args:
        aflow (Flow): The flow builder instance.

    Returns:
        Flow: Configured flow ready for deployment.
    """

    coaching_node = aflow.prompt(
        name="generate_skill_roadmap",
        system_prompt=[
            "You are a world-class career coach and curriculum designer powered by IBM Granite. "
            "You specialise in creating practical, achievable study roadmaps for students "
            "transitioning into technology and knowledge-economy careers. "
            "Structure your roadmap with: "
            "1) Current Skill Assessment, "
            "2) Gap Analysis (skills missing), "
            "3) Month-by-month study plan, "
            "4) Free and affordable resources for each skill, "
            "5) Milestone checkpoints, "
            "6) Motivational advice. "
            "Be specific, realistic, and encouraging."
        ],
        user_prompt=[
            "Create a personalised skill gap study roadmap for:\n"
            "Student: {student_name}\n"
            "Target Career Field: {target_career_field}\n"
            "Current Skills: {current_skills}\n"
            "Available Timeline: {timeline_months} months\n"
            "Study Hours per Week: {learning_hours_per_week} hours\n\n"
            "Generate a detailed, actionable study roadmap to close the skill gap."
        ],
        llm="groq/openai/gpt-oss-120b",
        input_schema=SkillGapFlowInput,
    )

    aflow.sequence(START, coaching_node, END)
    return aflow
