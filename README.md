# Automated Resume Parser

A starter Flask application that accepts PDF and DOCX resumes, extracts candidate contact details, skills and education, and stores searchable records in PostgreSQL.

## Features

- PDF text extraction with `pdfplumber`
- DOCX extraction with `python-docx`
- spaCy named-entity recognition when `en_core_web_sm` is installed
- Regex and configurable skills-taxonomy fallback
- PostgreSQL persistence through Flask-SQLAlchemy
- Search across name, email, skills, education and extracted resume text
- Candidate detail page and record deletion
- Upload size/type validation and generated storage filenames

## Requirements

- Python 3.10+
- PostgreSQL 13+
- Windows, macOS or Linux

## Setup (Windows PowerShell)

```powershell
# 1. Open this project folder in a terminal
py -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Install the spaCy English model
python -m spacy download en_core_web_sm

# 4. Create the PostgreSQL database and user
# In psql as a PostgreSQL administrator, run the commands in schema.sql.
# Change the sample password before using this outside local development.

# 5. Create your local environment file
Copy-Item .env.example .env
# Edit .env and set SECRET_KEY and DATABASE_URL to your PostgreSQL credentials.

# 6. Start the app
python app.py
```

Open http://127.0.0.1:5000.

### Linux / macOS

Activate the virtual environment with `source venv/bin/activate`, then follow the same install, database and run steps. Copy `.env.example` to `.env` with `cp .env.example .env`.

## Database

Tables are created automatically on first startup. The `Candidate` table stores:
- `name`, `email`, `phone`
- `skills_text`, `education_text`
- extracted `resume_text` for searching
- original and generated stored filenames
- creation timestamp

## Important limitations

This is a functional starter, not a production-grade hiring decision system.

- Name and education extraction use heuristics; always review and correct extracted information.
- The initial skill list is deliberately small and should be customized for your job families.
- Scanned/image-only PDFs need OCR, which is not included.
- Tables, columns and unusual document layouts may reduce extraction quality.
- Do not use parser output to automatically reject, rank or make employment decisions. Keep human review in the loop.
- Resumes contain personal data. Restrict access, use HTTPS in deployment, define retention/deletion rules, and never commit `.env`, uploaded resumes, or database credentials to GitHub.

## Project layout

```text
automated_resume_parser/
├── app.py
├── models.py
├── parser.py
├── requirements.txt
├── schema.sql
├── .env.example
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   └── detail.html
└── static/
    └── style.css
```
