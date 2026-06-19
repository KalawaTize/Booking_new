"""
app/utils/security.py
---------------------
Fonctions utilitaires de validation et de sécurité.
  - validate_email : vérifie le format d'une adresse email.
  - validate_password : vérifie la robustesse d'un mot de passe.
  - sanitize_input : nettoie une entrée utilisateur contre les injections XSS.
"""

import re


def validate_email(email):
    """
    Valide le format d'une adresse email à l'aide d'une expression régulière.
    
    Args:
        email (str): L'adresse email à valider.
    
    Returns:
        bool: True si l'email est valide, False sinon.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """
    Vérifie qu'un mot de passe respecte les critères de sécurité minimum.
    Critère : au moins 6 caractères.
    
    Args:
        password (str): Le mot de passe à valider.
    
    Returns:
        bool: True si le mot de passe est valide, False sinon.
    """
    return len(password) >= 6


def sanitize_input(text):
    """
    Nettoie une entrée utilisateur en supprimant les balises HTML
    potentiellement dangereuses (protection XSS basique).
    Jinja2 échappe automatiquement les variables dans les templates,
    mais cette fonction offre une couche de sécurité supplémentaire.
    
    Args:
        text (str): Le texte à nettoyer.
    
    Returns:
        str: Le texte nettoyé.
    """
    if not text:
        return ''
    # Supprime les balises HTML
    clean = re.sub(r'<[^>]*>', '', text)
    return clean.strip()