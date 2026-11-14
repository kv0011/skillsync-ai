"""Step 2: train Naive Bayes / Decision Tree / Random Forest, compare them,
and recommend roles from a list of skills."""
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import BernoulliNB
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.tree import DecisionTreeClassifier

from generate_data import generate
from skills_common import DATA_DIR, all_skills

MODEL_FILE = DATA_DIR / "model.joblib"


def _split(s):
    return [x.strip() for x in s.split(",") if x.strip()]


def train(save=True) -> dict:
    df = generate()
    mlb = MultiLabelBinarizer(classes=all_skills())
    X = mlb.fit_transform(df["skills"].apply(_split))
    y = df["role"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    models = {
        "Naive Bayes": BernoulliNB(),
        "Decision Tree": DecisionTreeClassifier(max_depth=12, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    }
    rows = []
    for name, m in models.items():
        m.fit(X_tr, y_tr)
        pred = m.predict(X_te)
        rows.append({"Model": name,
                     "Accuracy": round(accuracy_score(y_te, pred), 4),
                     "F1-score (macro)": round(f1_score(y_te, pred, average="macro"), 4)})
    results = pd.DataFrame(rows)
    best = results.sort_values(["F1-score (macro)", "Accuracy"], ascending=False).iloc[0]["Model"]
    bundle = {"models": models, "mlb": mlb, "results": results, "best": best,
              "n_train": len(X_tr), "n_test": len(X_te)}
    if save:
        try:
            joblib.dump(bundle, MODEL_FILE)
        except OSError:  # read-only filesystem (e.g. Vercel): keep model in memory
            pass
    return bundle


def load_bundle() -> dict:
    try:
        return joblib.load(MODEL_FILE)
    except Exception:  # missing or incompatible file: retrain
        return train()


def recommend_roles(skills, top_n=3, model_name=None, bundle=None):
    """Return [(role, score_percent), ...] sorted high to low.
    Empty list if none of the skills are in the listed skills."""
    bundle = bundle or load_bundle()
    known = [s for s in skills if s in bundle["mlb"].classes_]
    if not known:
        return []
    model = bundle["models"][model_name or bundle["best"]]
    probs = model.predict_proba(bundle["mlb"].transform([known]))[0]
    ranked = sorted(zip(model.classes_, probs), key=lambda t: -t[1])[:top_n]
    return [(r, round(float(p) * 100, 1)) for r, p in ranked]


if __name__ == "__main__":
    b = train()
    print(b["results"].to_string(index=False))
    print("Best model:", b["best"])
