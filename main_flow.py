"""
main_flow.py — programmatic testing script for the Career Assessment Flow
and Skill Gap Coaching Flow.

Usage:
  export PYTHONPATH=/path/to/adk/src:/path/to/adk
  python3 main_flow.py
"""
import asyncio
import json
from pathlib import Path

from career_counsellor.tools.career_assessment_flow import build_career_assessment_flow
from career_counsellor.tools.skill_gap_coaching_flow import build_skill_gap_coaching_flow


GENERATED_DIR = Path(__file__).resolve().parent / "career_counsellor" / "generated"
GENERATED_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Test: Career Assessment Flow
# ---------------------------------------------------------------------------
async def test_career_assessment_flow() -> None:
    print("\n" + "=" * 60)
    print("Testing: Career Assessment Flow")
    print("=" * 60)

    flow_def = await build_career_assessment_flow().compile_deploy()
    flow_def.dump_spec(str(GENERATED_DIR / "career_assessment_flow.json"))
    print(f"[✓] Flow spec dumped to {GENERATED_DIR}/career_assessment_flow.json")

    test_input = {
        "student_id": "STU-001",
        "student_name": "Priya Sharma",
        "age": 17,
        "current_grade": "11th Grade",
        "subjects_json": json.dumps([
            {"subject": "Mathematics", "score": 92},
            {"subject": "Computer Science", "score": 88},
            {"subject": "Physics", "score": 80},
            {"subject": "Chemistry", "score": 72},
            {"subject": "English", "score": 85},
        ]),
        "interests": "coding, problem solving, technology",
        "current_skills": "Python, basic SQL",
        "preferred_work_style": "independent",
    }

    result = await flow_def.invoke(test_input, debug=True)
    print("\n[Career Assessment Result]")
    print(result)


# ---------------------------------------------------------------------------
# Test: Skill Gap Coaching Flow
# ---------------------------------------------------------------------------
async def test_skill_gap_flow() -> None:
    print("\n" + "=" * 60)
    print("Testing: Skill Gap Coaching Flow")
    print("=" * 60)

    flow_def = await build_skill_gap_coaching_flow().compile_deploy()
    flow_def.dump_spec(str(GENERATED_DIR / "skill_gap_coaching_flow.json"))
    print(f"[✓] Flow spec dumped to {GENERATED_DIR}/skill_gap_coaching_flow.json")

    test_input = {
        "student_name": "Rahul Verma",
        "target_career_field": "data science",
        "current_skills": "Python, Excel, basic statistics",
        "timeline_months": 6,
        "learning_hours_per_week": 12,
    }

    result = await flow_def.invoke(test_input, debug=True)
    print("\n[Skill Gap Coaching Result]")
    print(result)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> None:
    await test_career_assessment_flow()
    await test_skill_gap_flow()


if __name__ == "__main__":
    asyncio.run(main())
