"""Shared helpers: load the roles/skills CSV."""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
ROLES_CSV = DATA_DIR / "roles_skills.csv"


def load_roles() -> dict:
    """Return {role: [skills]} from the CSV."""
    df = pd.read_csv(ROLES_CSV)
    return {r.role.strip(): [s.strip() for s in r.required_skills.split(",") if s.strip()]
            for r in df.itertuples()}


def all_skills() -> list:
    """Sorted list of every distinct skill in the CSV (the 'listed skills')."""
    return sorted({s for skills in load_roles().values() for s in skills})
