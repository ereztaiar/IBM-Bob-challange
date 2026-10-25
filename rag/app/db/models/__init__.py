"""Model registry — import all RAG models so Alembic can discover them."""

from app.db.models.scan_embedding import ScanEmbedding
from app.db.models.vulnerability_doc import VulnerabilityDoc

__all__ = ["VulnerabilityDoc", "ScanEmbedding"]
