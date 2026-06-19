"""
app/models/__init__.py
----------------------
Package des modèles de données.
Importe tous les modèles pour faciliter l'accès.
"""

from app.models.user import User
from app.models.event import Event
from app.models.booking import Booking
from app.models.activity_log import ActivityLog 
from app.models.event_photo import EventPhoto