"""Model registry — import all models so Alembic can discover them."""

from app.db.models.admin import Admin
from app.db.models.finding import Finding
from app.db.models.scan import Scan

__all__ = ["Admin", "Scan", "Finding"]
