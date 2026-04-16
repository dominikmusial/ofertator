# Marketplace Infrastructure

This directory contains the marketplace provider infrastructure implementing the **Provider Pattern** for multi-marketplace support.

## Architecture Overview

```
Domain Layer (API endpoints, Tasks, Services)
    ↓ uses
MarketplaceFactory
    ↓ creates (via Strategy Pattern)
IMarketplaceProvider (minimal interface)
    ↓ implemented by
Marketplace Providers (isolated, self-contained)
    ├── allegro/   → AllegroMarketplaceClient + services
    ├── decathlon/ → DecathlonMarketplaceClient
    └── [future marketplaces]
```

## Core Components

### 1. `base.py` - Interface Definition
Defines `IMarketplaceProvider` interface with minimal common operations:
- `refresh_token()`, `create_offer()`, `get_offer()`, `update_offer()`
- `list_offers()`, `upload_image()`, `get_categories()`
- `get_marketplace_type()`, `get_capabilities()`, `normalize_error()`

Marketplace-specific features (e.g., Allegro promotions, Amazon FBA) are **NOT** in the interface - use composition instead.

### 2. `config.py` - Configuration Strategy
Marketplace-specific configuration classes handle:
- Provider initialization (e.g., Decathlon needs shop_id)
- Token preparation (e.g., Decathlon API keys need decryption)

### 3. `factory.py` - Provider Factory
Creates provider instances using Strategy Pattern:
- No if/else chains for marketplace-specific logic
- Each marketplace owns its initialization via config class
- Easy to extend without modifying factory

### 4. Marketplace Folders
Each marketplace has its own folder with:
- `client.py` - Provider implementation
- `auth.py` - OAuth/API key authentication
- `api.py` - API client functions
- `services/` - Marketplace-specific business logic
- `tasks/` - Celery tasks (optional)

## Adding a New Marketplace

Follow these steps to add support for a new marketplace (e.g., Amazon):

### Step 1: Add Marketplace Type to Database

Edit `backend/app/db/models.py`:

```python
class MarketplaceType(str, enum.Enum):
    allegro = "allegro"
    decathlon = "decathlon"
    amazon = "amazon"  # Add new marketplace
```

### Step 2: Create Marketplace Folder Structure

```bash
mkdir -p backend/app/infrastructure/marketplaces/amazon
touch backend/app/infrastructure/marketplaces/amazon/__init__.py
touch backend/app/infrastructure/marketplaces/amazon/client.py
touch backend/app/infrastructure/marketplaces/amazon/auth.py
touch backend/app/infrastructure/marketplaces/amazon/api.py
```

### Step 3: Implement Provider Client

Create `amazon/client.py`:

```python
from app.infrastructure.marketplaces.base import IMarketplaceProvider, MarketplaceType
from typing import List, Optional, Dict

class AmazonMarketplaceClient(IMarketplaceProvider):
    """Amazon marketplace provider implementation"""
    
    def __init__(self, access_token: str, seller_id: str = None):
        self.access_token = access_token
        self.seller_id = seller_id
    
    def supports_token_refresh(self) -> bool:
        return True  # Amazon uses OAuth
    
    def refresh_token(self, refresh_token: str) -> dict:
        # Implement Amazon token refresh
        pass
    
    def create_offer(self, offer_data: dict) -> dict:
        # Implement Amazon product creation
        pass
    
    # ... implement all interface methods
    
    def get_marketplace_type(self) -> MarketplaceType:
        return MarketplaceType.amazon
    
    def get_capabilities(self) -> dict:
        return {
            'supports_fba': True,
            'max_images': 9,
            'supports_variations': True,
        }
    
    # Amazon-specific methods (not in interface)
    def get_fba_inventory(self) -> List[Dict]:
        """Amazon-specific: Get FBA inventory"""
        pass
```

### Step 4: Create Configuration Strategy

Edit `config.py` and add Amazon config:

```python
class AmazonConfig(MarketplaceConfig):
    """Configuration for Amazon marketplace"""
    
    def create_provider_instance(
        self, 
        provider_class: type, 
        access_token: str, 
        marketplace_data: Dict[str, Any]
    ) -> IMarketplaceProvider:
        seller_id = marketplace_data.get('seller_id')
        return provider_class(access_token, seller_id)
    
    def prepare_access_token(self, raw_token: str) -> str:
        # Amazon tokens may need special handling
        return raw_token

# Register in MARKETPLACE_CONFIGS
MARKETPLACE_CONFIGS = {
    'allegro': AllegroConfig(),
    'decathlon': DecathlonConfig(),
    'amazon': AmazonConfig(),  # Add here
}
```

### Step 5: Register in Factory

Edit `factory.py`:

