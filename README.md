# SkillSync AI

ML-based career recommendation and skill gap analysis (AI & ML minor project).

## Run locally
    pip install -r requirements.txt
    python app.py              # open http://127.0.0.1:5000

Optional: `python model.py` prints the model comparison. Streamlit version:
`pip install streamlit` then `streamlit run streamlit_app.py`.

## Files
- app.py: Flask website and API (Vercel entrypoint)
- public/static/: CSS, JS, fonts; templates/index.html: the page
- data/roles_skills.csv: roles and required skills (edit to add roles)
- skills_extractor.py: extract_skills(pdf_file) using pdfplumber
- model.py: Naive Bayes, Decision Tree, Random Forest; recommend_roles(skills)
- gap_analysis.py: matched and missing skills for a chosen role
- streamlit_app.py: Streamlit interface

