"""Step 4: compare student skills with a chosen role."""
from skills_common import load_roles


def skill_gap(student_skills, role) -> dict:
    required = load_roles()[role]
    have = {s.lower() for s in student_skills}
    matched = [s for s in required if s.lower() in have]
    missing = [s for s in required if s.lower() not in have]
    return {"matched": matched, "missing": missing,
            "match_percent": round(100 * len(matched) / len(required), 1)}