```python
from .amazon.client import AmazonMarketplaceClient  # Import client

class MarketplaceFactory:
    _providers = {
        MarketplaceType.allegro: {
            'class': AllegroMarketplaceClient,
            'config_key': 'allegro'
        },
        MarketplaceType.decathlon: {
            'class': DecathlonMarketplaceClient,
            'config_key': 'decathlon'
        },
        MarketplaceType.amazon: {  # Register here
            'class': AmazonMarketplaceClient,
            'config_key': 'amazon'
        },
    }
```

### Step 6: Create API Auth Endpoints

Create `backend/app/api/amazon/auth.py`:

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.infrastructure.marketplaces.amazon import auth as amazon_auth
from app.db.models import MarketplaceType

router = APIRouter()

@router.post("/authorize")
async def authorize_amazon_account(
    authorization_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    # Implement OAuth redirect flow
    tokens = amazon_auth.exchange_code_for_tokens(authorization_code)
    
    # Create account
    account = Account(
        nazwa_konta=tokens['seller_name'],
        access_token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        token_expires_at=datetime.utcnow() + timedelta(seconds=tokens['expires_in']),
        marketplace_type=MarketplaceType.amazon,
        marketplace_specific_data={'seller_id': tokens['seller_id']}
    )
    db.add(account)
    db.commit()
    
    return {"status": "success", "account_id": account.id}
```

### Step 7: Register API Routes

Edit `backend/app/main.py`:

```python
from app.api.amazon import auth_router as amazon_auth_router

# Add to routers
api_router.include_router(amazon_auth_router, prefix="/amazon", tags=["amazon"])
```

### Step 8: (Optional) Add Celery Tasks

If marketplace needs background tasks:

```bash
mkdir -p backend/app/infrastructure/marketplaces/amazon/tasks
touch backend/app/infrastructure/marketplaces/amazon/tasks/__init__.py
```

Edit `backend/app/celery_worker.py`:

```python
celery = Celery(
    include=[
        'app.tasks',
        'app.infrastructure.marketplaces.allegro.tasks',
        'app.infrastructure.marketplaces.amazon.tasks',  # Add here
    ]
)
```

### Step 9: Update Frontend

Add marketplace type to frontend:
- Update `MarketplaceType` enum in frontend types
- Add Amazon-specific auth flow components
- Add marketplace badges/labels for Amazon
- Handle Amazon-specific features in UI

### Step 10: Database Migration

Create Alembic migration:

```bash
cd backend
alembic revision -m "add_amazon_marketplace_type"
```

The migration should already work since `MarketplaceType` enum is updated automatically.

## Testing New Marketplace

1. **Unit Tests**: Test provider client methods independently
2. **Integration Tests**: Test full flow (auth → create account → list offers)
3. **Manual Testing**: Use Postman/frontend to test auth flow
4. **Capability Tests**: Verify marketplace-specific features work

## Key Principles

1. **Minimal Interface**: Only common operations in `IMarketplaceProvider`
2. **Composition Over Inheritance**: Marketplace-specific features as additional methods
3. **Strategy Pattern**: Config classes handle initialization differences
4. **Isolated Modules**: Marketplaces don't depend on each other
5. **Easy Extensibility**: Add marketplace without modifying factory logic

## Examples

### Using Factory to Get Provider

```python
from app.infrastructure.marketplaces.factory import factory
from app.infrastructure.marketplaces.base import MarketplaceType

# Method 1: Direct creation
provider = factory.get_provider(
    marketplace_type=MarketplaceType.amazon,
    access_token="amazon_token_here",
    marketplace_specific_data={'seller_id': 'ABC123'}
)

# Method 2: From database account
provider = factory.get_provider_for_account(db, account_id=123)

# Use provider
offers = provider.list_offers({'status': 'active'})
```

### Checking Marketplace Capabilities

```python
capabilities = provider.get_capabilities()

if capabilities.get('supports_fba'):
    # Amazon-specific FBA operations
    if hasattr(provider, 'get_fba_inventory'):
        inventory = provider.get_fba_inventory()
```

### Marketplace-Specific Error Handling

```python
try:
    provider.create_offer(offer_data)
except Exception as e:
    # Normalize error to user-friendly message
    error_message = provider.normalize_error(e)
    raise HTTPException(status_code=400, detail=error_message)
```

## Troubleshooting

### "Unsupported marketplace" Error
- Check `MarketplaceType` enum includes new marketplace
- Verify marketplace registered in `factory._providers`
- Confirm config registered in `config.MARKETPLACE_CONFIGS`

### Token Refresh Failing
- Implement `supports_token_refresh()` and `refresh_token()` in provider
- Check token expiry logic in config `prepare_access_token()`
- Verify OAuth flow in `auth.py` returns correct token format

### Provider Method Not Working
- Ensure method implements interface correctly (check signatures)
- Review marketplace API documentation
- Add logging to debug API responses
- Use `normalize_error()` to provide user-friendly messages
