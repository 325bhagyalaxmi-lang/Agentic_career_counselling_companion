"""
Career Assessment Flow — collects student academic data, generates
career pathway suggestions, and enriches them with live market trends.

Flow: START → save_profile → generate_pathways → enrich_with_market_data
         → synthesise_report (Granite LLM prompt) → END
"""
from pydantic import BaseModel, Field
from typing import List, Optional

from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class AssessmentInput(BaseModel):
    """Input schema for the career assessment flow."""

    student_id: str = Field(..., description="Unique student identifier.")
    student_name: str = Field(..., description="Student's full name.")
    age: int = Field(..., description="Student's age.")
    current_grade: str = Field(..., description="e.g. '11th Grade' or 'Year 2 Undergraduate'.")
    subjects_json: str = Field(
        ...,
        description=(
            "JSON array of subject objects. Each object must have 'subject' (string) "
            "and 'score' (number 0-100). "
            "Example: [{\"subject\": \"Mathematics\", \"score\": 92}, "
            "{\"subject\": \"Computer Science\", \"score\": 88}]"
        ),
    )
    interests: str = Field(
        ...,
        description="Comma-separated list of interests, e.g. 'coding, design, biology'.",
    )
    current_skills: Optional[str] = Field(
        default="",
        description="Comma-separated list of current skills, e.g. 'Python, SQL'.",
    )
    preferred_work_style: Optional[str] = Field(
        default="mixed",
        description="Work style preference: 'collaborative', 'independent', or 'mixed'.",
    )


# ---------------------------------------------------------------------------
# Helper tool (self-contained — called inside the flow as a tool node)
# ---------------------------------------------------------------------------
class AssessmentHelperInput(BaseModel):
    """Input for the assessment preparation helper."""
    student_name: str = Field(..., description="Student's name.")
    interests: str = Field(..., description="Comma-separated interests string.")


class AssessmentHelperOutput(BaseModel):
    """Cleaned output from the assessment helper."""
    greeting: str = Field(..., description="Greeting message for the student.")
    interests_list: List[str] = Field(..., description="Parsed list of interests.")


@tool(permission=ToolPermission.READ_ONLY)
def prepare_assessment(input: AssessmentHelperInput) -> AssessmentHelperOutput:
    """
    Prepare the career assessment session by parsing the student's
    interests and generating a personalised greeting.

    Args:
        input (AssessmentHelperInput): Student name and raw interests string.

    Returns:
        AssessmentHelperOutput: Greeting text and parsed interests list.
    """
    interests_list = [i.strip() for i in input.interests.split(",") if i.strip()]
    greeting = (
        f"Hello {input.student_name}! Welcome to your personalised career assessment. "
        f"I can see you're interested in: {', '.join(interests_list)}. "
        "Let me analyse your profile and suggest the best career pathways for you."
    )
    return AssessmentHelperOutput(greeting=greeting, interests_list=interests_list)


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="career_assessment_flow",
    display_name="Career Assessment Flow",
    description=(
        "End-to-end career counselling flow: collects student profile, "
        "analyses academic strengths and interests, retrieves market trends, "
        "and uses IBM Granite to produce a personalised career report."
    ),
    input_schema=AssessmentInput,
)
def build_career_assessment_flow(aflow: Flow) -> Flow:
    """
    Build the career assessment flow.

    Steps:
    1. prepare_assessment — parse inputs and greet the student
    2. LLM prompt node — use IBM Granite to synthesise a holistic career report

    Args:
        aflow (Flow): The flow builder instance.

    Returns:
        Flow: Configured flow ready for deployment.
    """

    # Step 1: Prepare assessment (parse interests, generate greeting)
    prepare_node = aflow.tool(prepare_assessment)

    # Step 2: Granite LLM synthesises the career counselling report
    report_node = aflow.prompt(
        name="synthesise_career_report",
        system_prompt=[
            "You are an expert career counsellor powered by IBM Granite. "
            "Your role is to provide empathetic, data-driven, personalised career guidance "
            "to students. Always be encouraging, practical, and specific. "
            "Structure your response with clear sections: "
            "1) Overview of the student's strengths, "
            "2) Top 3 recommended career pathways with rationale, "
            "3) Immediate next steps for each pathway, "
            "4) Market outlook for top recommendation, "
            "5) Motivational closing message."
        ],
        user_prompt=[
            "Please provide a comprehensive career counselling report for:\n"
            "Student: {student_name}\n"
            "Age: {age}\n"
            "Grade: {current_grade}\n"
            "Subjects & Scores (JSON): {subjects_json}\n"
            "Interests: {interests}\n"
            "Current Skills: {current_skills}\n"
            "Preferred Work Style: {preferred_work_style}\n\n"
            "Generate a personalised, actionable career guidance report."
        ],
        llm="groq/openai/gpt-oss-120b",
        input_schema=AssessmentInput,
    )

    aflow.sequence(START, prepare_node, report_node, END)
    return aflow
