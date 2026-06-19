"""
app/models/booking.py
---------------------
Modèle Booking : représente une réservation de billet.
Champs : id, user_id, event_id, nombre_places, statut, date_reservation.
Statuts possibles : 'en_attente', 'confirme', 'annule'.
"""

from app import db
from datetime import datetime


class Booking(db.Model):
    """
    Modèle de données pour les réservations de billets.
    
    Attributs:
        id (int): Identifiant unique de la réservation.
        user_id (int): Clé étrangère vers l'utilisateur qui a fait la réservation.
        event_id (int): Clé étrangère vers l'événement réservé.
        nombre_places (int): Nombre de places réservées.
        statut (str): Statut de la réservation ('en_attente', 'confirme', 'annule').
        date_reservation (datetime): Date et heure de la réservation.
        montant_total (float): Montant total de la réservation.
    """
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    nombre_places = db.Column(db.Integer, nullable=False, default=1)
    statut = db.Column(db.String(20), nullable=False, default='en_attente')
    date_reservation = db.Column(db.DateTime, nullable=False, default=datetime.now)
    montant_total = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'<Booking #{self.id} - User:{self.user_id} Event:{self.event_id} Status:{self.statut}>'