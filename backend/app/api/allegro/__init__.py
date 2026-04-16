"""Allegro-specific API endpoints"""
from .auth import router as auth_router
from .offers import router as offers_router
from .offer_creation import router as offer_creation_router
from .promotions import router as promotions_router
from .price_schedules import router as price_schedules_router
from .images import router as images_router
from .templates import router as templates_router

__all__ = [
    "auth_router",
    "offers_router",
    "offer_creation_router",
    "promotions_router",
    "price_schedules_router",
    "images_router",
    "templates_router",
]
