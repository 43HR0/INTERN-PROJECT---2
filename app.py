import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from parser import parse_resume

load_dotenv()
db = SQLAlchemy()

ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://resume_user:change_me@localhost:5432/resume_parser"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = str(Path(app.instance_path) / "uploads")
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from models import Candidate
    with app.app_context():
        db.create_all()

    @app.get("/")
    def index():
        q = request.args.get("q", "").strip()
        query = Candidate.query
        if q:
            pattern = f"%{q}%"
            query = query.filter(
                db.or_(
                    Candidate.name.ilike(pattern),
                    Candidate.email.ilike(pattern),
                    Candidate.skills_text.ilike(pattern),
                    Candidate.education_text.ilike(pattern),
                    Candidate.resume_text.ilike(pattern),
                )
            )
        candidates = query.order_by(Candidate.created_at.desc()).all()
        return render_template("index.html", candidates=candidates, q=q)

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        if request.method == "GET":
            return render_template("upload.html")

        uploaded = request.files.get("resume")
        if not uploaded or not uploaded.filename:
            flash("Choose a PDF or DOCX resume first.", "error")
            return redirect(url_for("upload"))

        original_name = secure_filename(uploaded.filename)
        extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
        if extension not in ALLOWED_EXTENSIONS:
            flash("Unsupported file type. Please upload a PDF or DOCX file.", "error")
            return redirect(url_for("upload"))

        # Save under a generated name to avoid collisions and path tricks.
        import uuid
        stored_name = f"{uuid.uuid4().hex}.{extension}"
        destination = Path(app.config["UPLOAD_FOLDER"]) / stored_name
        uploaded.save(destination)

        try:
            extracted = parse_resume(destination, extension)
            if not extracted["text"].strip():
                raise ValueError("No readable text was found. The file may be scanned; OCR is not included.")

            candidate = Candidate(
                name=extracted["name"] or "Name not detected",
                email=extracted["email"],
                phone=extracted["phone"],
                skills_text=", ".join(extracted["skills"]),
                education_text="\n".join(extracted["education"]),
                resume_text=extracted["text"][:100000],
                original_filename=original_name,
                stored_filename=stored_name,
            )
            db.session.add(candidate)
            db.session.commit()
            flash(f"Resume parsed and saved for {candidate.name}. Please review extracted fields.", "success")
            return redirect(url_for("candidate_detail", candidate_id=candidate.id))
        except Exception as exc:
            db.session.rollback()
            destination.unlink(missing_ok=True)
            flash(f"Could not parse this resume: {exc}", "error")
            return redirect(url_for("upload"))

    @app.get("/candidate/<int:candidate_id>")
    def candidate_detail(candidate_id):
        candidate = Candidate.query.get_or_404(candidate_id)
        return render_template("detail.html", candidate=candidate)

    @app.post("/candidate/<int:candidate_id>/delete")
    def delete_candidate(candidate_id):
        candidate = Candidate.query.get_or_404(candidate_id)
        stored = Path(app.config["UPLOAD_FOLDER"]) / candidate.stored_filename
        stored.unlink(missing_ok=True)
        db.session.delete(candidate)
        db.session.commit()
        flash("Candidate record deleted.", "success")
        return redirect(url_for("index"))

    @app.errorhandler(413)
    def too_large(_error):
        flash(f"File too large. Maximum upload size is {MAX_UPLOAD_MB} MB.", "error")
        return redirect(url_for("upload"))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
