"""
app/utils/auth.py
-----------------
Décorateurs d'autorisation personnalisés.
  - admin_required : restreint l'accès aux administrateurs.
"""

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Décorateur qui restreint l'accès à une route aux administrateurs.
    Si l'utilisateur n'est pas admin, il est redirigé vers l'accueil
    avec un message d'erreur.
    
    Usage:
        @app.route('/admin')
        @login_required
        @admin_required
        def admin_page():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('event.index'))
        return f(*args, **kwargs)
    return decorated_function