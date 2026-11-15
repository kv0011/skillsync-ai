"""SkillSync AI - website (Flask).
Run: python app.py   then open http://127.0.0.1:5000
Uploaded resumes are processed in memory and are never saved."""
import io
from collections import Counter
from flask import Flask, jsonify, render_template, request

from gap_analysis import skill_gap
from model import load_bundle, recommend_roles
from skills_common import all_skills, load_roles
from skills_extractor import analyze_pdf

# Static files live in public/ so Vercel serves them from its CDN; locally Flask serves them too.
app = Flask(__name__, static_folder="public/static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB (Vercel request limit is 4.5 MB)
BUNDLE = load_bundle()
ROLES = load_roles()
DEMAND = Counter(s for skills in ROLES.values() for s in skills)


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/meta")
def meta():
    return jsonify(skills=all_skills(), roles=ROLES, best=BUNDLE["best"],
                   models=BUNDLE["results"].to_dict("records"),
                   n_train=BUNDLE["n_train"], n_test=BUNDLE["n_test"])


@app.post("/api/extract")
def extract():
    f = request.files.get("resume")
    if not f or not f.filename.lower().endswith(".pdf"):
        return jsonify(error="Please upload a PDF file."), 400
    data = f.read()
    if not data.startswith(b"%PDF"):
        return jsonify(error="This file is not a valid PDF."), 400
    result = analyze_pdf(io.BytesIO(data))
    if not result["ok"]:
        return jsonify(error=result["message"]), 422
    return jsonify(skills=result["skills"])


@app.post("/api/recommend")
def recommend():
    body = request.get_json(silent=True) or {}
    recs = recommend_roles(body.get("skills", []), top_n=5,
                           model_name=body.get("model") or None, bundle=BUNDLE)
    return jsonify(recommendations=[{"role": r, "score": s} for r, s in recs])


@app.post("/api/gap")
def gap():
    body = request.get_json(silent=True) or {}
    role = body.get("role")
    if role not in ROLES:
        return jsonify(error="Unknown role."), 400
    g = skill_gap(body.get("skills", []), role)
    # learning priority: skills needed by more roles come first
    g["priority"] = [{"skill": s, "roles": DEMAND[s]}
                     for s in sorted(g["missing"], key=lambda s: -DEMAND[s])]
    return jsonify(g)


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File is too large (max 4 MB)."), 413


if __name__ == "__main__":
    app.run(debug=False)
