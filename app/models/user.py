"""
app/models/user.py
------------------
Modèle User : représente un utilisateur de l'application.
Champs : id, nom, email, password (haché), role (user/admin).
Relation : un utilisateur peut avoir plusieurs réservations (bookings).
"""

from app import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    """
    Callback utilisé par Flask-Login pour recharger l'utilisateur
    à partir de l'ID stocké en session.
    """
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """
    Modèle de données pour les utilisateurs.
    
    Attributs:
        id (int): Identifiant unique auto-incrémenté.
        nom (str): Nom complet de l'utilisateur.
        email (str): Adresse email unique, utilisée pour la connexion.
        password (str): Mot de passe haché avec bcrypt.
        role (str): Rôle de l'utilisateur ('user' ou 'admin').
        bookings: Relation vers les réservations de l'utilisateur.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    # Relation one-to-many : un utilisateur possède plusieurs réservations
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')

    def is_admin(self):
        """Vérifie si l'utilisateur a le rôle administrateur."""
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.nom} ({self.email})>'