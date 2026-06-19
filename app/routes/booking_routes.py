"""
app/routes/booking_routes.py
----------------------------
Routes pour la gestion des réservations :
  - /book/<event_id> : formulaire de réservation
  - /payment/<booking_id> : simulation de paiement sécurisé
  - /my-bookings : tableau de bord utilisateur avec ses réservations
  - /booking/cancel/<booking_id> : annulation d'une réservation
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.event import Event
from app.models.booking import Booking

# Création du blueprint pour les routes de réservation
booking_bp = Blueprint('booking', __name__)


@booking_bp.route('/book/<int:event_id>', methods=['GET', 'POST'])
@login_required
def book_event(event_id):
    """
    Réservation de billets pour un événement.
    GET : affiche le formulaire avec la sélection du nombre de places.
    POST : crée la réservation et redirige vers le paiement.
    """
    event = Event.query.get_or_404(event_id)

    # Vérifier que l'événement n'est pas passé
    if event.is_past():
        flash('Cet événement est déjà passé.', 'warning')
        return redirect(url_for('event.event_detail', event_id=event.id))

    # Vérifier qu'il reste des places
    if not event.is_available():
        flash('Désolé, il n\'y a plus de places disponibles pour cet événement.', 'danger')
        return redirect(url_for('event.event_detail', event_id=event.id))

    if request.method == 'POST':
        nombre_places = request.form.get('nombre_places', 1, type=int)

        # ─── Validation ───
        if nombre_places <= 0:
            flash('Le nombre de places doit être au moins 1.', 'danger')
            return render_template('book_event.html', event=event)

        if nombre_places > event.places_disponibles:
            flash(f'Il ne reste que {event.places_disponibles} place(s) disponible(s).', 'danger')
            return render_template('book_event.html', event=event)

        # Limiter à 10 places par réservation
        if nombre_places > 10:
            flash('Vous ne pouvez réserver que 10 places maximum par réservation.', 'danger')
            return render_template('book_event.html', event=event)

        # ─── Calcul du montant total ───
        montant_total = event.prix * nombre_places

        # ─── Création de la réservation (statut = en_attente) ───
        booking = Booking(
            user_id=current_user.id,
            event_id=event.id,
            nombre_places=nombre_places,
            statut='en_attente',
            montant_total=montant_total
        )

        # Réduire le nombre de places disponibles
        event.places_disponibles -= nombre_places

        db.session.add(booking)
        db.session.commit()

        flash('Réservation créée ! Veuillez procéder au paiement.', 'info')
        return redirect(url_for('booking.payment', booking_id=booking.id))

    return render_template('book_event.html', event=event)


@booking_bp.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def payment(booking_id):
    """
    Simulation de paiement sécurisé.
    GET : affiche le formulaire de paiement (simulation).
    POST : confirme le paiement et change le statut de la réservation à 'confirme'.
    
    NOTE : Ceci est une SIMULATION. Dans un vrai projet, on utiliserait
    Stripe, PayPal ou un autre service de paiement.
    """
    booking = Booking.query.get_or_404(booking_id)

    # Vérifier que la réservation appartient à l'utilisateur courant
    if booking.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('booking.my_bookings'))

    # Vérifier que la réservation est en attente de paiement
    if booking.statut != 'en_attente':
        flash('Cette réservation a déjà été traitée.', 'warning')
        return redirect(url_for('booking.my_bookings'))

    if request.method == 'POST':
        # ─── Simulation du paiement ───
        card_number = request.form.get('card_number', '').replace(' ', '')
        card_name = request.form.get('card_name', '').strip()
        expiry = request.form.get('expiry', '').strip()
        cvv = request.form.get('cvv', '').strip()

        # Validation basique du formulaire de paiement (simulation)
        errors = []
        if not card_number or len(card_number) < 16:
            errors.append('Numéro de carte invalide (16 chiffres requis).')
        if not card_name:
            errors.append('Le nom sur la carte est requis.')
        if not expiry:
            errors.append('La date d\'expiration est requise.')
        if not cvv or len(cvv) < 3:
            errors.append('Le CVV est invalide (3 chiffres requis).')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('payment.html', booking=booking)

        # ─── Paiement accepté (simulation) ───
        booking.statut = 'confirme'
        db.session.commit()

        flash('Paiement accepté ! Votre réservation est confirmée. 🎉', 'success')
        return redirect(url_for('booking.my_bookings'))

    return render_template('payment.html', booking=booking)


@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    """
    Tableau de bord utilisateur.
    Affiche toutes les réservations de l'utilisateur connecté,
    triées par date de réservation décroissante.
    """
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(
        Booking.date_reservation.desc()
    ).all()

    return render_template('my_bookings.html', bookings=bookings)


@booking_bp.route('/booking/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """
    Annulation d'une réservation par l'utilisateur.
    Restitue les places à l'événement et change le statut à 'annule'.
    """
    booking = Booking.query.get_or_404(booking_id)

    # Vérifier que la réservation appartient à l'utilisateur courant
    if booking.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('booking.my_bookings'))

    # Vérifier que la réservation peut être annulée
    if booking.statut == 'annule':
        flash('Cette réservation est déjà annulée.', 'warning')
        return redirect(url_for('booking.my_bookings'))

    # ─── Annulation ───
    booking.statut = 'annule'

    # Restituer les places disponibles à l'événement
    event = Event.query.get(booking.event_id)
    if event:
        event.places_disponibles += booking.nombre_places

    db.session.commit()

    flash('Votre réservation a été annulée avec succès.', 'success')
    return redirect(url_for('booking.my_bookings'))