"""
app/routes/event_routes.py
--------------------------
Routes pour la gestion des événements :
  - / : page d'accueil avec liste des événements
  - /event/<id> : détail d'un événement
  - /search : recherche d'événements
  - /admin/dashboard : tableau de bord administrateur
  - /admin/events : gestion CRUD des événements (admin)
  - /admin/events/add : ajout d'un événement
  - /admin/events/edit/<id> : modification d'un événement
  - /admin/events/delete/<id> : suppression d'un événement
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.event import Event
from app.models.booking import Booking
from app.models.user import User
from app.utils.auth import admin_required
from datetime import datetime
from app.utils.logger import log_activity 
from app.models.event_photo import EventPhoto
from app.utils.upload import save_event_photos, delete_event_photo_file

# Création du blueprint pour les routes des événements
event_bp = Blueprint('event', __name__)


# ═══════════════════════════════════════════════════════════
#  ROUTES PUBLIQUES (accessibles par tous les utilisateurs)
# ═══════════════════════════════════════════════════════════

@event_bp.route('/')
def index():
    """
    Page d'accueil : affiche la liste de tous les événements à venir,
    triés par date croissante. Possibilité de filtrer par catégorie.
    """
    categorie = request.args.get('categorie', '')
    page = request.args.get('page', 1, type=int)

    # Requête de base : événements futurs triés par date
    query = Event.query.filter(Event.date >= datetime.utcnow()).order_by(Event.date.asc())

    # Filtrage par catégorie si spécifié
    if categorie:
        query = query.filter(Event.categorie == categorie)

    # Pagination : 6 événements par page
    events = query.paginate(page=page, per_page=6, error_out=False)

    # Récupérer toutes les catégories distinctes pour le filtre
    categories = db.session.query(Event.categorie).distinct().all()
    categories = [c[0] for c in categories]

    return render_template('index.html',
                           events=events,
                           categories=categories,
                           selected_categorie=categorie)


@event_bp.route('/event/<int:event_id>')
def event_detail(event_id):
    """
    Page de détail d'un événement.
    Affiche toutes les informations et permet de réserver.
    """
    event = Event.query.get_or_404(event_id)
    return render_template('event_detail.html', event=event)


@event_bp.route('/search')
def search():
    """
    Recherche d'événements par mot-clé.
    Cherche dans le titre, la description et le lieu.
    """
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    if query:
        # Recherche insensible à la casse dans titre, description et lieu
        search_filter = Event.query.filter(
            db.or_(
                Event.titre.ilike(f'%{query}%'),
                Event.description.ilike(f'%{query}%'),
                Event.lieu.ilike(f'%{query}%')
            )
        ).filter(Event.date >= datetime.utcnow()).order_by(Event.date.asc())

        results = search_filter.paginate(page=page, per_page=6, error_out=False)
    else:
        results = None

    return render_template('search_results.html', results=results, query=query)


# ═══════════════════════════════════════════════════════════
#  ROUTES ADMINISTRATEUR (accès restreint aux admins)
# ═══════════════════════════════════════════════════════════

@event_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    Tableau de bord administrateur.
    Affiche des statistiques sur les événements, réservations et utilisateurs.
    """
    # Statistiques globales
    total_events = Event.query.count()
    total_bookings = Booking.query.count()
    total_users = User.query.filter_by(role='user').count()
    confirmed_bookings = Booking.query.filter_by(statut='confirme').count()
    pending_bookings = Booking.query.filter_by(statut='en_attente').count()
    cancelled_bookings = Booking.query.filter_by(statut='annule').count()

    # Calcul du revenu total (réservations confirmées)
    revenue = db.session.query(db.func.sum(Booking.montant_total)).filter_by(statut='confirme').scalar() or 0

    # 5 prochains événements
    upcoming_events = Event.query.filter(
        Event.date >= datetime.utcnow()
    ).order_by(Event.date.asc()).limit(5).all()

    # 10 dernières réservations
    recent_bookings = Booking.query.order_by(
        Booking.date_reservation.desc()
    ).limit(10).all()

    return render_template('admin_dashboard.html',
                           total_events=total_events,
                           total_bookings=total_bookings,
                           total_users=total_users,
                           confirmed_bookings=confirmed_bookings,
                           pending_bookings=pending_bookings,
                           cancelled_bookings=cancelled_bookings,
                           revenue=revenue,
                           upcoming_events=upcoming_events,
                           recent_bookings=recent_bookings)


