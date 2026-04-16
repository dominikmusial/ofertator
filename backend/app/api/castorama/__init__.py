"""Castorama API endpoints"""
from .auth import router as auth_router
from .products import router as products_router

__all__ = ['auth_router', 'products_router']
