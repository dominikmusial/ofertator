# Multi-Marketplace Refactor - Context

**Quick Facts**:
- **Status**: ✅ Backend refactor completed, Frontend partially migrated
- **Current**: Supports Allegro and Decathlon with clean architecture
- **Goal**: Support 5+ marketplaces (Allegro, Decathlon, Amazon, eMAG, Kaufland, etc.)
- **Approach**: Modular Provider Architecture (industry standard)
- **Completed**: Backend infrastructure, API endpoints, tasks, services migrated

---

## Why This is Complex

After comprehensive analysis, this affects:
- **30 Celery tasks** (4,909 lines in tasks.py)
- **15 API modules** calling Allegro API
- **29 frontend pages** (10 need marketplace awareness)
- **126 activity tracking actions** (all have "allegro" prefix)
- **Account sharing** between team members
- **Different OAuth flows** per marketplace (Device Code vs Redirect vs API Key)
- **Module permissions** system (`konta_allegro` is a permission module)

---

## System Overview

### Account Creation
1. User clicks "Add Account"
2. **Allegro**: Device Code Flow (poll for token, user authorizes on Allegro)
3. **Future Amazon**: Redirect Flow (user redirected, comes back with code)
4. **Future eMAG**: API Key (no OAuth)
5. Creates `Account` + `UserAllegroAccount` (links user to account)
6. For vsprint employees: auto-shares with team

### Core Features
- **Offer Editor** (1855 lines) - Template-based descriptions with AI
- **Copy Offers** - Between accounts (same or different marketplace)
- **Bulk Operations** - 30 Celery tasks for titles, images, prices, promotions, etc.
- **Templates** - JSON structure with HTML (sanitization rules differ per marketplace)
- **AI Integration** - Anthropic/Google for content generation
- **Image Processing** - MinIO storage, frames, backgrounds, composites
- **Price Scheduling** - Automated price changes
- **Analytics** - Activity tracking, AI token usage, team dashboards

### Database Key Tables
- `accounts` - Tokens, marketplace_type (NEW), marketplace_specific_data (NEW)
- `user_allegro_accounts` → **RENAME** to `user_marketplace_accounts`
- `modules` - Permission system, `konta_allegro` → **RENAME** to `konta_marketplace`
- `templates`, `offer_backups`, `account_images`, `ai_token_usage`, `user_activity_logs`

---

## Architecture Pattern: Modular Provider (✅ IMPLEMENTED)

**Industry Standard** (ChannelEngine, Linnworks, Stripe):

```
Domain Layer (API endpoints, Tasks, Services)
    ↓ uses factory
MarketplaceFactory
    ↓ creates
IMarketplaceProvider (minimal interface)
    ↓ implemented by
Marketplace Providers (isolated, self-contained)
    ├── allegro/ → AllegroMarketplaceClient + helpers
    ├── decathlon/ → DecathlonMarketplaceClient + helpers
    └── amazon/ → (future) AmazonMarketplaceClient + helpers
```

**Provider Interface** (only common operations):
- `create_offer()`, `get_offer()`, `update_offer()`, `list_offers()`
- `refresh_token()`, `upload_image()`, `get_categories()`
- `get_marketplace_type()`, `get_capabilities()`

**Marketplace-specific features** (NOT in interface - composition):
- Allegro: `update_offer_status()`, `bulk_edit_offers()`, `get_offer_price()`, `update_offer_price()`, `process_template_sections_for_offer()`, `update_offer_attachments()`
- Decathlon: `get_orders()`, `get_shop_info()`
- Future Amazon: `get_fba_settings()`, `suggest_category_ai()`

---

## Backend Migration - ✅ COMPLETED

### ✅ Provider Infrastructure
```
backend/app/infrastructure/marketplaces/
├── base.py                          # IMarketplaceProvider interface
├── factory.py                       # MarketplaceFactory
├── README.md                        # Architecture documentation
├── allegro/
│   ├── __init__.py                  # Exports all functions
│   ├── client.py                    # AllegroMarketplaceClient
│   ├── api.py                       # API call functions
│   ├── auth.py                      # OAuth Device Code Flow
│   ├── html_sanitizer.py            # Allegro HTML validation rules
│   ├── template_processor.py       # Template processing with AI
│   ├── error_handler.py             # Polish error messages
│   ├── price_operations.py          # Price get/update (Allegro-specific)
│   ├── offer_operations.py          # Status, bulk edits, attachments
│   └── promotion_service.py         # Allegro promotions
└── decathlon/
    ├── client.py                    # DecathlonMarketplaceClient
    ├── api.py                       # Mirakl API client
    └── auth.py                      # API key validation
```

