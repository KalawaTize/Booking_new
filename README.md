TicketBooking — Système de Réservation de Billets

Application web de réservation de billets pour événements, développée avec **Python/Flask**.

## Fonctionnalités

### Utilisateurs
- Inscription et connexion sécurisées (bcrypt)
- Gestion du profil utilisateur
- Recherche d'événements (par mot-clé et catégorie)
- Réservation de billets avec sélection du nombre de places
- Simulation de paiement sécurisé
- Tableau de bord avec historique des réservations
- Annulation de réservation

### Administrateurs
- Tableau de bord avec statistiques (événements, réservations, revenus)
- CRUD complet des événements (ajouter, modifier, supprimer)
- Gestion des réservations (confirmer, annuler)
- Visualisation de toutes les données

## Technologies
- **Backend** : Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt
- **Frontend** : HTML5, CSS3, Bootstrap 5, Jinja2
- **Base de données** : SQLite
- **Sécurité** : CSRF (Flask-WTF), hachage bcrypt, validation des formulaires

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-repo/ticket_booking.git
cd ticket_booking

# 2. Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
# Modifier le fichier .env si nécessaire

# 5. Lancer l'application
python run.py
