"""
app/__init__.py
---------------
Factory function pour créer et configurer l'application Flask.
Initialise les extensions, le logging, et enregistre les blueprints.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
import os

# ─── Initialisation des extensions ───
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
migrate = Migrate()


def create_app():
    """
    Factory function : crée l'application Flask, charge la config,
    initialise les extensions, le logging et enregistre les blueprints.
    """
    app = Flask(__name__)

    # Chargement de la configuration
    app.config.from_object('app.config.Config')

    # Créer automatiquement le dossier d'upload s'il n'existe pas
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ==============================
    # SUPPORT HTTPS / PROXY
    # ==============================

    # Utile en production derrière Heroku, Nginx, AWS Load Balancer...
    # Permet à Flask de reconnaître correctement les requêtes HTTPS
    if app.config.get("USE_PROXY_FIX"):
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
            x_port=1
        )

    # ─── Liaison des extensions ───
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # ==============================
    # SÉCURITÉ HTTPS AVEC TALISMAN
    # ==============================

    Talisman(
        app,
        force_https=app.config.get("FORCE_HTTPS", False),

        # En local, on évite les redirections permanentes.
        # En production, c'est recommandé.
        force_https_permanent=not app.config.get("HTTPS_ENABLED", False),

        # HSTS uniquement en production.
        # En local avec certificat auto-signé, mieux vaut éviter.
        strict_transport_security=(
            app.config.get("FORCE_HTTPS", False)
            and not app.config.get("HTTPS_ENABLED", False)
        ),
        strict_transport_security_max_age=31536000,

        # On désactive CSP pour ne pas casser Bootstrap CDN et les scripts inline.
        # Tu pourras le renforcer plus tard.
        content_security_policy=None
    )

    # Configuration du login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'

    # ══════════════════════════════════════════════
    #  NOUVEAU : Configuration du système de logging
    # ══════════════════════════════════════════════
    from app.utils.logger import setup_file_logger, log_request, log_error

    # 1. Configurer le logger fichier (logs/app.log)
    setup_file_logger(app)

    # 2. Logger automatiquement TOUTES les requêtes HTTP
    @app.after_request
    def after_request_logging(response):
        return log_request(response)

    # 3. Logger les erreurs 404
    @app.errorhandler(404)
    def page_not_found(e):
        log_error(e)
        from flask import render_template
        return render_template('base.html'), 404

    # 4. Logger les erreurs 500
    @app.errorhandler(500)
    def internal_error(e):
        log_error(e)
        db.session.rollback()
        from flask import render_template
        return render_template('base.html'), 500

    app.logger.info('Système de logging initialisé avec succès')
    # ══════════════════════════════════════════════

    # ─── Import et enregistrement des blueprints ───
    from app.routes.auth_routes import auth_bp
    from app.routes.event_routes import event_bp
    from app.routes.booking_routes import booking_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(booking_bp)

    # ─── Création des tables ───
    with app.app_context():
        from app.models import user, event, booking, activity_log, event_photo
      
        db.create_all()
        _create_default_admin()

    return app


def _create_default_admin():
    """Crée un compte administrateur par défaut."""
    from app.models.user import User

    admin = User.query.filter_by(email='admin@admin.com').first()
    if not admin:
        admin = User(
            nom='Administrateur',
            email='admin@admin.com',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()