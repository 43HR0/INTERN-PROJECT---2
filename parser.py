import re
from pathlib import Path

import pdfplumber
from docx import Document

# Starter taxonomy: extend this list for the roles your team recruits for.
SKILLS = {
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "postgresql",
    "mysql", "sqlite", "flask", "django", "fastapi", "react", "node.js", "html",
    "css", "machine learning", "deep learning", "nlp", "spacy", "pandas", "numpy",
    " scikit-learn", "tensorflow", "pytorch", "git", "docker", "kubernetes", "aws",
    "azure", "linux", "rest api", "excel", "power bi", "tableau", "data analysis",
    "communication", "project management", "problem solving"
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
EDUCATION_TERMS = (
    "bachelor", "master", "b.tech", "b.e.", "m.tech", "m.e.", "b.sc", "m.sc",
    "bca", "mca", "ph.d", "phd", "diploma", "university", "college"
)

def extract_text(path: Path, extension: str) -> str:
    if extension == "pdf":
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages)
    if extension == "docx":
        doc = Document(str(path))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(parts)
    raise ValueError("Only PDF and DOCX files are supported.")

def detect_name(text: str, email: str | None) -> str | None:
    # Heuristic fallback: first plausible short line near the top.
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()[:12]]
    for line in lines:
        if not line or len(line) > 60 or "@" in line:
            continue
        if re.search(r"\d", line):
            continue
        if any(word in line.lower() for word in ("resume", "curriculum vitae", "phone", "email", "linkedin")):
            continue
        words = line.split()
        if 2 <= len(words) <= 5 and all(re.match(r"^[A-Za-z][A-Za-z.'-]*$", w) for w in words):
            return line
    return None

def parse_resume(path: Path, extension: str) -> dict:
    text = extract_text(path, extension)
    email_match = EMAIL_RE.search(text)
    email = email_match.group(0) if email_match else None
    phone_match = PHONE_RE.search(text)
    phone = phone_match.group(0).strip() if phone_match else None

    # spaCy is used for sentence/phrase processing when the English model is installed.
    # Extraction still works without it; the skill taxonomy and contact regexes are fallback.
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text[:100000])
        person = next((ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"), None)
    except (ImportError, OSError):
        person = None

    name = person or detect_name(text, email)
    lower = text.lower()
    found_skills = sorted(
        {skill.strip() for skill in SKILLS if skill.strip() and
         re.search(r"(?<![a-z0-9+#])" + re.escape(skill.strip()) + r"(?![a-z0-9+#])", lower)}
    )

    education = []
    for line in text.splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip(" •-\t")
        if cleaned and any(term in cleaned.lower() for term in EDUCATION_TERMS):
            if cleaned not in education:
                education.append(cleaned[:300])

    return {
        "text": text,
        "name": name,
        "email": email,
        "phone": phone,
        "skills": found_skills,
        "education": education[:20],
    }
