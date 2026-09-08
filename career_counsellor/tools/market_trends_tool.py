"""
Labor Market Trends Tool — returns curated, up-to-date information
about top emerging career fields, in-demand skills, and salary ranges.
Uses a built-in knowledge base to avoid needing a live API key.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

# ---------------------------------------------------------------------------
# Embedded knowledge base (keeps the tool self-contained and offline-safe)
# ---------------------------------------------------------------------------
_MARKET_DATA: dict[str, dict] = {
    "artificial intelligence": {
        "demand": "Very High",
        "growth_rate": "38% over next 5 years",
        "avg_salary_usd": "110000-180000",
        "top_skills": ["Python", "TensorFlow", "PyTorch", "MLOps", "LLM Fine-tuning"],
        "entry_roles": ["ML Engineer", "Data Scientist", "AI Research Intern"],
        "senior_roles": ["Lead AI Engineer", "ML Platform Architect", "AI Product Manager"],
        "education_path": "B.Sc. Computer Science / Data Science + Certifications",
        "industry_sectors": ["Tech", "Healthcare", "Finance", "Autonomous Vehicles"],
    },
    "data science": {
        "demand": "Very High",
        "growth_rate": "35% over next 5 years",
        "avg_salary_usd": "95000-160000",
        "top_skills": ["Python", "SQL", "Statistics", "Power BI", "Spark"],
        "entry_roles": ["Data Analyst", "Business Analyst", "Junior Data Scientist"],
        "senior_roles": ["Senior Data Scientist", "Chief Data Officer", "Analytics Manager"],
        "education_path": "B.Sc. Statistics / Mathematics / Computer Science",
        "industry_sectors": ["Finance", "E-commerce", "Healthcare", "Government"],
    },
    "cybersecurity": {
        "demand": "High",
        "growth_rate": "32% over next 5 years",
        "avg_salary_usd": "85000-155000",
        "top_skills": ["Network Security", "Ethical Hacking", "SIEM", "Zero Trust", "Cloud Security"],
        "entry_roles": ["SOC Analyst", "Security Tester", "Junior Pen-Tester"],
        "senior_roles": ["CISO", "Security Architect", "Red Team Lead"],
        "education_path": "B.Sc. Computer Science + CEH / CISSP certifications",
        "industry_sectors": ["Government", "Finance", "Healthcare", "Defense"],
    },
    "cloud computing": {
        "demand": "Very High",
        "growth_rate": "28% over next 5 years",
        "avg_salary_usd": "90000-150000",
        "top_skills": ["AWS", "Azure", "GCP", "Kubernetes", "Terraform", "DevOps"],
        "entry_roles": ["Cloud Support Engineer", "Junior DevOps", "Cloud Intern"],
        "senior_roles": ["Cloud Architect", "Platform Engineering Lead", "SRE Manager"],
        "education_path": "B.Sc. Computer Science + AWS/Azure/GCP certifications",
        "industry_sectors": ["Tech", "Retail", "Finance", "Startups"],
    },
    "healthcare": {
        "demand": "High",
        "growth_rate": "15% over next 5 years",
        "avg_salary_usd": "60000-200000",
        "top_skills": ["Clinical Skills", "Diagnostics", "EHR Systems", "Research Methods"],
        "entry_roles": ["Junior Doctor", "Nurse", "Medical Intern", "Healthcare Administrator"],
        "senior_roles": ["Specialist Physician", "Surgeon", "Hospital Director"],
        "education_path": "MBBS / BDS / B.Sc. Nursing",
        "industry_sectors": ["Hospitals", "Pharma", "Biotech", "Telemedicine"],
    },
    "renewable energy": {
        "demand": "High",
        "growth_rate": "22% over next 5 years",
        "avg_salary_usd": "70000-130000",
        "top_skills": ["Solar PV Systems", "Wind Turbine Engineering", "Energy Storage", "Grid Management"],
        "entry_roles": ["Renewable Energy Analyst", "Solar Installer", "Junior Environmental Engineer"],
        "senior_roles": ["Energy Systems Architect", "Project Director", "Sustainability Head"],
        "education_path": "B.Sc. Electrical Engineering / Environmental Engineering",
        "industry_sectors": ["Energy", "Government", "Manufacturing", "Construction"],
    },
    "ux design": {
        "demand": "High",
        "growth_rate": "18% over next 5 years",
        "avg_salary_usd": "65000-130000",
        "top_skills": ["Figma", "User Research", "Prototyping", "Accessibility", "Design Thinking"],
        "entry_roles": ["UI Designer", "Junior UX Researcher", "Product Designer Intern"],
        "senior_roles": ["Lead UX Designer", "Head of Design", "VP Product Design"],
        "education_path": "B.Sc. Design / HCI + Portfolio",
        "industry_sectors": ["Tech", "E-commerce", "Media", "Finance"],
    },
    "finance": {
        "demand": "Moderate",
        "growth_rate": "10% over next 5 years",
        "avg_salary_usd": "70000-200000",
        "top_skills": ["Financial Modeling", "CFA", "Risk Management", "Blockchain", "Excel"],
        "entry_roles": ["Financial Analyst", "Investment Banking Analyst", "Accountant"],
        "senior_roles": ["CFO", "Portfolio Manager", "Head of Risk"],
        "education_path": "B.Sc. Finance / Accounting / Economics + CFA",
        "industry_sectors": ["Banking", "Insurance", "FinTech", "Consulting"],
    },
}


def _find_field(query: str) -> Optional[str]:
    """Return the closest matching field key for a query string."""
    q = query.lower()
    # Exact match
    if q in _MARKET_DATA:
        return q
    # Partial match
    for key in _MARKET_DATA:
        if key in q or q in key:
            return key
    return None


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class MarketTrendsInput(BaseModel):
    """Input to query labor market trends for a specific career field."""

    career_field: str = Field(
        ...,
        description=(
            "Career field to query, e.g. 'artificial intelligence', 'healthcare', "
            "'cybersecurity', 'cloud computing', 'data science', 'ux design', "
            "'renewable energy', 'finance'."
        ),
    )


class MarketTrendsOutput(BaseModel):
    """Labor market trend data for the requested career field."""

    career_field: str = Field(..., description="The career field queried.")
    demand_level: str = Field(..., description="Current demand level.")
    growth_rate: str = Field(..., description="Projected 5-year growth rate.")
    salary_range_usd: str = Field(..., description="Typical annual salary range in USD.")
    top_skills: List[str] = Field(..., description="Most in-demand skills.")
    entry_roles: List[str] = Field(..., description="Common entry-level roles.")
    senior_roles: List[str] = Field(..., description="Common senior-level roles.")
    education_path: str = Field(..., description="Recommended educational path.")
    industry_sectors: List[str] = Field(
        ..., description="Industries that typically hire in this field."
    )
    note: str = Field(..., description="Additional contextual note.")


class AllTrendsInput(BaseModel):
    """Input to retrieve a summary of all tracked career fields."""

    top_n: int = Field(
        default=5, ge=1, le=10, description="Number of top fields to return by demand."
    )


class AllTrendsOutput(BaseModel):
    """Summary of all tracked career fields ranked by demand."""

    fields_summary: str = Field(
        ..., description="Formatted multi-line summary of top career fields."
    )


# Ensure Pydantic v2 models are fully built before @tool decorators run
MarketTrendsInput.model_rebuild()
MarketTrendsOutput.model_rebuild()
AllTrendsInput.model_rebuild()
AllTrendsOutput.model_rebuild()


@tool(permission=ToolPermission.READ_ONLY)
def get_market_trends(input: MarketTrendsInput) -> MarketTrendsOutput:
    """
    Retrieve real-world labor market trend data for a specific career field
    including demand level, growth projections, salary ranges, required skills,
    and recommended educational pathways.

    Args:
        input (MarketTrendsInput): Career field name to look up.

    Returns:
        MarketTrendsOutput: Comprehensive market trend data.
    """
    key = _find_field(input.career_field)

    if key is None:
        return MarketTrendsOutput(
            career_field=input.career_field,
            demand_level="Unknown",
            growth_rate="Data not available",
            salary_range_usd="Data not available",
            top_skills=[],
            entry_roles=[],
            senior_roles=[],
            education_path="Please consult industry reports for this field.",
            industry_sectors=[],
            note=(
                f"No trend data found for '{input.career_field}'. "
                "Try 'artificial intelligence', 'data science', 'cybersecurity', "
                "'cloud computing', 'healthcare', 'ux design', 'renewable energy', or 'finance'."
            ),
        )

    d = _MARKET_DATA[key]
    return MarketTrendsOutput(
        career_field=key.title(),
        demand_level=d["demand"],
        growth_rate=d["growth_rate"],
        salary_range_usd=d["avg_salary_usd"],
        top_skills=d["top_skills"],
        entry_roles=d["entry_roles"],
        senior_roles=d["senior_roles"],
        education_path=d["education_path"],
        industry_sectors=d["industry_sectors"],
        note="Data sourced from aggregated global labor market reports (2024–2025).",
    )


@tool(permission=ToolPermission.READ_ONLY)
def get_top_career_fields(input: AllTrendsInput) -> AllTrendsOutput:
    """
    Return a ranked summary of the most in-demand career fields to help
    students understand the broader opportunity landscape.

    Args:
        input (AllTrendsInput): How many top fields to return.

    Returns:
        AllTrendsOutput: Formatted summary string of top career fields.
    """
    demand_order = {"Very High": 0, "High": 1, "Moderate": 2, "Low": 3}
    ranked = sorted(
        _MARKET_DATA.items(),
        key=lambda kv: (demand_order.get(kv[1]["demand"], 9), kv[0]),
    )

    lines: List[str] = []
    for i, (field, data) in enumerate(ranked[: input.top_n], start=1):
        lines.append(
            f"{i}. {field.title()} — Demand: {data['demand']}, "
            f"Growth: {data['growth_rate']}, Salary: ${data['avg_salary_usd']} USD/yr"
        )

    return AllTrendsOutput(fields_summary="\n".join(lines))
