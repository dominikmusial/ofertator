"""
Central Celery tasks module.

NOTE: This file used to be a "God Object" containing all tasks.
It has been refactored to use modular architecture.

- Marketplace-specific tasks are now in: app.infrastructure.marketplaces.<marketplace>.tasks
- They are automatically loaded by Celery via 'include' in celery_worker.py
- API endpoints should import tasks directly from their source modules.

This file is kept for:
1. Shared, system-wide tasks (e.g. database cleanup, email sending) that don't belong to a specific domain.
2. Backward compatibility (if any external scripts import from here - though they should be updated).
"""
import logging
from .celery_worker import celery

logger = logging.getLogger(__name__)

# Place shared system tasks here
