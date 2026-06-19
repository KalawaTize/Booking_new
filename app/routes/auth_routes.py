"""
app/routes/auth_routes.py
-------------------------
Routes d'authentification avec logging des activités.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.user import User
from app.utils.security import validate_email, validate_password
from app.utils.logger import log_activity  # ← AJOUTÉ

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription d'un nouvel utilisateur."""
    if current_user.is_authenticated:
        return redirect(url_for('event.index'))

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if not nom or len(nom) < 2:
            errors.append('Le nom doit contenir au moins 2 caractères.')
        if not validate_email(email):
            errors.append('Adresse email invalide.')
        if not validate_password(password):
            errors.append('Le mot de passe doit contenir au moins 6 caractères.')
        if password != confirm_password:
            errors.append('Les mots de passe ne correspondent pas.')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            errors.append('Cet email est déjà utilisé.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            # ── LOG : tentative d'inscription échouée ──
            log_activity('REGISTER_FAILED', f'Tentative échouée pour {email} : {", ".join(errors)}')
            return render_template('register.html', nom=nom, email=email)

        # Création de l'utilisateur
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(nom=nom, email=email, password=hashed_password, role='user')
        db.session.add(new_user)
        db.session.commit()

        # ── LOG : inscription réussie ──
        log_activity('REGISTER', f'Nouvel utilisateur inscrit : {nom} ({email})', user=new_user)

        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))

    # ── LOG : page d'inscription visitée ──
    log_activity('PAGE_VIEW', 'Page d\'inscription visitée')
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion d'un utilisateur."""
    if current_user.is_authenticated:
        return redirect(url_for('event.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=bool(remember))

            # ── LOG : connexion réussie ──
            log_activity('LOGIN', f'Connexion réussie pour {user.nom} ({email})', user=user)

            flash(f'Bienvenue, {user.nom} !', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin():
                return redirect(url_for('event.admin_dashboard'))
            return redirect(url_for('event.index'))
        else:
            # ── LOG : tentative de connexion échouée ──
            log_activity('LOGIN_FAILED', f'Tentative de connexion échouée pour {email}')

            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion de l'utilisateur."""
    # ── LOG : déconnexion ──
    log_activity('LOGOUT', f'Déconnexion de {current_user.nom} ({current_user.email})')

    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('event.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Page de profil utilisateur."""
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if not nom or len(nom) < 2:
            errors.append('Le nom doit contenir au moins 2 caractères.')
        if new_password:
            if not validate_password(new_password):
                errors.append('Le nouveau mot de passe doit contenir au moins 6 caractères.')
            if new_password != confirm_password:
                errors.append('Les mots de passe ne correspondent pas.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('profile.html')

        old_nom = current_user.nom
        current_user.nom = nom
        password_changed = False
        if new_password:
            current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            password_changed = True

        db.session.commit()

        # ── LOG : profil modifié ──
        details = f'Profil modifié : nom "{old_nom}" → "{nom}"'
        if password_changed:
            details += ' + mot de passe changé'
        log_activity('PROFILE_UPDATE', details)

        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('profile.html')