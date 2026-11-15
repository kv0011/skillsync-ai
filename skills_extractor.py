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


def _pdf_text(pdf_file):
    """Return (text, number_of_pages)."""
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages), len(pdf.pages)


# Words that normally appear as section headings in a resume / CV.
RESUME_SECTIONS = ["education", "experience", "work experience", "skills", "technical skills",
                   "projects", "certifications", "certificates", "summary", "objective",
                   "profile", "internship", "achievements", "languages", "references",
                   "declaration", "curriculum vitae", "resume", "academic", "qualification"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?\d[\s-]?){10,13}")
LINKS = re.compile(r"linkedin\.com|github\.com")


def check_resume(text: str, pages: int):
    """Heuristic check that a PDF is a resume. Returns (ok, message)."""
    low = text.lower()
    words = len(low.split())
    if words < 40:
        return False, ("No readable text was found in this PDF. Scanned or image-only files are not "
                       "supported. Upload a text-based resume PDF, or add your skills manually.")
    if pages > 5 or words > 2500:
        return False, ("This file is too long to be a resume (looks like a report, book or article). "
                       "Please upload your resume, which is usually 1 to 3 pages.")
    sections = sum(1 for w in RESUME_SECTIONS if _found(w, low))
    contacts = sum(bool(x.search(low)) for x in (EMAIL, PHONE, LINKS))
    if sections < 1 or sections + contacts < 3:
        return False, ("This does not look like a resume. A resume should have sections such as "
                       "Education, Skills, Projects or Experience, plus contact details like an email "
                       "or phone number. Please upload your resume PDF.")
    return True, ""


def _found(term: str, text: str) -> bool:
    # whole-term match, so "Java" does not match "JavaScript"
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(term.lower()) + r"(?![A-Za-z0-9])", text) is not None


def analyze_pdf(pdf_file) -> dict:
    """Validate the PDF as a resume, then extract skills.
    Returns {"ok": bool, "message": str, "skills": list}."""
    try:
        text, pages = _pdf_text(pdf_file)
    except Exception:
        return {"ok": False, "message": "This PDF could not be read. Please upload a valid PDF.", "skills": []}
    ok, message = check_resume(text, pages)
    if not ok:
        return {"ok": False, "message": message, "skills": []}
    return {"ok": True, "message": "", "skills": _skills_from_text(text.lower())}


def _skills_from_text(text: str) -> list:
    found = {s for s in all_skills() if _found(s, text)}
    found |= {skill for alias, skill in ALIASES.items() if _found(alias, text)}
    return sorted(found)


def extract_skills(pdf_file) -> list:
    """Return listed skills found in the resume. Empty list if none match
    or the PDF has no readable text."""
    try:
        text, _ = _pdf_text(pdf_file)
    except Exception:
        return []
    return _skills_from_text(text.lower()) if text.strip() else []
