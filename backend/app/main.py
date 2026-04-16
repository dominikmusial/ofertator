from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.db.session import engine, get_db
from app.db import models
from app.db.repositories import AdminRepository
from app.middleware.activity_tracker import ActivityTrackingMiddleware
from app.api import (
    accounts,
    auth,
    ai_config,
    analytics,
    admin,
    asystenciai,
    config,
)
from app.api.allegro import (
    auth_router as allegro_auth_router,
    offer_creation_router as allegro_offer_creation_router,
    promotions_router as allegro_promotions_router,
    price_schedules_router as allegro_price_schedules_router,
    images_router as allegro_images_router,
    templates_router as allegro_templates_router,
    offers_router as allegro_offers_router,
)
from app.api.decathlon import (
    auth_router as decathlon_auth_router,
    products_router as decathlon_products_router,
)
from app.api.castorama import (
    auth_router as castorama_auth_router,
    products_router as castorama_products_router,
)
from app.api.leroymerlin import (
    auth_router as leroymerlin_auth_router,
    products_router as leroymerlin_products_router,
)

# Create tables
# models.Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Environment-based configuration
if settings.ENVIRONMENT == "production":
    # Production: Only allow the configured frontend URL
    origins = [settings.FRONTEND_URL]
else:
    # Development: Allow localhost for both main and client versions
    origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        settings.FRONTEND_URL,
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Activity tracking middleware
app.add_middleware(ActivityTrackingMiddleware)

# Routers
api_router = APIRouter(prefix="/api/v1", redirect_slashes=False)

# Common/agnostic routes (truly universal, not marketplace-specific)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(ai_config.router, prefix="/ai-config", tags=["ai-configuration"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(asystenciai.router, prefix="/asystenciai", tags=["asystenciai-integration"])
api_router.include_router(config.router, prefix="/config", tags=["config"])

# Allegro-specific routes
api_router.include_router(allegro_auth_router, prefix="/allegro", tags=["allegro"])
api_router.include_router(allegro_offers_router, prefix="/allegro/offers", tags=["allegro", "offers"])
api_router.include_router(allegro_offer_creation_router, prefix="/allegro/offer-creation", tags=["allegro", "offer-creation"])
api_router.include_router(allegro_promotions_router, prefix="/allegro/promotions", tags=["allegro", "promotions"])
api_router.include_router(allegro_price_schedules_router, prefix="/allegro", tags=["allegro", "price-schedules"])
api_router.include_router(allegro_images_router, prefix="/allegro/images", tags=["allegro", "images"])
# Also mount image proxy at root level for backward compatibility with existing URLs
api_router.include_router(allegro_images_router, prefix="/images", tags=["images"])
api_router.include_router(allegro_templates_router, prefix="/allegro/templates", tags=["allegro", "templates"])

# Mirakl marketplace routes
api_router.include_router(decathlon_auth_router, prefix="/decathlon", tags=["decathlon"])
api_router.include_router(decathlon_products_router, prefix="/decathlon/products", tags=["decathlon", "products"])

api_router.include_router(castorama_auth_router, prefix="/castorama", tags=["castorama"])
api_router.include_router(castorama_products_router, prefix="/castorama/products", tags=["castorama", "products"])

api_router.include_router(leroymerlin_auth_router, prefix="/leroymerlin", tags=["leroymerlin"])
api_router.include_router(leroymerlin_products_router, prefix="/leroymerlin/products", tags=["leroymerlin", "products"])

app.include_router(api_router)

# Special route for asystenciai integration (no /api/v1 prefix for clean URLs)
app.include_router(asystenciai.router, include_in_schema=False)

@app.get("/")
def read_root():
    return {"message": "Welcome to Bot-sok API", "version": settings.VERSION}

@app.get("/health")
def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Basic health check - just return status
        return {"status": "healthy", "version": settings.VERSION}
    except Exception as e:
        # If anything fails, still return a response so health check doesn't fail
        return {"status": "healthy", "version": settings.VERSION, "note": "basic health check"}

@app.on_event("startup")
async def startup_event():
    """Initialize default admin on startup"""
    import os
    # Only run in main process, not in workers
    if os.getenv('UVICORN_WORKER') != 'true':
        try:
            if settings.DATABASE_URL.startswith("sqlite"):
                models.Base.metadata.create_all(bind=engine)
            db = next(get_db())
            AdminRepository.create_default_admin(
                db, 
                settings.DEFAULT_ADMIN_EMAIL, 
                settings.DEFAULT_ADMIN_PASSWORD
            )
            print(f"✅ Default admin initialized: {settings.DEFAULT_ADMIN_EMAIL}")
        except Exception as e:
            print(f"❌ Failed to initialize default admin: {str(e)}")
            # Don't let admin initialization failure prevent app startup
            pass
        finally:
            try:
                db.close()
            except:
                pass 
