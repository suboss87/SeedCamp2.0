"""
Persistence -- Backend Selector
Routes all database operations to the configured backend:
  - "memory" (default): In-memory store, no external dependencies
  - "firestore": Google Cloud Firestore (requires google-cloud-firestore)

Usage:
    from app.services.persistence import db
    campaign = await db.create_campaign(data)
"""

import importlib
import logging
import types

from app.config import settings

logger = logging.getLogger(__name__)


def _load_backend() -> types.ModuleType:
    """Load the persistence backend module based on config."""
    backend = settings.persistence_backend.lower()

    if backend == "firestore":
        try:
            return importlib.import_module("app.services.firestore_client")
        except ImportError:
            logger.warning(
                "Firestore requested but google-cloud-firestore not installed. "
                "Falling back to in-memory store. "
                "Install with: pip install google-cloud-firestore"
            )
            return importlib.import_module("app.services.memory_store")

    # Default: memory
    return importlib.import_module("app.services.memory_store")


db = _load_backend()
