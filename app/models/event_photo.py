"""
app/models/event_photo.py
-------------------------
Modèle pour stocker les photos associées aux événements.
"""

from app import db
from datetime import datetime


class EventPhoto(db.Model):
    __tablename__ = "event_photos"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False,
        index=True
    )

    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)

    caption = db.Column(db.String(255), nullable=True)

    uploaded_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<EventPhoto {self.filename}>"