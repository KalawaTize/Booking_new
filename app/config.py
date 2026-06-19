import os
from dotenv import load_dotenv

load_dotenv()


def str_to_bool(value, default=False):
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY manquante. Ajoutez SECRET_KEY dans le fichier .env"
        )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///ticket_booking.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # ==============================
    # CONFIGURATION HTTPS si tu l'utilises
    # ==============================
    HTTPS_ENABLED = str_to_bool(os.environ.get("HTTPS_ENABLED"), False)
    FORCE_HTTPS = str_to_bool(os.environ.get("FORCE_HTTPS"), False)
    USE_PROXY_FIX = str_to_bool(os.environ.get("USE_PROXY_FIX"), False)

    PREFERRED_URL_SCHEME = "https" if (HTTPS_ENABLED or FORCE_HTTPS) else "http"

    SESSION_COOKIE_SECURE = str_to_bool(
        os.environ.get("SESSION_COOKIE_SECURE"),
        HTTPS_ENABLED or FORCE_HTTPS
    )

    REMEMBER_COOKIE_SECURE = str_to_bool(
        os.environ.get("REMEMBER_COOKIE_SECURE"),
        HTTPS_ENABLED or FORCE_HTTPS
    )

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ==============================
    # UPLOAD DES PHOTOS D'ÉVÉNEMENTS
    # ==============================

    # Chemin racine du projet : C:\Booking_new
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Dossier où les photos seront stockées
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        os.path.join(BASE_DIR, "app", "static", "uploads", "events")
    )

    # Extensions autorisées
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Taille maximale : 16 Mo
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024