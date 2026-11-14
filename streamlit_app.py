"""SkillSync AI - Streamlit app.  Run: streamlit run app.py"""
import pandas as pd
import streamlit as st

from gap_analysis import skill_gap
from model import load_bundle, recommend_roles
from skills_common import all_skills, load_roles
from skills_extractor import extract_skills

st.set_page_config(page_title="SkillSync AI", page_icon="🎯", layout="wide")
bundle = load_bundle()

st.title("🎯 SkillSync AI")
st.caption("ML-based career recommendation and skill gap analysis")

tab_main, tab_models, tab_data = st.tabs(["Analyze Resume", "Model Comparison", "Roles Dataset"])

with tab_main:
    st.subheader("1. Upload your resume (PDF)")
    pdf = st.file_uploader("Resume PDF", type=["pdf"], label_visibility="collapsed")

    if pdf is not None:
        # Step 2: extract skills
        detected = extract_skills(pdf)
        st.subheader("2. Skills found in your resume")
        if detected:
            st.success(f"{len(detected)} listed skills detected.")
        else:
            st.warning("No listed skills were found. You can add skills manually below.")
        skills = st.multiselect("Review or edit your skills", all_skills(), default=detected)

        # Step 3: recommend roles
        if skills:
            st.subheader("3. Recommended roles")
            model_choice = st.selectbox("Model used", list(bundle["models"]),
                                        index=list(bundle["models"]).index(bundle["best"]))
            recs = recommend_roles(skills, top_n=5, model_name=model_choice, bundle=bundle)
            rec_df = pd.DataFrame(recs, columns=["Role", "Score (%)"]).set_index("Role")
            c1, c2 = st.columns([1, 1])
            c1.dataframe(rec_df, width="stretch")
            c2.bar_chart(rec_df)

            # Step 4: skill gap
            st.subheader("4. Skill gap for a role")
            role = st.selectbox("Choose a role", [r for r, _ in recs])
            gap = skill_gap(skills, role)
            st.progress(int(gap["match_percent"]), text=f"Match: {gap['match_percent']}%")
            g1, g2 = st.columns(2)
            g1.markdown("**✅ Matched skills**")
            g1.write(", ".join(gap["matched"]) or "None")
            g2.markdown("**❌ Missing skills**")
            g2.write(", ".join(gap["missing"]) or "None, you meet all requirements.")
        else:
            st.info("Select at least one skill to get recommendations.")

with tab_models:
    st.subheader("Model comparison")
    st.write(f"Trained on {bundle['n_train']} samples, tested on {bundle['n_test']} held-out samples.")
    res = bundle["results"].set_index("Model")
    st.dataframe(res, width="stretch")
    st.bar_chart(res)
    st.success(f"Best model (highest F1-score): {bundle['best']}")
    st.caption("Training samples are simulated from the roles CSV (random subsets of each role's "
               "skills plus noise), so scores reflect this dataset and not real-world hiring.")

with tab_data:
    st.subheader("Roles and required skills")
    st.dataframe(pd.DataFrame([(r, ", ".join(s)) for r, s in load_roles().items()],
                              columns=["Role", "Required skills"]), width="stretch")
