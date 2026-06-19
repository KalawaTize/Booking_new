"""
app/models/event.py
-------------------
Modèle Event : représente un événement pour lequel des billets peuvent être réservés.
Champs : id, titre, description, date, lieu, prix, capacite, places_disponibles, categorie, image_url.
Relation : un événement peut avoir plusieurs réservations (bookings).
"""

from app import db
from datetime import datetime


class Event(db.Model):
    """
    Modèle de données pour les événements.
    
    Attributs:
        id (int): Identifiant unique.
        titre (str): Nom de l'événement.
        description (str): Description détaillée.
        date (datetime): Date et heure de l'événement.
        lieu (str): Lieu où se déroule l'événement.
        prix (float): Prix d'un billet.
        capacite (int): Nombre total de places.
        places_disponibles (int): Nombre de places encore libres.
        categorie (str): Catégorie/tag de l'événement (concert, sport, théâtre, etc.).
        image_url (str): URL de l'image de l'événement.
        bookings: Relation vers les réservations liées à cet événement.
    """
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(200), nullable=False)
    prix = db.Column(db.Float, nullable=False, default=0.0)
    capacite = db.Column(db.Integer, nullable=False)
    places_disponibles = db.Column(db.Integer, nullable=False)
    categorie = db.Column(db.String(50), nullable=False, default='Général')
    image_url = db.Column(db.String(500), default='')

    # Relation one-to-many : un événement possède plusieurs réservations
    bookings = db.relationship('Booking', backref='event', lazy=True, cascade='all, delete-orphan')

    photos = db.relationship(
        "EventPhoto",
        backref="event",
        lazy=True,
        cascade="all, delete-orphan"
    )


    def is_available(self):
        """Vérifie s'il reste des places disponibles."""
        return self.places_disponibles > 0

    def is_past(self):
        """Vérifie si l'événement est déjà passé."""
        return self.date < datetime.utcnow()

    def __repr__(self):
        return f'<Event {self.titre} - {self.date}>'