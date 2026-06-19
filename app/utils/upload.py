"""
app/utils/upload.py
-------------------
Fonctions pour gérer l'upload et la suppression des photos d'événements.
"""

import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_image(filename):
    """
    Vérifie que le fichier possède une extension autorisée.
    """
    allowed_extensions = current_app.config.get(
        "ALLOWED_IMAGE_EXTENSIONS",
        {"png", "jpg", "jpeg", "gif", "webp"}
    )

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def ensure_upload_folder():
    """
    Vérifie que le dossier d'upload existe.
    Si UPLOAD_FOLDER n'existe pas dans la config, on crée une valeur par défaut.
    """

    upload_folder = current_app.config.get("UPLOAD_FOLDER")

    # Sécurité : si UPLOAD_FOLDER n'est pas défini dans config.py
    if not upload_folder:
        upload_folder = os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "events"
        )

        current_app.config["UPLOAD_FOLDER"] = upload_folder

    os.makedirs(upload_folder, exist_ok=True)

    return upload_folder


def save_event_photos(files, event_id):
    """
    Sauvegarde plusieurs photos pour un événement.

    Args:
        files: fichiers venant de request.files.getlist("photos")
        event_id: ID de l'événement

    Returns:
        tuple: (photos, errors)
    """

    from app.models.event_photo import EventPhoto

    upload_folder = ensure_upload_folder()

    photos = []
    errors = []

    for file in files:
        if not file or file.filename == "":
            continue

        if not allowed_image(file.filename):
            errors.append(
                f"Le fichier {file.filename} n'est pas une image autorisée."
            )
            continue

        original_filename = secure_filename(file.filename)

        if "." not in original_filename:
            errors.append(f"Le fichier {file.filename} n'a pas d'extension valide.")
            continue

        extension = original_filename.rsplit(".", 1)[1].lower()

        unique_filename = f"event_{event_id}_{uuid.uuid4().hex}.{extension}"

        file_path = os.path.join(upload_folder, unique_filename)

        file.save(file_path)

        photo = EventPhoto(
            event_id=event_id,
            filename=unique_filename,
            original_filename=original_filename
        )

        photos.append(photo)

    return photos, errors


def delete_event_photo_file(photo):
    """
    Supprime physiquement le fichier image du disque.
    """

    if not photo or not photo.filename:
        return

    upload_folder = current_app.config.get("UPLOAD_FOLDER")

    if not upload_folder:
        upload_folder = os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "events"
        )

    file_path = os.path.join(upload_folder, photo.filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass