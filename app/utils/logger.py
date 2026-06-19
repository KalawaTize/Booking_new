"""
app/utils/logger.py
-------------------
Configuration du système de logging de l'application.
Deux niveaux de logging :
  1. Fichier log (logs/app.log) : trace technique de toutes les requêtes et erreurs
  2. Base de données (table activity_logs) : trace fonctionnelle des actions utilisateur

Le fichier log utilise une rotation automatique (max 5 Mo, 10 fichiers conservés).
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import request
from flask_login import current_user


def setup_file_logger(app):
    """
    Configure le logger fichier avec rotation automatique.
    Les logs sont écrits dans logs/app.log.
    
    Format : [DATE HEURE] NIVEAU - IP - MÉTHODE URL - Message
    
    Args:
        app: L'instance Flask de l'application.
    """
    # ─── Créer le dossier logs s'il n'existe pas ───
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'app.log')

    # ─── Configuration du handler avec rotation ───
    # maxBytes=5MB, backupCount=10 fichiers conservés
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 Mo
        backupCount=10,
        encoding='utf-8'
    )

    # ─── Format des logs ───
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # ─── Attacher le handler à l'app Flask ───
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Log de démarrage
    app.logger.info('=' * 60)
    app.logger.info('APPLICATION DÉMARRÉE')
    app.logger.info('=' * 60)


def log_activity(action, details='', user=None):
    """
    Enregistre une activité utilisateur dans la base de données
    ET dans le fichier log.
    
    Args:
        action (str): Type d'action (ex: 'LOGIN', 'REGISTER', 'BOOKING', etc.)
        details (str): Description détaillée de l'action.
        user: L'utilisateur concerné (par défaut : current_user).
    
    Exemple:
        log_activity('LOGIN', 'Connexion réussie pour admin@admin.com')
        log_activity('BOOKING', f'Réservation de 2 places pour Concert X', user=current_user)
    """
    from app import db
    from app.models.activity_log import ActivityLog
    from flask import current_app

    # Déterminer l'utilisateur
    if user is None:
        try:
            if current_user.is_authenticated:
                user = current_user
        except Exception:
            pass

    # Récupérer les informations de la requête
    try:
        ip_address = request.remote_addr or 'N/A'
        user_agent = str(request.user_agent) or 'N/A'
        endpoint = request.endpoint or 'N/A'
        method = request.method or 'N/A'
        url = request.url or 'N/A'
    except RuntimeError:
        # Si appelé en dehors d'un contexte de requête
        ip_address = 'N/A'
        user_agent = 'N/A'
        endpoint = 'N/A'
        method = 'N/A'
        url = 'N/A'

    # ─── 1. Enregistrer dans la base de données ───
    try:
        activity = ActivityLog(
            user_id=user.id if user else None,
            user_email=user.email if user else 'Anonyme',
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent[:500],  # Limiter la taille
            endpoint=endpoint,
            method=method,
            url=url[:500]
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        # Si erreur BD, au moins logger dans le fichier
        current_app.logger.error(f'Erreur enregistrement activité BD: {e}')

    # ─── 2. Enregistrer dans le fichier log ───
    try:
        user_info = f'{user.email}' if user else 'Anonyme'
        log_message = f'{ip_address} - {user_info} - {action} - {details} - {method} {url}'
        current_app.logger.info(log_message)
    except Exception:
        pass


def log_request(response):
    """
    Middleware pour logger automatiquement TOUTES les requêtes HTTP.
    À utiliser avec app.after_request().
    
    Args:
        response: L'objet Response Flask.
    
    Returns:
        response: L'objet Response inchangé.
    """
    from flask import current_app

    try:
        # Ignorer les fichiers statiques (CSS, JS, images)
        if request.path.startswith('/static'):
            return response

        # Construire le message de log
        user_info = 'Anonyme'
        try:
            if current_user.is_authenticated:
                user_info = current_user.email
        except Exception:
            pass

        log_message = (
            f'{request.remote_addr} - {user_info} - '
            f'{request.method} {request.path} - '
            f'Status: {response.status_code} - '
            f'Agent: {request.user_agent.platform}/{request.user_agent.browser}'
        )

        # Niveau de log selon le code de statut
        if response.status_code >= 500:
            current_app.logger.error(log_message)
        elif response.status_code >= 400:
            current_app.logger.warning(log_message)
        else:
            current_app.logger.info(log_message)

    except Exception as e:
        current_app.logger.error(f'Erreur middleware logging: {e}')

    return response


def log_error(error):
    """
    Logger les erreurs non gérées.
    
    Args:
        error: L'exception capturée.
    """
    from flask import current_app

    try:
        user_info = 'Anonyme'
        try:
            if current_user.is_authenticated:
                user_info = current_user.email
        except Exception:
            pass

        current_app.logger.error(
            f'ERREUR - {request.remote_addr} - {user_info} - '
            f'{request.method} {request.path} - '
            f'Exception: {str(error)}'
        )
    except Exception:
        pass