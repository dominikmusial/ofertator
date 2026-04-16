# Dodawanie Funkcji do Marketplace Mirakl

## 1. Dodaj metodę do MiraklAPIClient

**Plik:** `backend/app/infrastructure/marketplaces/mirakl/api_client.py`

```python
def nowa_metoda(self, param1: str, param2: Optional[int] = None) -> Dict:
    """Dokumentacja endpoint'u"""
    params = {"param1": param1}
    if param2:
        params["param2"] = param2
    
    response = self._request("GET", "/api/endpoint", params=params)
    return response
```

## 2. Zaimplementuj w klientach Mirakl

**Pliki:** 
- `backend/app/infrastructure/marketplaces/decathlon/client.py`
- `backend/app/infrastructure/marketplaces/castorama/client.py`
- `backend/app/infrastructure/marketplaces/leroymerlin/client.py`

```python
def nowa_funkcja(self, param1: str) -> dict:
    """Implementacja dla Mirakl"""
    return self._api_client.nowa_metoda(param1)
```

## 3. Dodaj endpoint API

**Plik:** `backend/app/api/decathlon/products.py` (kopiuj dla castorama/leroymerlin)

```python
@router.get("/nowy-endpoint")
def nowy_endpoint(
    account_id: int,
    param1: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not crud.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    account = crud.get_account(db, account_id=account_id)
    if not account or account.marketplace_type != models.MarketplaceType.decathlon:
        raise HTTPException(status_code=404, detail="Account not found")
    
    try:
        provider = factory.get_provider_for_account(db, account_id)
        return provider.nowa_funkcja(param1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 4. Dodaj hook w frontend (opcjonalnie)

**Plik:** `frontend/src/hooks/useMiraklProducts.ts`

```typescript
export const useNowaFunkcja = (
  marketplace: 'decathlon' | 'castorama' | 'leroymerlin',
  accountId: number | null,
  param1: string
) => {
  return useQuery({
    queryKey: ['mirakl-nova-funkcja', marketplace, accountId, param1],
    queryFn: async () => {
      const response = await api.get(
        `/${marketplace}/products/nowy-endpoint?account_id=${accountId}&param1=${param1}`
      )
      return response.data
    },
    enabled: !!accountId && !!param1,
  })
}
```

## Zasady

✅ **Używaj** `provider.metoda()` - wszystkie Mirakl clients mają te same metody
✅ **Zawsze** dodawaj type hints
✅ **Kopiuj** endpoint dla wszystkich 3 marketplaces (decathlon/castorama/leroymerlin)
✅ **Używaj** `factory.get_provider_for_account(db, account_id)`
✅ **Sprawdzaj** dokumentację API w `openapi3-download.json`

❌ **NIE** łam enkapsulacji (`._api_client`)
❌ **NIE** duplikuj logiki - użyj wspólnego `MiraklAPIClient`
❌ **NIE** implementuj niepotrzebnych metod (np. `refresh_token` - Mirakl używa statycznych kluczy!)

## Architektura Protocol-based

**Nie ma już abstrakcyjnego interfejsu!** Każdy marketplace implementuje tylko to, czego potrzebuje.

- **Allegro**: OAuth → implementuje `TokenRefreshProvider`
- **Mirakl** (Decathlon/Castorama/LeroyMerlin): Statyczne klucze → **NIE** implementuje `TokenRefreshProvider`

Protokoły w `base.py`:
- `MarketplaceIdentity` - wymagane dla wszystkich
- `TokenRefreshProvider` - tylko OAuth marketplaces
- `OffersProvider` - marketplaces z ofertami
- `CategoriesProvider` - marketplaces z kategoriami
- `ImageUploadProvider` - marketplaces z uploadem zdjęć

**Duck typing** - kod działa dopóki klient ma metodę. Bez wymuszania fake implementacji! 🎯

## Operacje Bulk - Użyj Celery Tasks

**Dla operacji na wielu ofertach równocześnie (tłumaczenie, publikacja, walidacja, aktualizacja) - ZAWSZE używaj Celery tasks jak w Allegro!**

**Przykład struktury task:**
```python
# backend/app/infrastructure/marketplaces/mirakl/tasks/offer_tasks.py
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.infrastructure.marketplaces.factory import factory

@celery.task(bind=True, name='mirakl_bulk_publish_offers')
def mirakl_bulk_publish_offers(self, account_id: int, offer_ids: List[str]):
    db = SessionLocal()
    try:
        provider = factory.get_provider_for_account(db, account_id)
        # Operacja bulk
        for offer_id in offer_ids:
            provider.publish_offer(offer_id)
    finally:
        db.close()
```

**Rejestracja:**
1. Dodaj do `celery_worker.py`: `'app.infrastructure.marketplaces.mirakl.tasks'`
2. API endpoint uruchamia task: `task.delay(account_id, offer_ids)`
3. Frontend monitoruje status przez task_id
