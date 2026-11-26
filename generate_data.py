"""Builds a synthetic training set from roles_skills.csv.

The CSV has one row per role, which is too small to train and compare models.
For each role we simulate many students: each has a random 50-100% of the
role's skills plus 0-2 unrelated skills (noise). Run: python generate_data.py
"""
import random
import pandas as pd
from skills_common import load_roles, all_skills, DATA_DIR

SAMPLES_PER_ROLE = 150


def generate(samples_per_role=SAMPLES_PER_ROLE, seed=42) -> pd.DataFrame:
    rng = random.Random(seed)
    roles, pool, rows = load_roles(), all_skills(), []
    for role, req in roles.items():
        for _ in range(samples_per_role):
            k = max(2, round(len(req) * rng.uniform(0.5, 1.0)))
            skills = set(rng.sample(req, min(k, len(req))))
            skills |= set(rng.sample(pool, rng.randint(0, 2)))
            rows.append({"skills": ", ".join(sorted(skills)), "role": role})
    return pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)


if __name__ == "__main__":
    df = generate()
    df.to_csv(DATA_DIR / "training_data.csv", index=False)
    print(f"Saved {len(df)} rows to data/training_data.csv")