### ✅ Database
- `marketplace_type` added to `accounts` ✅
- `user_allegro_accounts` → `user_marketplace_accounts` ✅
- `modules`: `konta_allegro` → `konta_marketplace` ✅

### ✅ API Endpoints
- `token_utils.py` - Uses `provider.refresh_token()` ✅
- `offers.py` - Uses `provider.list_offers()`, `provider.get_categories()` ✅
- `price_schedules.py` - Uses Allegro-specific methods with capability checks ✅
- `allegro.py` - Uses `infrastructure/marketplaces/allegro/auth` ✅
- `promotions.py` - Uses `infrastructure/marketplaces/allegro/promotion_service` ✅

### ✅ Celery Tasks (30 tasks in tasks.py)
- All `allegro_service` calls replaced with factory pattern ✅
- Error handlers use `infrastructure/marketplaces/allegro/error_handler` ✅
- Template processing uses `provider.process_template_sections_for_offer()` ✅
- Price operations use `provider.get_offer_price()`, `provider.update_offer_price()` ✅

### ✅ Domain Services
- `pdf_generator.py` - Uses factory pattern ✅
- `title_optimizer_service.py` - Uses factory pattern ✅
- `schedule_import.py` - Uses factory pattern ✅
- `promotion_service.py` - Moved to `infrastructure/marketplaces/allegro/` ✅

### ✅ Removed
- `services/allegro.py` (1823 lines) - All logic migrated to infrastructure layer ✅

### Activity Tracking
- Kept Allegro-specific action names for backward compatibility
- Future: Add marketplace-specific action names as needed (e.g., `decathlon_auth_start`)

### Frontend
1. **Types**: Add `marketplace_type` to Account, Offer interfaces
2. **Hooks**: Update to handle marketplace_type
3. **Components**: 
   - `MarketplaceLabel` component (🟠 Allegro, 📦 Amazon, 🟣 eMAG)
   - `FeatureGuard` component (hide features not supported by marketplace)
4. **UI Text**:
   - "Ofertator Allegro" → "Ofertator"
   - "Konta Allegro" → "Konta"
   - Add marketplace badges everywhere
5. **Permissions**: 
   - `MODULES.KONTA_ALLEGRO` → `MODULES.KONTA_MARKETPLACE`

---

## OAuth Flows by Marketplace

**Allegro** (current):
- Device Code Flow
- User authorizes on Allegro website
- Backend polls for token every X seconds
- Returns account name from user info

**Amazon** (future):
- OAuth Redirect Flow
- User redirected to Amazon
- Returns to callback URL with code
- Exchange code for token

**eMAG** (future):
- API Key authentication
- Username + API key stored
- No OAuth flow

---

## Testing Strategy

**Test after EVERY step** (see IMPLEMENTATION_PLAN.md for checkpoints):

1. **Unit tests**: Each provider method
2. **Integration tests**: Full flow (create account → list offers → copy offer)
3. **Regression tests**: All Allegro features still work
4. **Manual tests**: UI + API + Tasks
5. **Staging deploy**: Before each phase merge

---

## Rollback Plan

Each step is reversible:
- **Step 1-5**: Delete new files, no DB changes yet
- **Step 6**: Revert DB migration
- **Step 7+**: Feature flag to use old vs new code
- **Final**: Keep old code until new code proven in production

---

## Critical Files

**Backend**:
- `backend/app/tasks.py` (4,909 lines, 30 tasks) - ⚠️ MOST COMPLEX
- `backend/app/services/allegro.py` (1,823 lines) - ALL Allegro API logic
- `backend/app/api/allegro.py` - OAuth endpoints
- `backend/app/api/offers.py` (1,668 lines) - Offer operations
- `backend/app/middleware/activity_tracker.py` - 126 action types

**Frontend**:
- `frontend/src/pages/OfferEditor.tsx` (1,855 lines)
- `frontend/src/pages/CopyOffers.tsx`
- `frontend/src/pages/Accounts.tsx`
- `frontend/src/hooks/usePermissions.ts` - Module constants

**Database**:
- `backend/app/db/models.py` - Table definitions
- `backend/app/db/crud.py` - CRUD operations

---

## Key Principles

1. **Incremental**: One small step at a time, test, commit
2. **Backward Compatible**: Allegro always works
3. **Isolated Modules**: Marketplaces don't depend on each other
4. **Test First**: Before refactoring, create test to prove it works
5. **Feature Flags**: Can enable/disable new marketplace support

---

## Ready to Start?

See **IMPLEMENTATION_PLAN.md** for step-by-step instructions with testing checkpoints.
