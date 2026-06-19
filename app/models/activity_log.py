"""
app/models/activity_log.py
--------------------------
Modèle pour enregistrer les activités des utilisateurs.
"""

from app import db
from datetime import datetime


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)

    # Utilisateur concerné
    user_id = db.Column(db.Integer, nullable=True)
    user_email = db.Column(db.String(120), nullable=False, default="Anonyme")

    # Type d'action : LOGIN, LOGOUT, BOOKING_CREATED, etc.
    action = db.Column(db.String(80), nullable=False, index=True)

    # Détails de l'activité
    details = db.Column(db.Text, nullable=True)

    # Infos techniques
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    endpoint = db.Column(db.String(120), nullable=True)
    method = db.Column(db.String(10), nullable=True)
    url = db.Column(db.String(500), nullable=True)

    # Date de création du log
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ActivityLog {self.action} - {self.user_email}>"