@event_bp.route('/admin/events')
@login_required
@admin_required
def admin_events():
    """
    Liste de tous les événements pour l'administrateur.
    Permet d'ajouter, modifier ou supprimer des événements.
    """
    page = request.args.get('page', 1, type=int)
    events = Event.query.order_by(Event.date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin_events.html', events=events)


@event_bp.route('/admin/events/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_event():
    """
    Ajout d'un nouvel événement par l'administrateur.
    GET : affiche le formulaire.
    POST : valide et crée l'événement.
    """
    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        description = request.form.get('description', '').strip()
        date_str = request.form.get('date', '')
        lieu = request.form.get('lieu', '').strip()
        prix = request.form.get('prix', 0, type=float)
        capacite = request.form.get('capacite', 0, type=int)
        categorie = request.form.get('categorie', 'Général').strip()
        image_url = request.form.get('image_url', '').strip()

        # ─── Validation ───
        errors = []
        if not titre:
            errors.append('Le titre est obligatoire.')
        if not description:
            errors.append('La description est obligatoire.')
        if not date_str:
            errors.append('La date est obligatoire.')
        if not lieu:
            errors.append('Le lieu est obligatoire.')
        if prix < 0:
            errors.append('Le prix ne peut pas être négatif.')
        if capacite <= 0:
            errors.append('La capacité doit être supérieure à 0.')

        # Convertir la date
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            errors.append('Format de date invalide.')
            event_date = None

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('admin_event_form.html', action='add',
                                   titre=titre, description=description,
                                   lieu=lieu, prix=prix, capacite=capacite,
                                   categorie=categorie, image_url=image_url)

        # ─── Création de l'événement ───
        new_event = Event(
            titre=titre,
            description=description,
            date=event_date,
            lieu=lieu,
            prix=prix,
            capacite=capacite,
            places_disponibles=capacite,
            categorie=categorie,
            image_url=image_url
        )

        db.session.add(new_event)

        # Permet d'obtenir new_event.id avant le commit final
        db.session.flush()

        # Gestion des photos uploadées
        uploaded_files = request.files.getlist("photos")

        photos, photo_errors = save_event_photos(uploaded_files, new_event.id)

        for photo in photos:
            db.session.add(photo)

        db.session.commit()

        for error in photo_errors:
            flash(error, "warning")

        if photos:
            flash(f"{len(photos)} photo(s) ajoutée(s) à l'événement.", "success")

        flash(f'Événement « {titre} » créé avec succès !', 'success')
        return redirect(url_for('event.admin_events'))
                
        log_activity(
            'EVENT_CREATED',
            f'Événement créé : "{titre}" — Date: {event_date} — '
            f'Lieu: {lieu} — Capacité: {capacite} — Prix: {prix}$'
        )



        flash(f'Événement « {titre} » créé avec succès !', 'success')
        return redirect(url_for('event.admin_events'))

    return render_template('admin_event_form.html', action='add')


@event_bp.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_event(event_id):
    """
    Modification d'un événement existant.
    GET : pré-remplit le formulaire avec les données actuelles.
    POST : applique les modifications.
    """
    event = Event.query.get_or_404(event_id)

    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        description = request.form.get('description', '').strip()
        date_str = request.form.get('date', '')
        lieu = request.form.get('lieu', '').strip()
        prix = request.form.get('prix', 0, type=float)
        capacite = request.form.get('capacite', 0, type=int)
        categorie = request.form.get('categorie', 'Général').strip()
        image_url = request.form.get('image_url', '').strip()

        # Validation
        errors = []
        if not titre:
            errors.append('Le titre est obligatoire.')
        if not description:
            errors.append('La description est obligatoire.')
        if capacite <= 0:
            errors.append('La capacité doit être supérieure à 0.')

        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            errors.append('Format de date invalide.')
            event_date = event.date

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('admin_event_form.html', action='edit', event=event)

        # Calculer le changement de capacité
        # Si la capacité augmente, les places disponibles augmentent d'autant
        difference = capacite - event.capacite
        new_places_disponibles = max(0, event.places_disponibles + difference)

        # Appliquer les modifications
        event.titre = titre
        event.description = description
        event.date = event_date
        event.lieu = lieu
        event.prix = prix
        event.capacite = capacite
        event.places_disponibles = new_places_disponibles
        event.categorie = categorie
        event.image_url = image_url

        # Gestion des nouvelles photos ajoutées lors de la modification
        uploaded_files = request.files.getlist("photos")

        photos, photo_errors = save_event_photos(uploaded_files, event.id)

        for photo in photos:
            db.session.add(photo)

        db.session.commit()
        for error in photo_errors:
            flash(error, "warning")

        if photos:
            flash(f"{len(photos)} nouvelle(s) photo(s) ajoutée(s).", "success")



        log_activity(
            'EVENT_UPDATED',
            f'Événement #{event.id} modifié : "{titre}"'
        )



        flash(f'Événement « {titre} » modifié avec succès !', 'success')
        return redirect(url_for('event.admin_events'))

    return render_template('admin_event_form.html', action='edit', event=event)


@event_bp.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_event(event_id):
    """
    Suppression d'un événement.
    Toutes les réservations associées seront supprimées en cascade.
    """
    event = Event.query.get_or_404(event_id)
    titre = event.titre

    # Supprimer aussi les fichiers photos associés
    for photo in event.photos:
        delete_event_photo_file(photo)

    db.session.delete(event)
    db.session.commit()


    log_activity('EVENT_DELETED', f'Événement supprimé : "{titre}" (ID:{event_id})')

    flash(f'Événement « {titre} » supprimé avec succès.', 'success')
    return redirect(url_for('event.admin_events'))


@event_bp.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings():
    """
    Affiche toutes les réservations pour l'administrateur.
    Permet de voir le statut de chaque réservation.
    """
    page = request.args.get('page', 1, type=int)
    statut_filter = request.args.get('statut', '')

    query = Booking.query.order_by(Booking.date_reservation.desc())

    if statut_filter:
        query = query.filter_by(statut=statut_filter)

    bookings = query.paginate(page=page, per_page=15, error_out=False)

    return render_template('admin_bookings.html', bookings=bookings, selected_statut=statut_filter)


@event_bp.route('/admin/bookings/<int:booking_id>/confirm', methods=['POST'])
@login_required
@admin_required
def admin_confirm_booking(booking_id):
    """Confirme une réservation en attente (admin)."""
    booking = Booking.query.get_or_404(booking_id)
    if booking.statut == 'en_attente':
        booking.statut = 'confirme'
        db.session.commit()

        log_activity(
            'ADMIN_CONFIRM_BOOKING',
            f'Réservation #{booking.id} confirmée par admin'
        )

        flash(f'Réservation #{booking.id} confirmée.', 'success')
    else:
        flash('Cette réservation ne peut pas être confirmée.', 'warning')
    return redirect(url_for('event.admin_bookings'))


@event_bp.route('/admin/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@admin_required
def admin_cancel_booking(booking_id):
    """Annule une réservation (admin). Restitue les places disponibles."""
    booking = Booking.query.get_or_404(booking_id)
    if booking.statut != 'annule':
        booking.statut = 'annule'
        # Restituer les places
        event = Event.query.get(booking.event_id)
        if event:
            event.places_disponibles += booking.nombre_places
        db.session.commit()

        log_activity(
            'ADMIN_CANCEL_BOOKING',
            f'Réservation #{booking.id} annulée par admin — '
            f'{booking.nombre_places} place(s) restituées'
        )

        flash(f'Réservation #{booking.id} annulée.', 'success')
    else:
        flash('Cette réservation est déjà annulée.', 'warning')
    return redirect(url_for('event.admin_bookings'))

@event_bp.route('/admin/logs')
@login_required
@admin_required
def admin_logs():
    """
    Page administrateur permettant de consulter le journal d'activités.
    Accessible uniquement aux administrateurs.
    """

    from app.models.activity_log import ActivityLog
    from sqlalchemy import or_

    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    search = request.args.get('search', '').strip()

    # Requête de base : les logs les plus récents d'abord
    query = ActivityLog.query.order_by(ActivityLog.timestamp.desc())

    # Filtrer par action si demandé
    if action_filter:
        query = query.filter(ActivityLog.action == action_filter)

    # Recherche par email, IP ou détails
    if search:
        query = query.filter(
            or_(
                ActivityLog.user_email.ilike(f'%{search}%'),
                ActivityLog.ip_address.ilike(f'%{search}%'),
                ActivityLog.details.ilike(f'%{search}%')
            )
        )

    # Pagination : 25 logs par page
    logs = query.paginate(page=page, per_page=25, error_out=False)

    # Liste des actions disponibles pour le filtre
    actions_query = db.session.query(ActivityLog.action).distinct().order_by(ActivityLog.action).all()
    actions = [a[0] for a in actions_query]

    # Optionnel : enregistrer le fait que l'admin consulte les logs
    try:
        from app.utils.logger import log_activity
        log_activity('VIEW_LOGS', 'Consultation du journal d’activités par un administrateur')
    except Exception:
        pass

    return render_template(
        'admin_logs.html',
        logs=logs,
        actions=actions,
        selected_action=action_filter,
        search=search
    )


@event_bp.route(
    "/admin/events/<int:event_id>/photos/<int:photo_id>/delete",
    methods=["POST"]
)
@login_required
@admin_required
def admin_delete_event_photo(event_id, photo_id):
    """
    Supprime une photo d'un événement.
    Accessible uniquement à l'administrateur.
    """
    event = Event.query.get_or_404(event_id)

    photo = EventPhoto.query.filter_by(
        id=photo_id,
        event_id=event.id
    ).first_or_404()

    # Supprimer le fichier physique
    delete_event_photo_file(photo)

    # Supprimer l'entrée en base
    db.session.delete(photo)
    db.session.commit()

    flash("Photo supprimée avec succès.", "success")

    return redirect(url_for("event.admin_edit_event", event_id=event.id))