from datetime import datetime, timezone
from app import db

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(320), index=True)
    phone = db.Column(db.String(50))
    skills_text = db.Column(db.Text, nullable=False, default="")
    education_text = db.Column(db.Text, nullable=False, default="")
    resume_text = db.Column(db.Text, nullable=False, default="")
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def skills(self):
        return [item.strip() for item in self.skills_text.split(",") if item.strip()]

    @property
    def education(self):
        return [item.strip() for item in self.education_text.splitlines() if item.strip()]
