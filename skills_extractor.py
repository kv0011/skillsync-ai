"""Step 1: pull skills out of a resume PDF."""
import re
import pdfplumber
from skills_common import all_skills

# Common spellings that should map to a listed skill.
ALIASES = {
    "sklearn": "Scikit-learn", "scikit learn": "Scikit-learn",
    "powerbi": "Power BI", "power-bi": "Power BI",
    "nodejs": "Node.js", "node js": "Node.js", "reactjs": "React",
    "ml": "Machine Learning", "tensor flow": "TensorFlow",
    "ci cd": "CI/CD", "ida": "IDA Pro", "dfir": "Digital Forensics",
    "data viz": "Data Visualization", "k8s": "Kubernetes",
}


def _pdf_text(pdf_file) -> str:
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def _found(term: str, text: str) -> bool:
    # whole-term match, so "Java" does not match "JavaScript"
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(term.lower()) + r"(?![A-Za-z0-9])", text) is not None


def extract_skills(pdf_file) -> list:
    """Return listed skills found in the resume. Empty list if none match
    or the PDF has no readable text."""
    try:
        text = _pdf_text(pdf_file).lower()
    except Exception:
        return []
    if not text.strip():
        return []
    found = {s for s in all_skills() if _found(s, text)}
    found |= {skill for alias, skill in ALIASES.items() if _found(alias, text)}
    return sorted(found)
