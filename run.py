"""
run.py
------
Point d'entrée principal de l'application Flask.
Permet de lancer l'application en HTTP ou HTTPS selon la configuration.
"""

import os
from app import create_app

app = create_app()


def get_ssl_context():
    """
    Retourne le contexte SSL pour lancer Flask en HTTPS local.

    Si HTTPS_ENABLED=true :
        - Flask démarre en HTTPS.
        - Par défaut, un certificat auto-signé temporaire est généré.
    """
    if not app.config.get("HTTPS_ENABLED"):
        return None

    # Optionnel : si tu veux utiliser tes propres certificats
    cert_file = os.environ.get("SSL_CERT_FILE")
    key_file = os.environ.get("SSL_KEY_FILE")

    if cert_file and key_file:
        return cert_file, key_file

    # Certificat auto-signé généré automatiquement
    return "adhoc"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    debug = os.environ.get("FLASK_DEBUG", "1").lower() in ("1", "true", "yes", "on")

    ssl_context = get_ssl_context()

    if ssl_context:
        print(f"Application disponible sur : https://127.0.0.1:{port}")
    else:
        print(f"Application disponible sur : http://127.0.0.1:{port}")

    app.run(
        debug=debug,
        host="0.0.0.0",
        port=port,
        ssl_context=ssl_context
    )