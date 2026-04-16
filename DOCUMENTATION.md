# 📚 Bot-sok - Kompletna Dokumentacja

## 🎯 Przegląd Aplikacji

**Bot-sok** (obecnie **Ofertator Allegro**) to zaawansowana aplikacja webowa do zarządzania ofertami na platformie Allegro. Została zmigrowana z aplikacji desktopowej (tkinter) do nowoczesnej architektury web-based.

### 🏗️ Architektura

- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI + Python
- **Baza danych**: PostgreSQL 
- **Kolejka zadań**: Celery + Redis
- **Storage**: MinIO (S3-compatible)
- **Autoryzacja**: JWT + Google SSO
- **Deployment**: Docker + GitHub Actions

---

## 🔐 System Autoryzacji

### Funkcjonalności
- ✅ **Rejestracja i logowanie** z weryfikacją emailową
- ✅ **Zatwierdzanie przez administratora** - zewnętrzni użytkownicy wymagają akceptacji
- ✅ **Google SSO** (ograniczone do domeny @vsprint.pl)
- ✅ **System ról**: user, vsprint_employee, admin
- ✅ **Reset hasła** przez email
- ✅ **JWT tokens** z automatycznym odświeżaniem
- ✅ **Rate limiting** na endpointach autoryzacji
- ✅ **Powiadomienia email** o nowych rejestracjach dla adminów
- ✅ **Panel zarządzania użytkownikami** z wyszukiwaniem i filtrami
- ✅ **System uprawnień modułowych** - granularna kontrola dostępu do funkcji
- ✅ **Integracja z Asystenciai** - płynny transfer kont między aplikacjami

### 🆕 System Uprawnień Modułowych

**Funkcjonalności:**
- **Granularna kontrola dostępu** - każda funkcja aplikacji może być osobno włączana/wyłączana
- **Moduły podstawowe** (zawsze dostępne): Dashboard, Konta Allegro, Profil
- **Moduły ograniczone**: Edytor Ofert, Kopiowanie Ofert, Promocje, Harmonogram Cen, Tytuły, Miniatury, Podmiana Zdjęć, Wyłączanie Ofert, Zdjęcia na Banerach, Karty Produktowe
- **Moduły zależne**: Dodawanie Grafik, Zapisane Zdjęcia, Zużycie AI (auto-włączane przez inne moduły)
- **Zależności między modułami**: 
  - Edytor Ofert → Dodawanie Grafik + Zapisane Zdjęcia + Zużycie AI
  - Karty Produktowe → Dodawanie Grafik
- **Zarządzanie przez adminów** z interfejsem do masowego przydzielania uprawnień
- **Real-time aktualizacje** - uprawnienia sprawdzane przy każdej nawigacji, odświeżeniu strony i co 2 minuty
- **Zachowanie wstecznej kompatybilności** - wszyscy istniejący użytkownicy mają pełne uprawnienia
- **UI z blokadami** - zablokowane funkcje pokazane z ikoną kłódki i wyjaśnieniem

### 🆕 Zaawansowane Zarządzanie Użytkownikami

**Funkcjonalności dezaktywacji i usuwania:**
- **Dezaktywacja użytkowników** - odwracalna blokada dostępu z powodu
- **Usuwanie użytkowników** - trwałe usunięcie z selektywnym transferem danych
- **Ochrona administratorów** - admini nie mogą być dezaktywowani/usunięci
- **Transfer danych dla pracowników vsprint** - konta Allegro, szablony, obrazy mogą być przeniesione
- **Archiwizacja danych analitycznych** - przeniesienie do tabel archiwum z zachowaniem historii
- **Powiadomienia email** - automatyczne powiadomienia użytkownika i adminów
- **Audit trail** - pełne logowanie operacji zarządzania użytkownikami
- **Wskaźniki wczytywania** - UI z loaderami podczas długich operacji

### Implementacja Techniczna

**Backend (Python/FastAPI):**
- **Tabele bazy danych**: 
  - `modules` - definicje modułów aplikacji
  - `user_module_permissions` - uprawnienia użytkowników do modułów  
  - `module_dependencies` - zależności między modułami
  - `ai_token_usage_archive` - archiwum danych analitycznych AI
  - `ai_usage_daily_stats_archive` - archiwum statystyk dziennych
  - `user_activity_logs_archive` - archiwum logów aktywności
- **CRUD Operations** w `crud.py`: zarządzanie uprawnieniami z logiką zależności
- **Serwisy**:
  - `UserManagementService` - logika dezaktywacji/usuwania użytkowników
  - `AnalyticsArchiveService` - archiwizacja danych usuniętych użytkowników
  - `EmailService` - rozszerzone szablony powiadomień
- **API Endpoints**:
  - `GET /admin/modules` - lista dostępnych modułów
  - `GET/POST /admin/users/{id}/permissions` - zarządzanie uprawnieniami użytkownika
  - `GET /auth/me/permissions` - uprawnienia bieżącego użytkownika
  - `POST /admin/users/{id}/deactivate` - dezaktywacja użytkownika
  - `POST /admin/users/{id}/reactivate` - reaktywacja użytkownika
  - `DELETE /admin/users/{id}/delete` - usunięcie użytkownika
  - `GET /admin/users/{id}/management-info` - info o danych użytkownika
- **Migracje**: addytywne (bezpieczne), zachowują wszystkie istniejące dane, obsługa foreign key constraints

**Frontend (React/TypeScript):**
- **Hooks**: `usePermissions`, `usePermissionGuard` do sprawdzania uprawnień
- **Komponenty**: `PermissionGuard`, `PermissionManager` do kontroli UI
- **Store**: `authStore` rozszerzony o real-time zarządzanie uprawnieniami
- **Routing**: `ProtectedRoute` z parametrem `requireModule`
- **Auto-refresh**: uprawnienia sprawdzane przy nawigacji, refresh, focus (throttling 30s)
- **User Management UI**: 
  - Kompleksowy modal zarządzania użytkownikami z zakładkami (Info/Dezaktywuj/Usuń/Przywróć)
  - Wskaźniki wczytywania podczas operacji
  - Interfejs transferu danych dla pracowników vsprint
  - Kondycjonalne wyświetlanie przycisków (ochrona adminów)

### Role użytkowników

| Rola | Opis | Uprawnienia | Zatwierdzanie |
|------|------|-------------|-------------|
| `user` | Zwykły użytkownik | Dostęp tylko do swoich kont Allegro | Wymaga zatwierdzenia przez admina |
| `vsprint_employee` | Pracownik @vsprint.pl | Współdzielenie kont w zespole | Auto-zatwierdzany |
| `admin` | Administrator | Pełny dostęp + zarządzanie użytkownikami | Auto-zatwierdzany |

### Endpointy API
```
# Autoryzacja
POST /api/v1/auth/register           # Rejestracja
POST /api/v1/auth/login              # Logowanie (sprawdza zatwierdzenie)
POST /api/v1/auth/google-login       # Google SSO
POST /api/v1/auth/verify-email/{token} # Weryfikacja email (powiadomienie adminów)
POST /api/v1/auth/forgot-password    # Reset hasła
POST /api/v1/auth/reset-password     # Nowe hasło
POST /api/v1/auth/refresh-token      # Odświeżenie tokenu (sprawdza zatwierdzenie)
GET  /api/v1/auth/me                 # Info o użytkowniku
GET  /api/v1/auth/me/permissions     # Uprawnienia bieżącego użytkownika
POST /api/v1/auth/change-password    # Zmiana hasła
DELETE /api/v1/auth/delete-account   # Usunięcie konta

# Integracja Asystenciai
GET  /transfer-from-asystenciai      # Transfer użytkownika z Asystenciai (główny endpoint)
GET  /setup-token-data               # Pobieranie danych do formularza setup
POST /complete-setup                 # Finalizacja rejestracji nowego użytkownika
GET  /health                         # Health check integracji

# Zarządzanie uprawnieniami (tylko admin)
GET  /api/v1/admin/modules                      # Lista wszystkich modułów
GET  /api/v1/admin/modules/restricted           # Lista modułów z ograniczeniami
GET  /api/v1/admin/users/{id}/permissions       # Uprawnienia konkretnego użytkownika
POST /api/v1/admin/users/{id}/permissions       # Aktualizacja uprawnień użytkownika
POST /api/v1/admin/users/{id}/permissions/{module}/grant  # Przyznaj uprawnienie
POST /api/v1/admin/users/{id}/permissions/{module}/revoke # Odbierz uprawnienie

# Zarządzanie użytkownikami (Admin)
GET  /api/v1/admin/users/pending          # Użytkownicy oczekujący na zatwierdzenie
GET  /api/v1/admin/users/search           # Wyszukiwanie użytkowników (paginacja, filtry)
POST /api/v1/admin/users/{id}/approve     # Zatwierdzenie użytkownika
POST /api/v1/admin/users/{id}/reject      # Odrzucenie użytkownika
GET  /api/v1/admin/notification-emails    # Lista emaili powiadomień
POST /api/v1/admin/notification-emails    # Aktualizacja emaili powiadomień
GET  /api/v1/admin/dashboard/stats        # Statystyki dashboardu admina

# Zaawansowane zarządzanie użytkownikami (Admin)
GET  /api/v1/admin/users/{id}/management-info  # Informacje o danych użytkownika do zarządzania
POST /api/v1/admin/users/{id}/deactivate       # Dezaktywacja użytkownika (odwracalne)
POST /api/v1/admin/users/{id}/reactivate       # Reaktywacja zdezaktywowanego użytkownika
DELETE /api/v1/admin/users/{id}/delete         # Usunięcie użytkownika (trwałe) z transferem danych

# Konfiguracja AI (Admin)
GET  /api/admin/ai-config                      # Pobierz wszystkie konfiguracje AI (tylko Titles)
PUT  /api/admin/ai-config/titles/{provider}    # Zaktualizuj config dla Titles i providera (anthropic/gemini)

# Analityka z archiwum (Admin)
GET  /api/v1/admin/analytics/archived-users    # Lista usuniętych użytkowników z danymi
GET  /api/v1/admin/analytics/archived-user/{display_name} # Analityka usuniętego użytkownika
GET  /api/v1/admin/analytics/team-with-archived # Analityka zespołu z danymi archiwalnymi
```

---

## 👥 System Zarządzania Użytkownikami

### Przepływ rejestracji zewnętrznych użytkowników

1. **Rejestracja** → Użytkownik wypełnia formularz rejestracji
2. **Weryfikacja email** → Link weryfikacyjny wysłany na email
3. **Kliknięcie linku** → Email zweryfikowany, powiadomienie wysłane do adminów
4. **Oczekiwanie na zatwierdzenie** → Użytkownik nie może się zalogować
5. **Zatwierdzenie przez admina** → Email powiadomienia o akceptacji
6. **Dostęp do aplikacji** → Użytkownik może się logować

### Panel administratora (/admin/users)

#### Zakładka "Oczekujące zatwierdzenia"
- Lista użytkowników wymagających zatwierdzenia
- Możliwość zatwierdzenia lub odrzucenia
- Opcjonalny powód odrzucenia

#### Zakładka "Wszyscy użytkownicy"
- **Wyszukiwarka**: Po nazwie lub adresie email
- **Filtry**:
  - **Rola**: user, admin, vsprint_employee
  - **Status**: aktywny/nieaktywny, zweryfikowany/niezweryfikowany, zatwierdzony/oczekujący
- **Paginacja**: 25 użytkowników na stronę
- **Responsywność**: Tabela na desktop, karty na mobile

#### Zakładka "Ustawienia powiadomień"
- Zarządzanie listą emaili administratorów
- Automatyczne dodawanie/usuwanie emaili
- Powiadomienia o nowych rejestracjach

### Email Templates (w języku polskim)

#### Powiadomienie dla admina o nowej rejestracji
- Informacje o nowym użytkowniku
- Link do panelu zatwierdzania
- Data rejestracji

#### Powiadomienie o zatwierdzeniu konta
- Potwierdzenie akceptacji
- Link do logowania
- Instrukcje pierwszych kroków

#### Powiadomienie o odrzuceniu konta
- Informacja o odrzuceniu
- Opcjonalny powód odrzucenia
- Kontakt do wsparcia

### Bezpieczeństwo

- **Auto-zatwierdzanie**: Pracownicy @vsprint.pl i administratorzy
- **Blokada logowania**: Niezatwierdzeni użytkownicy nie mogą się logować
- **Refresh token**: Sprawdzanie zatwierdzenia przy odświeżaniu tokenu
- **Usuwanie konta**: Odrzucenie usuwa użytkownika i wszystkie powiązane dane

---

## 🏢 Zarządzanie Kontami Allegro

### System współdzielenia kont
- **Właściciel konta**: Może zarządzać, udostępniać i usuwać konto
- **Współdzielenie w zespole**: Pracownicy @vsprint.pl mogą współdzielić konta
- **Automatyczne współdzielenie**: Nowe konta są automatycznie współdzielone w zespole vsprint

### 🆕 System Re-autoryzacji i Trackingu Tokenów

#### Funkcjonalności
- **Automatyczne wykrywanie** wygasłych refresh tokenów (ważność: 3 miesiące)
- **Tracking tokenów**: `refresh_token_expires_at`, `last_token_refresh`, `needs_reauth`
- **Device Flow**: Bezpieczna ponowna autoryzacja bez przekierowań
- **Weryfikacja konta**: Zabezpieczenie przed przypadkową podmianą konta Allegro podczas re-auth
- **Statusy tokenów** w UI: zielony (>14 dni), żółty (7-14 dni), czerwony (wymaga re-auth)
- **Graceful error handling**: Automatyczne ustawianie flagi `needs_reauth` przy `invalid_grant`
- **Centralized token management**: `token_utils.py` z `get_valid_token_with_reauth_handling()`

#### Przepływ re-autoryzacji
1. **Wykrycie wygaśnięcia**: Podczas operacji API token nie może być odświeżony (error 400 `invalid_grant`)
2. **Flaga `needs_reauth`**: System automatycznie ustawia flagę w bazie danych
3. **Powiadomienie UI**: Użytkownik widzi czerwony status "Wymaga ponownej autoryzacji"
4. **Kliknięcie "Ponowna autoryzacja"**: Rozpoczyna Device Flow (nie wymaga przekierowań)
5. **Weryfikacja konta**: System sprawdza czy użytkownik autoryzował właściwe konto Allegro
6. **Aktualizacja tokenów**: Nowe tokeny, reset `needs_reauth`, update `refresh_token_expires_at`

#### Implementacja techniczna
**Backend:**
- `token_utils.py`: Centralizacja logiki odświeżania tokenów z obsługą `needs_reauth`
- `allegro.py`: Endpointy `/re-authenticate/start` i `/re-authenticate/status/{task_id}`
- `tasks.py`: Rozszerzenie `allegro_auth_task` o re-auth z weryfikacją account name
- `crud.py`: `update_account_token()` aktualizuje wszystkie pola trackingu

**Frontend:**
- `ReAuthAccountModal.tsx`: Modal z Device Flow (kod + link + status polling)
- `useReAuthAccount.ts`, `useReAuthStatus.ts`: Hooks do zarządzania re-auth
- `Accounts.tsx`: Status badges (zielony/żółty/czerwony) + przycisk re-auth
- Modal używa React Portal (`createPortal`) dla prawidłowego z-index

### Struktura bazy danych
```sql
-- Główna tabela kont (rozszerzona o tracking tokenów)
accounts (
  id, nazwa_konta, access_token, refresh_token, 
  token_expires_at,                      -- Access token (12h)
  refresh_token_expires_at,              -- Refresh token (3 miesiące) 
  needs_reauth BOOLEAN DEFAULT false,    -- Flaga wymagająca re-auth
  last_token_refresh TIMESTAMP,          -- Ostatnie udane odświeżenie
  created_at, updated_at
)

-- Tabela powiązań użytkownik-konto
user_allegro_accounts (user_id, account_id, is_owner, shared_with_vsprint)
```

### Endpointy API
```
GET  /api/v1/accounts/              # Lista kont użytkownika
POST /api/v1/accounts/share         # Współdzielenie konta
DELETE /api/v1/accounts/{id}        # Usunięcie konta

GET  /api/v1/allegro/shared-accounts # Wszystkie dostępne konta
POST /api/v1/allegro/auth/start     # Rozpocznij autoryzację Allegro
GET  /api/v1/allegro/auth/status/{task_id} # Status autoryzacji

# Re-autoryzacja (NEW!)
POST /api/v1/allegro/accounts/{account_id}/re-authenticate/start          # Rozpocznij Device Flow
GET  /api/v1/allegro/accounts/{account_id}/re-authenticate/status/{task_id} # Poll status
```

---

## 🖼️ Zarządzanie Obrazami

### Funkcjonalności
- ✅ **Upload obrazów** do MinIO
- ✅ **Przetwarzanie obrazów**: usuwanie tła, kadrowanie, rozmycie
- ✅ **Zarządzanie przez konta**: obrazy przypisane do konkretnych kont
- ✅ **Typy obrazów**: logo, fillery (pozycje 1-16), regularne obrazy
- ✅ **Bezpieczny dostęp**: autoryzacja per konto

### Struktura MinIO
```
bucket: account-images
path: {account_name}/{image_type}/{filename}
```

### Endpointy API
```
GET  /api/v1/images/{account_id}    # Lista obrazów konta
POST /api/v1/images/upload          # Upload obrazów
POST /api/v1/images/process         # Przetwarzanie obrazów
DELETE /api/v1/images/{image_id}    # Usunięcie obrazu
POST /api/v1/images/bulk-delete     # Masowe usuwanie
```

---

## 📝 Zarządzanie Ofertami

### Kluczowe funkcjonalności
- ✅ **Masowa edycja opisów** z integracją AI
- ✅ **Backup i restore** ofert
- ✅ **Kopiowanie ofert** między kontami
- ✅ **Duplikacja ofert** z nowymi tytułami na tym samym koncie (testy A/B)
- ✅ **Zarządzanie tytułami**
- ✅ **AI Tytułomat** - optymalizacja tytułów z AI
- ✅ **Zarządzanie miniaturami**
- ✅ **Podmiana zdjęć** (kompozytowe obrazy)
- ✅ **Zarządzanie statusem** (włączanie/wyłączanie)
- ✅ **Zarządzanie banerami** w opisach
- ✅ **Logowanie operacji** do Google Sheets (tylko admin/vsprint_employee)

### System backup
Automatyczne tworzenie kopii zapasowych przed każdą operacją edycji.

### Logowanie operacji (External Logging)
Automatyczne logowanie operacji użytkowników do Google Sheets (tylko dla admin i vsprint_employee):
- **Edycja tytułu** - zapisuje ID oferty i nowy tytuł
- **Edycja opisu** - zapisuje ID oferty  
- **Dodanie rabatów** - zapisuje ID oferty
- **Zmiana miniatury** - zapisuje ID oferty
- **Duplikacja oferty** - zapisuje stare i nowe ID oferty oraz nowy tytuł
- Asynchroniczne wysyłanie batch (nie blokuje operacji)
- Notyfikacja w UI przy błędach logowania
- Format daty/czasu: polski (DD.MM.YYYY, HH:MM w strefie Warsaw)
- **Konfigurowalny webhook URL** - zmiana przez API bez restartu serwera (cache 5 min)
- Automatyczny retry z nowym URL przy błędzie webhooka

### Endpointy API
```
GET  /api/v1/offers/{account_id}           # Lista ofert (z filtrowaniem: kategorie, ceny, offer_ids)
GET  /api/v1/offers/categories/{account_id} # Kategorie Allegro (dropdown, bez wyszukiwania)
POST /api/v1/offers/bulk-edit              # Masowa edycja (+ logging)
POST /api/v1/offers/bulk-edit-titles       # Edycja tytułów (+ logging)
POST /api/v1/offers/pull-titles            # Pobieranie tytułów z Allegro
POST /api/v1/offers/optimize-titles-ai     # Optymalizacja tytułów z AI
POST /api/v1/offers/duplicate-offers-with-titles # Duplikacja ofert z nowymi tytułami (+ logging)
POST /api/v1/offers/bulk-change-status     # Zmiana statusu
POST /api/v1/offers/bulk-update-thumbnails # Aktualizacja miniatur (+ logging)
POST /api/v1/offers/bulk-replace-images    # Podmiana zdjęć
POST /api/v1/offers/bulk-manage-banners    # Zarządzanie banerami
POST /api/v1/offers/copy                   # Kopiowanie ofert
POST /api/v1/offers/{offer_id}/restore-backup # Przywracanie z backup
GET  /api/v1/offers/saved-images/{account_id} # Zapisane obrazy
GET  /api/v1/offers/task-status/{task_id} # Status asynchronicznego zadania
```

### AI Tytułomat

**Funkcjonalności:**
- ✅ **Asynchroniczne przetwarzanie** - Celery task z real-time progress tracking (polling co 3s)
- ✅ **Monitoring postępu** - Pasek postępu, liczniki (sukces/błąd), statusy partii w języku polskim
- ✅ **Optymalizacja z AI** - Masowe przetwarzanie (max 50 tytułów, 20 z parametrami) przez Claude/Gemini
- ✅ **Automatyczny batching** - Batch size: 12 bez parametrów, 7 z parametrami
- ✅ **Adaptacyjne retry** - Automatyczne dzielenie na mniejsze partie (min 2) przy błędach MAX_TOKENS
- ✅ **Równoległe pobieranie parametrów** - ThreadPoolExecutor (max 10 workers), 10x szybsze (~300ms vs 3s)
- ✅ **Cache parametrów** - 30 min, unika powtórnych wywołań API Allegro
- ✅ **Konfiguracja admin** - Respektowanie max_output_tokens z SystemConfig (bez hardcoded overrides)
- ✅ **Persistencja localStorage** - Wyniki i zaakceptowane ID zachowane przy nawigacji/odświeżeniu
- ✅ **Walidacja Allegro** - Sprawdzanie długości (max 75 znaków) i zgodności z regulaminem
- ✅ **Polski interfejs** - Wszystkie komunikaty statusów i błędów w języku polskim
- ✅ **Szczegółowe błędy** - Indywidualne komunikaty dla każdej oferty
- ✅ **Porównanie tytułów** - Widok przed/po z możliwością akceptacji/odrzucenia
- ✅ **Wizualny selektor ofert** - Przeglądanie ofert z filtrowaniem (kategorie dropdown, ceny, zdjęcia)

### Duplikacja Ofert z Nowymi Tytułami

**Funkcjonalności:**
- ✅ **Duplikacja na tym samym koncie** - Tworzenie kopii ofert z nowymi tytułami dla testów A/B (podobnie jak Allegro)
- ✅ **Pełne kopiowanie danych** - Wszystkie parametry, opis, zdjęcia, cena, dostawa, zwroty, gwarancja
- ✅ **Równoległe przetwarzanie** - Celery Chord dla szybkiego duplikowania wielu ofert jednocześnie
- ✅ **Real-time progress** - Monitoring postępu z paskiem i licznikami sukces/błąd
- ✅ **Wybór statusu publikacji** - Modal z wyborem ACTIVE lub INACTIVE przed duplikacją
- ✅ **Mapowanie ID** - Wyświetlanie mapowania starych i nowych ID ofert po zakończeniu
- ✅ **Podmiana ID w edytorze** - Opcja automatycznej podmiany starych ID na nowe w textarea
- ✅ **Format wejściowy** - `ID_oferty | Nowy_tytuł` (separatory: `,`, `;`, `|`, tab)
- ✅ **Walidacja** - Sprawdzanie formatu ID, długości tytułu (max 75 znaków), wykrywanie duplikatów
- ✅ **Zachowanie języka** - Wykorzystanie `Accept-Language` header dla poprawnego języka ofert
- ✅ **Logging operacji** - Automatyczne logowanie do zewnętrznego systemu (tylko admin/vsprint_employee)

**Implementacja techniczna (AI Tytułomat):**
- **Backend**: 
  - `optimize_titles_ai_task` (Celery) - asynchroniczne zadanie z `self.update_state()` dla progress tracking
  - `TitleOptimizerService._fetch_offer_parameters()` - równoległe pobieranie z ThreadPoolExecutor
  - `TitleOptimizerService._optimize_single_batch()` - statyczna metoda do przetwarzania partii
  - Cache parametrów ofert (30 min) z automatycznym kluczem user_id + offer_id
  - Adaptacyjne retry: batch_size // 2, minimum 2 tytuły
- **Frontend**: 
  - `useAIOptimizationTaskStatus()` - polling task status co 3s z automatycznym stop
  - `AIOptimizationPanel` - UI z paskiem postępu i licznikami w czasie rzeczywistym
  - `localStorage` - automatyczny zapis wyników i zaakceptowanych ID przy zmianie
  - Odczyt z localStorage przy mount komponentu
- **Hooks**: `useOptimizeTitlesAI`, `useAIOptimizationTaskStatus`, `useOfferSelector`
- **API Endpoints**:
  - `POST /api/v1/offers/optimize-titles-ai` → zwraca `{task_id}`
  - `GET /api/v1/offers/task-status/{task_id}` → zwraca status i progress metadata
- **Progress metadata**: `{status, progress, processed, total, successful, failed}`
- **Walidacja**: Max 50 tytułów bez parametrów, max 20 z parametrami (error 400 przy przekroczeniu)

**Implementacja techniczna (Duplikacja Ofert):**
- **Backend**:
  - `duplicate_offer_with_title_task` (Celery) - zadanie duplikujące pojedynczą ofertę z nowym tytułem
  - `batch_duplicate_offers_callback` (Celery) - callback agregujący wyniki z wielu duplikacji
  - Celery Chord - równoległe wykonywanie duplikacji z finalnym callback
  - `_prepare_catalog_offer_payload` - specjalna logika dla ofert katalogowych (same_account_duplicate=True)
  - Zachowanie wszystkich danych: afterSalesServices, delivery, shippingRates, returnPolicy, warranty, impliedWarranty
  - Usuwanie problematycznych pól: publication, isAiCoCreated, images i language z product (zapobiega konfliktom z katalogiem)
  - `Accept-Language` header - przekazywanie języka oferty źródłowej do API Allegro
- **Frontend**:
  - `useDuplicateOffers()` - hook do wysyłania żądania duplikacji
  - `useTaskStatus()` - polling statusu zadania Celery Chord
  - Modal z wyborem statusu (ACTIVE/INACTIVE) przed duplikacją
  - Modal z mapowaniem ID (stare → nowe) po zakończeniu
  - Opcja podmiany ID w textarea (separator: przecinek)
- **Schemas**: `DuplicateOfferItem`, `DuplicateOffersRequest` w `backend/app/db/schemas.py`
- **API Endpoints**:
  - `POST /api/v1/offers/duplicate-offers-with-titles` → zwraca `{task_id}`
  - `GET /api/v1/offers/task-status/{task_id}` → zwraca status chord i mapowanie ID
- **Response**: `{status, total_offers, success_count, failure_count, duplicated_offers: [{old_id, new_id, title}], failed_offers: [{offer_id, title, error}]}`

---

## 📄 Generowanie PDF (Karty Produktowe)

### Funkcjonalności
- ✅ **Automatyczne generowanie** kart produktowych
- ✅ **Integracja z ofertami** Allegro
- ✅ **Zarządzanie załącznikami**
- ✅ **Upload własnych plików** PDF
- ✅ **WeasyPrint** do generowania PDF

### Endpointy API
```
POST /api/v1/offers/generate-pdf           # Generowanie PDF
POST /api/v1/offers/bulk-delete-attachments # Usuwanie załączników
POST /api/v1/offers/bulk-restore-attachments # Przywracanie załączników
POST /api/v1/offers/upload-custom-attachment # Upload własnego PDF
```

---

## 🎯 Promocje i Rabaty

### Funkcjonalności
- ✅ **Tworzenie promocji** typu bundle
- ✅ **Zarządzanie rabatami** ilościowymi
- ✅ **Usuwanie promocji**

### Endpointy API
```
GET  /api/v1/promotions/               # Lista promocji
POST /api/v1/promotions/create         # Tworzenie promocji (+ logging)
DELETE /api/v1/promotions/{id}         # Usuwanie promocji
DELETE /api/v1/promotions/delete-all/{account_id} # Usuwanie wszystkich
```

---

## 💰 Harmonogram Cen (Price Scheduler)

### Funkcjonalności
- ✅ **Automatyczne zarządzanie cenami** - zmiana cen ofert według harmonogramu
- ✅ **Harmonogram tygodniowy** - możliwość ustawienia różnych cen dla każdego dnia tygodnia i godziny
- ✅ **Backup cen** - automatyczne zapisywanie oryginalnych cen przed zmianą
- ✅ **Historia zmian** - pełny log wszystkich zmian cen z timestampem
- ✅ **Celery Beat** - automatyczne wykonywanie zmian cen w tle
- ✅ **Przywracanie cen** - możliwość przywrócenia oryginalnej ceny przy usuwaniu harmonogramu
- ✅ **Token refresh** - automatyczne odświeżanie wygasłych tokenów Allegro API

### Architektura

**Komponenty:**
- **Frontend**: React component z tygodniowym kalendarzemdo konfiguracji harmonogramu
- **Backend API**: FastAPI endpoints w `/api/v1/price-schedules/`
- **Celery Tasks**: Zadanie `process_price_schedules` wykonywane co godzinę przez Celery Beat
- **Database**: Tabele `price_schedules`, `price_snapshots`, `price_change_logs`

**Przepływ działania:**
1. Użytkownik tworzy harmonogram dla oferty z ceną promocyjną i konfiguracją tygodniową
2. System zapisuje aktualną cenę jako backup (`price_snapshots`)
3. Celery Beat co godzinę sprawdza aktywne harmonogramy
4. Dla każdego harmonogramu sprawdza czy aktualny dzień/godzina wymaga zmiany ceny
5. Jeśli tak, zmienia cenę oferty przez Allegro API i loguje operację
6. Token Allegro jest automatycznie odświeżany jeśli wygasł

### Struktura bazy danych

**price_schedules** - główna tabela harmonogramów
```python
id: int (PK)
account_id: int (FK -> accounts)
offer_id: str  # ID oferty Allegro
offer_name: str  # Nazwa oferty dla UI
original_price: str  # Oryginalna cena (backup)
scheduled_price: str  # Cena promocyjna
schedule_config: JSON  # Konfiguracja tygodniowa
current_price_state: str  # 'original' lub 'scheduled'
is_active: bool  # Czy harmonogram jest aktywny
created_at: datetime
updated_at: datetime
```

**price_snapshots** - backupy cen przed zmianą
```python
id: int (PK)
account_id: int (FK -> accounts)
offer_id: str
price: str
snapshot_reason: str  # np. 'schedule_created'
created_at: datetime
```

**price_change_logs** - historia wszystkich zmian
```python
id: int (PK)
schedule_id: int (FK -> price_schedules)
account_id: int (FK -> accounts)
offer_id: str
price_before: str
price_after: str
change_reason: str  # np. 'scheduled_change', 'schedule_deleted_restore'
success: bool
error_message: str (nullable)
changed_at: datetime
```

**system_config** - konfiguracja systemowa
```python
id: int (PK)
config_key: str (unique, indexed)  # np. 'external_logging_webhook_url', 'ai.titles.anthropic.prompt'
config_value: text                 # Wartość (może być JSON)
description: str (nullable)
updated_at: datetime
updated_by_user_id: int (FK -> users.id, nullable)

# Konwencja dla AI: ai.{module}.{provider}.{parameter}
```

### Endpointy API
```
GET  /api/v1/offers/active/{account_id}          # Lista aktywnych ofert z Allegro
POST /api/v1/price-schedules/                     # Tworzenie harmonogramu
GET  /api/v1/price-schedules/{account_id}        # Lista harmonogramów dla konta
PUT  /api/v1/price-schedules/{schedule_id}       # Aktualizacja harmonogramu
DELETE /api/v1/price-schedules/{schedule_id}     # Usunięcie (z opcją przywrócenia ceny)
GET  /api/v1/price-schedules/{schedule_id}/logs  # Historia zmian cen
```

### Token Refresh Pattern

**Problem:** Tokeny Allegro API wygasają po czasie, co powodowało błędy 401 Unauthorized.

**Rozwiązanie:** Funkcja `get_valid_token()` w `price_schedules.py`:
```python
def get_valid_token(db: Session, current_user: User, account_id: int) -> str:
    # Sprawdź czy token wygasa w ciągu 5 minut
    if account.token_expires_at <= datetime.utcnow() + timedelta(minutes=5):
        # Odśwież token używając refresh_token
        new_token_data = allegro_service.refresh_allegro_token(account.refresh_token)
        # Zaktualizuj dane w bazie
        account.access_token = new_token_data['access_token']
        account.refresh_token = new_token_data['refresh_token']
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=new_token_data['expires_in'])
        db.commit()
    return account.access_token
```

Ten sam pattern jest używany w:
- `promotions.py` - wszystkie endpointy
- `tasks.py` - wszystkie zadania Celery
- `price_schedules.py` - wszystkie endpointy (po poprawce)

### Celery Task Configuration
```python
# Harmonogram wykonywania (co godzinę)
@celery.beat_schedule
'process-price-schedules': {
    'task': 'app.tasks.process_price_schedules',
    'schedule': crontab(minute=0)  # Co godzinę o pełnej godzinie
}
```

### System Uprawnień
- Wymaga modułu `price_scheduler` w uprawnieniach użytkownika
- Użytkownik musi mieć dostęp do konta Allegro
- Dependency: `require_price_scheduler = require_module_permission("price_scheduler")`

---

## 🎨 Szablony Opisów

### Funkcjonalności
- ✅ **CRUD operations** na szablonach z kontrolą uprawnień
- ✅ **JSON structure** dla sekcji
- ✅ **Przypisanie do kont** Allegro (wymagane)
- ✅ **Integracja z AI** do generowania treści
- ✅ **System uprawnień** oparty na właścicielu
- ✅ **Współdzielenie** między pracownikami vSprint
- ✅ **Unikalne nazwy** per konto Allegro
- ✅ **Kopiowanie** z obsługą konfliktów nazw

### System uprawnień
- **Właściciel szablonu**: Może edytować i usuwać swoje szablony
- **Pozostali użytkownicy**: Mogą tylko przeglądać i kopiować szablony
- **Pracownicy vSprint**: Widzą wszystkie szablony dla kont do których mają dostęp
- **Użytkownicy regulari**: Widzą szablony tylko dla kont współdzielonych z vSprint

### Struktura szablonu
```json
{
  "prompt": "Instrukcje dla AI...",
  "sections": [
    {
      "type": "IMG,TXT",
      "values": {
        "image": "Aukcja:1",
        "text": "Opis produktu..."
      }
    }
  ]
}
```

### Funkcje w Edytorze Ofert
- **Wczytywanie**: Wszystkie dostępne szablony dla wybranego konta
- **Zapisywanie**: Tworzenie nowych szablonów
- **Aktualizacja**: Tylko właściciel może aktualizować szablon
- **Usuwanie**: Tylko właściciel może usunąć szablon
- **Kopiowanie**: Z automatycznym rozwiązywaniem konfliktów nazw
- **Filtrowanie**: Pracownicy vSprint mogą filtrować swoje szablony

### Endpointy API
```
GET  /api/v1/templates/?account_id={id}        # Lista szablonów dla konta
POST /api/v1/templates/?account_id={id}        # Tworzenie szablonu
PUT  /api/v1/templates/{id}                    # Edycja szablonu (tylko właściciel)
DELETE /api/v1/templates/{id}                  # Usunięcie szablonu (tylko właściciel)
POST /api/v1/templates/copy                    # Kopiowanie szablonu
POST /api/v1/templates/copy-with-name          # Kopiowanie z nową nazwą
```

### Ograniczenia
- Nazwy szablonów muszą być unikalne w ramach konta Allegro
- Każdy szablon musi być przypisany do konkretnego konta
- Maksymalnie 16 sekcji w szablonie

---

## 🤖 Konfiguracja AI

### Obsługiwane providery
- ✅ **Anthropic Claude** (wszystkie modele)
- ✅ **Google Gemini** (wszystkie modele)
- ✅ **Szyfrowanie kluczy** API
- ✅ **Testowanie połączenia**
- ✅ **Automatyczny fallback** - użytkownicy bez własnego klucza korzystają z domyślnego providera

### Panel administratora (NEW!)
Administratorzy mogą zarządzać promptami i parametrami AI dla modułu **Tytuły** przez `/admin/ai-prompts`:
- **Edycja promptów** dla Title Optimizer (osobno dla Anthropic i Gemini)
- **Parametry API**: temperature, max_output_tokens, top_p, top_k, stop_sequences
- **Walidacja zakresów** per-provider (np. temperature 0.0-1.0 dla Anthropic, 0.0-2.0 dla Gemini)
- **Przechowywanie w SystemConfig** z konwencją `ai.{module}.{provider}.{parameter}`
- **Audit trail** - logowanie zmian przez `updated_by_user_id`

**Uwaga:** Moduł OfferEditor używa hardcoded promptów i nie jest konfigurowalny przez panel admina.

### Domyślny AI Provider
System automatycznie określa providera dla użytkowników bez własnej konfiguracji:
- **Asystenciai** (`registration_source=asystenciai`) → Gemini
- **Administratorzy i vSprint** → Anthropic (Claude)
- **Pozostali** → muszą skonfigurować własny klucz

### Endpointy API
```
# Konfiguracja użytkownika
GET  /api/v1/ai-config/config          # Pobierz konfigurację użytkownika
POST /api/v1/ai-config/config          # Utwórz konfigurację
PUT  /api/v1/ai-config/config          # Zaktualizuj konfigurację
DELETE /api/v1/ai-config/config        # Usuń konfigurację
POST /api/v1/ai-config/test-key        # Testuj klucz API
GET  /api/v1/ai-config/status          # Status (z default provider/model)
```

---

## 🤖 Integracja z Asystenciai

### Funkcjonalności
- ✅ **Płynny transfer kont** - użytkownicy Asystenciai mogą jednym kliknijęciem przejść do Ofertatora
- ✅ **Automatyczne logowanie** - istniejący użytkownicy są automatycznie logowani
- ✅ **Proces rejestracji** - nowi użytkownicy przechodzą przez formularz setup
- ✅ **Domyślny klucz AI** - automatyczny dostęp do firmowego klucza Gemini bez dodatkowej konfiguracji
- ✅ **Konfiguracja AI** - opcjonalne dodanie własnego klucza z możliwością przełączania
- ✅ **Toggle system** - przełączanie między własnym a firmowym kluczem bez usuwania konfiguracji
- ✅ **Uprawnienia "Tytuły"** - automatyczne nadanie dostępu do modułu Tytuły
- ✅ **Obsługa błędów** - pełna obsługa wygasłych tokenów i błędów
- ✅ **Bezpieczeństwo** - JWT z shared secret, logowanie wszystkich aktywności

### Architektura integracji

#### Przepływ dla istniejącego użytkownika:
1. **Asystenciai** generuje JWT token z danymi użytkownika
2. **Przekierowanie** do `/transfer-from-asystenciai?token={jwt}`
3. **Ofertator** sprawdza czy użytkownik istnieje (po `external_user_id` lub `email`)
4. **Auto-login** - tworzy access/refresh tokeny
5. **Przekierowanie** do `/auth/success` z tokenami
6. **Frontend** zapisuje tokeny i przekierowuje do `/titles`

#### Przepływ dla nowego użytkownika:
1. **Asystenciai** generuje JWT token z danymi użytkownika
2. **Przekierowanie** do `/transfer-from-asystenciai?token={jwt}`
3. **Ofertator** stwierdza że użytkownik nie istnieje
4. **Setup token** - tworzy token setup (ważny 30 min)
5. **Przekierowanie** do `/setup-account?token={setup_token}`
6. **Frontend** wyświetla formularz rejestracji (hasło)
7. **Submit** - `POST /complete-setup` z hasłem
8. **Ofertator** tworzy konto, nadaje uprawnienia, loguje użytkownika
9. **Użytkownik automatycznie ma dostęp do firmowego klucza Gemini** (bez konfiguracji)
10. **Przekierowanie** do `/titles`

### Struktura bazy danych
```sql
-- Rozszerzenie tabeli users o pola integracji
users (
  ...,
  registration_source ENUM('web', 'asystenciai') DEFAULT 'web',
  external_user_id VARCHAR(255) NULL,  -- ID użytkownika w Asystenciai
  INDEX idx_external_user_id (external_user_id)
)
```

### Endpointy API
```
# Integracja Asystenciai (bez prefiksu /api/v1 dla czystych URL)
GET  /transfer-from-asystenciai      # Główny endpoint transferu
GET  /setup-token-data               # Pobieranie danych do formularza setup  
POST /complete-setup                 # Finalizacja rejestracji nowego użytkownika
GET  /health                         # Health check integracji
```

### Konfiguracja
```bash
# Zmienne środowiskowe dla integracji
ASYSTENCIAI_SHARED_SECRET=change-me-in-production
ASYSTENCIAI_SETUP_TOKEN_EXPIRE_MINUTES=30
```

### Frontend
- **Strona setup**: `/setup-account` - formularz rejestracji dla nowych użytkowników
- **Strona sukcesu**: `/auth/success` - obsługa automatycznego logowania
- **Strona błędów**: `/auth/error` - obsługa błędów integracji

## 🔑 System Kluczy API (Default AI Keys)

### Przegląd
Wszyscy użytkownicy mają automatyczny dostęp do firmowych kluczy AI bez konieczności konfiguracji. Mogą dodać własny klucz i przełączać się między firmowym a własnym w czasie rzeczywistym.

### Mechanizm Fallback
- **Użytkownicy zewnętrzni** (role: `user`) → Gemini API (`GEMINI_API_KEY`)
- **Użytkownicy Asystenci AI** → Gemini API (`GEMINI_API_KEY`)
- **Pracownicy vSprint** (role: `vsprint_employee`) → Anthropic API (`ANTHROPIC_API_KEY`)
- **Administratorzy** (role: `admin`) → Anthropic API (`ANTHROPIC_API_KEY`)

### Toggle System (Przełączanie Kluczy)
Użytkownicy z własną konfiguracją mogą przełączać się między:
- **Własny klucz** (`is_active = True`) - używany ich klucz API
- **Klucz firmowy** (`is_active = False`) - używany klucz vAutomate (fallback)

**UI w `/profile/ai-config`:**
- Przełącznik pozostaje widoczny i nie znika po zmianie
- Wyraźne oznaczenie aktywnej konfiguracji z zielonym tłem
- Zapisana konfiguracja wyświetlana w osobnej karcie
- Formularz automatycznie aktywuje konfigurację po zapisaniu
- Optymalizacja React Query - brak nadmiarowych refetch operacji

### Tracking Użycia
Pole `key_source` w tabeli `ai_token_usage` przechowuje informację czy użyto klucza użytkownika ('user_custom') czy firmowego ('company_default').

**Implementacja:**
- `KeySource` enum w modelu `AITokenUsage`
- Automatyczne logowanie źródła przy każdym zapytaniu AI
- Indeks na kolumnie dla szybkich zapytań analitycznych

### Team Analytics dla Adminów
Panel `/team-analytics` pozwala adminom filtrować użytkowników według:
- **Filtry**: Rola, źródło rejestracji, źródło klucza API, wyszukiwanie po nazwie/email
- **Przycisk "Wyczyść filtry"** - szybkie resetowanie wszystkich filtrów
- **Paginacja**: 10/25/50 użytkowników na stronę
- **Stabilny layout**: Tabela z poziomym scrollem bez wpływu na szerokość sidebaru
- **Opcja pokazywania użytkowników bez użycia AI**

### Migracja
Skrypt `backend/migrate_asystenciai_configs.py` obsługuje migrację istniejących konfiguracji.

### Struktura Bazy Danych
```sql
-- UserAIConfig
user_ai_configs (
  ...,
  is_active BOOLEAN DEFAULT TRUE,  -- Czy aktywna konfiguracja
  ...
)

-- AITokenUsage
ai_token_usage (
  ...,
  key_source ENUM('user_custom', 'company_default') NULL,  -- Źródło klucza
  INDEX idx_key_source (key_source)
)
```

### Bezpieczeństwo
- **JWT tokens** z shared secret (HS256)
- **Walidacja danych** - sprawdzanie wszystkich wymaganych pól
- **Expiry tokens** - krótki czas życia tokenów (5-30 min)
- **Logowanie aktywności** - pełny audit trail
- **Rate limiting** - ochrona przed nadmiernym użyciem (opcjonalne)

### Dokumentacja dla developerów
Pełna dokumentacja integracji dla zespołu Asystenciai znajduje się w:
📄 **[ASYSTENCIAI_INTEGRATION_GUIDE.md](./ASYSTENCIAI_INTEGRATION_GUIDE.md)**

---

## 🚀 Deployment i Infrastruktura

### Środowiska

#### Development
```bash
# Uruchomienie lokalnie
docker-compose up -d
```

#### Production
```bash
# Automatyczne wdrażanie przez GitHub Actions przy push do 'staging'
# Lub ręcznie:
docker-compose -f docker-compose.prod.yml up -d
```

### Komponenty infrastruktury

| Komponent | Port | Opis |
|-----------|------|------|
| Nginx (Frontend) | 80, 443 | Serwowanie React app + reverse proxy |
| Backend API | 8000 | FastAPI application |
| PostgreSQL | 5432 | Baza danych |
| Redis | 6379 | Kolejka zadań Celery |
| MinIO | 9000, 9001 | Object storage |
| Celery Worker | - | Przetwarzanie zadań w tle |

### Health Checks
- **Frontend**: `https://ofertator.vautomate.pl/health`
- **Backend**: `https://ofertator.vautomate.pl/api/docs`
- **Database**: Automatyczne sprawdzanie połączenia
- **Redis**: `redis-cli ping`
- **MinIO**: Health endpoint

### Automatyczne wdrażanie
GitHub Actions automatycznie:
1. **Buduje** obrazy Docker
2. **Wdraża** na serwer produkcyjny
3. **Uruchamia** testy zdrowia
4. **Wykonuje rollback** w przypadku błędów

---

## 🎮 Frontend - Interfejs Użytkownika

### Struktura stron

| Strona | Ścieżka | Status | Opis |
|--------|---------|--------|------|
| **Home** | `/` | ✅ | Dashboard z przeglądem funkcji |
| **Logowanie** | `/auth/login` | ✅ | Logowanie + Google SSO |
| **Rejestracja** | `/auth/register` | ✅ | Rejestracja nowych użytkowników |
| **Profil** | `/profile` | ✅ | Zarządzanie kontem i konfiguracją AI |
| **Konta** | `/accounts` | ✅ | Zarządzanie kontami Allegro |
| **Edytor Ofert** | `/offer-editor` | ✅ | Masowa edycja opisów |
| **Kopiowanie** | `/copy-offers` | ✅ | Kopiowanie ofert między kontami |
| **Promocje** | `/promotions` | ✅ | Zarządzanie promocjami |
| **Tytuły** | `/titles` | ✅ | Pobieranie i edycja tytułów |
| **Miniatury** | `/thumbnails` | ✅ | Zarządzanie miniaturkami |
| **Podmiana Zdjęć** | `/replace-images` | ✅ | Kompozytowe obrazy |
| **Wyłączanie** | `/disable-offers` | ✅ | Zmiana statusu ofert |
| **Bannery** | `/banner-images` | ✅ | Zarządzanie banerami |
| **Karty PDF** | `/product-cards` | ✅ | Generowanie PDF |
| **Obrazy** | `/images` | ✅ | Upload i zarządzanie obrazami |
| **Zapisane Zdjęcia** | `/saved-images` | ✅ | Przeglądanie zapisanych zdjęć |
| **Szablony** | `/templates` | ✅ | Zarządzanie szablonami |
| **Zarządzanie Użytkownikami** | `/admin/users` | ✅ | Panel administratora - zatwierdzanie użytkowników |
| **Konfiguracja AI** | `/admin/ai-prompts` | ✅ | Panel administracyjny - edycja promptów i parametrów AI dla Titles |
| **Setup Asystenciai** | `/setup-account` | ✅ | Formularz rejestracji dla użytkowników Asystenciai |
| **Auth Success** | `/auth/success` | ✅ | Obsługa automatycznego logowania |
| **Auth Error** | `/auth/error` | ✅ | Obsługa błędów integracji |

### Komponenty UI
- ✅ **shadcn/ui** - gotowe komponenty
- ✅ **TailwindCSS** - styling
- ✅ **React Query** - zarządzanie stanem serwera
- ✅ **Zustand** - globalny stan aplikacji
- ✅ **React Router** - routing
- ✅ **Chronione trasy** - ProtectedRoute

---

## 🗄️ Baza Danych

### Główne tabele

```sql
-- Użytkownicy (rozszerzeni o zarządzanie)
users (id, email, password_hash, first_name, last_name, is_active, is_verified, 
       admin_approved, role, google_id, company_domain, created_at, updated_at,
       deactivated_at, deactivated_by_admin_id, deactivation_reason)

-- Emaile powiadomień administratorów (z nullable created_by_admin_id)
admin_notification_emails (id, email, is_active, created_at, created_by_admin_id)

-- System uprawnień modułowych
modules (id, name, route, display_name, description, is_core, category, created_at)
user_module_permissions (id, user_id, module_id, granted_at, granted_by_admin_id)
module_dependencies (parent_module_id, dependent_module_id)

-- Konta Allegro (rozszerzone o tracking tokenów)
accounts (id, nazwa_konta, access_token, refresh_token, token_expires_at, 
          refresh_token_expires_at, needs_reauth, last_token_refresh, ...)

-- Powiązania użytkownik-konto
user_allegro_accounts (user_id, account_id, is_owner, shared_with_vsprint, ...)

-- Szablony
templates (id, name, content, owner_id, account_id, prompt, ...)

-- Obrazy kont
account_images (id, account_id, filename, original_filename, url, ...)

-- Kopie zapasowe ofert
offer_backups (id, offer_id, backup_data, account_id, ...)

-- Weryfikacja email
email_verifications (id, user_id, token, expires_at, is_used, ...)

-- Reset hasła
password_resets (id, user_id, token, expires_at, is_used, ...)

-- Konfiguracja AI
user_ai_configs (id, user_id, ai_provider, model_name, encrypted_api_key, ...)

-- Integracja Asystenciai (rozszerzenie tabeli users)
users (..., registration_source, external_user_id, ...)

-- Statystyki AI (dla analityki)
ai_usage_daily_stats (id, user_id, date, total_requests, total_input_tokens, 
                      total_output_tokens, total_cost_usd, operations_breakdown)
ai_token_usage (id, user_id, account_id, operation_type, ai_provider, model_name,
                input_tokens, output_tokens, total_tokens, input_cost_usd, 
                output_cost_usd, total_cost_usd, request_timestamp, ...)

-- Archiwum danych usuniętych użytkowników
ai_token_usage_archive (id, original_id, user_id, account_id, ..., 
                        deleted_user_display_name, deleted_at, deleted_by_admin_id)
ai_usage_daily_stats_archive (id, original_id, user_id, date, ...,
                               deleted_user_display_name, deleted_at, deleted_by_admin_id)
user_activity_logs_archive (id, original_id, user_id, action_type, ...,
                             deleted_user_display_name, deleted_at, deleted_by_admin_id)

-- Logi aktywności użytkowników
user_activity_logs (id, user_id, action_type, resource_type, resource_id,
                    details, ip_address, user_agent, created_at)

-- Sesje użytkowników
user_sessions (id, user_id, session_id, session_start, session_end,
               ip_address, user_agent, login_method, activity_count)

-- Harmonogram Cen (Price Scheduler)
price_schedules (id, account_id, offer_id, offer_name, original_price,
                 scheduled_price, schedule_config, current_price_state,
                 is_active, created_at, updated_at)

price_snapshots (id, account_id, offer_id, price, snapshot_reason, created_at)

price_change_logs (id, schedule_id, account_id, offer_id, price_before,
                   price_after, change_reason, success, error_message, changed_at)
```

### Migracje
Zarządzane przez **Alembic**:

```bash
# Zastosuj migracje
alembic upgrade heads

# Utwórz nową migrację
alembic revision --autogenerate -m "opis_zmiany"

# Sprawdź aktualny stan migracji
alembic current

# Zobacz historię migracji
alembic history --verbose
```

### ⚠️ Najnowsze Migracje (Październik 2025)

**Sekwencja migracji dla modułowych uprawnień, zarządzania użytkownikami, integracji Asystenciai i konfiguracji AI:**

1. `1cf67a6ef659` - **Module Permissions System** - Podstawowy system uprawnień modułowych
2. `bd78175794a7` - **User Management Fields** - Pola dezaktywacji w tabeli users
3. `e8b329d4a71c` - **Analytics Archive Tables** - Tabele archiwum dla danych usuniętych użytkowników
4. `7d538c3e5cf0` - **Archive FK Constraints Fix** - Naprawa foreign key w tabelach archiwum
5. `341d3fcd2fd4` - **Admin Emails FK Fix** - Naprawa FK w admin_notification_emails
6. `f5a2f36fde70` - **Self-Referencing FK Fix** - Naprawa samo-referencyjnych FK w users
7. `2f984f8ae3ae` - **Asystenciai Integration** - Pola integracji z Asystenciai (registration_source, external_user_id)
8. `4b5c6d7e8f9a` - **AI Config Defaults** - Domyślne wartości AI w SystemConfig (prompty i parametry dla Titles)
9. `add_token_reauth_tracking` - **Token Re-auth Tracking** - Kolumny trackingu tokenów w accounts (refresh_token_expires_at, needs_reauth, last_token_refresh)

**Bezpieczeństwo migracji:**
- ✅ **Addytywne** - żadne dane nie są usuwane
- ✅ **Wsteczna kompatybilność** - istniejący kod nadal działa
- ✅ **Seed data** - automatyczne nadanie uprawnień istniejącym użytkownikom
- ✅ **Foreign key safety** - `SET NULL` zamiast `CASCADE` dla bezpieczeństwa
- ✅ **Nullable fields** - nowe pola mogą być puste w starych rekordach

---

## 🔧 Konfiguracja

### Zmienne środowiskowe

#### Wymagane dla produkcji
```bash
# Baza danych
DATABASE_URL=postgresql://user:pass@host:port/db
POSTGRES_DB=allegro_bot_prod
POSTGRES_USER=allegro_bot_user
POSTGRES_PASSWORD=secure_password

# JWT & Security
SECRET_KEY=very-long-secure-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=app-password
MAIL_FROM=noreply@vsprint.pl

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/google/callback

# Allegro API
ALLEGRO_CLIENT_ID=your-allegro-client-id
ALLEGRO_CLIENT_SECRET=your-allegro-client-secret

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=secure-minio-password
MINIO_PUBLIC_URL=https://your-domain.com:9000
MINIO_INTERNAL_URL=http://minio:9000

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Admin konto
DEFAULT_ADMIN_EMAIL=admin@vsprint.pl
DEFAULT_ADMIN_PASSWORD=ChangeThisPassword123!
```

---

## 🔄 Migracja z Starej Aplikacji

### Status migracji
- ✅ **Kompletna migracja** z aplikacji tkinter
- ✅ **Wszystkie funkcjonalności** przeniesione
- ✅ **Nowa architektura** z systemem użytkowników
- ✅ **Współdzielenie kont** w zespole vsprint

### Główne zmiany
1. **Desktop → Web**: Z tkinter na React + FastAPI
2. **SFTP → MinIO**: Z serwera SSH na object storage
3. **Globalne konta → Per-user**: System autoryzacji użytkowników
4. **Synchroniczne → Asynchroniczne**: Zadania w tle z Celery

---

## 🛠️ Rozwijanie i Maintenance

### Uruchamianie lokalnie
```bash
# 1. Sklonuj repozytorium
git clone https://github.com/your-org/Bot-sok.git
cd Bot-sok

# 2. Skonfiguruj środowisko
cp .env.example .env.dev
# Edytuj .env.dev

# 3. Uruchom z Docker
docker-compose up -d

# 4. Zastosuj migracje
docker-compose exec backend alembic upgrade heads

# 5. Otwórz w przeglądarce
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

### Dodawanie nowych funkcji
1. **Backend**: Dodaj endpoint w `/backend/app/api/`
2. **Frontend**: Dodaj hook w `/frontend/src/hooks/`
3. **UI**: Dodaj komponent/stronę w `/frontend/src/`
4. **Testy**: Przetestuj ręcznie kluczowe przepływy

### Monitoring
- **Logi aplikacji**: `docker-compose logs backend`
- **Logi zadań**: `docker-compose logs worker`  
- **Logi web**: `docker-compose logs nginx`
- **Stan kontenerów**: `docker-compose ps`

---

## 📊 Status Projektu (Grudzień 2024)

### ✅ UKOŃCZONE (100%)
- **System autoryzacji** - pełna funkcjonalność
- **Zarządzanie kontami** - współdzielenie w zespole
- **Wszystkie operacje na ofertach** - edycja, kopiowanie, backup
- **Zarządzanie obrazami** - upload, przetwarzanie, MinIO
- **Generowanie PDF** - karty produktowe
- **Promocje i rabaty** - pełna funkcjonalność  
- **Szablony opisów** - CRUD + integracja AI
- **Frontend** - wszystkie strony i komponenty
- **Infrastruktura** - deployment, monitoring, backup

### 🎯 PRODUKCJA
Aplikacja jest **w pełni wdrożona** i gotowa do użycia produkcyjnego:
- **URL**: https://ofertator.vautomate.pl
- **Automatyczne wdrażanie** przez GitHub Actions
- **Monitoring** i health checks
- **Backup** i procedury rollback

---

## 📞 Wsparcie

### Kontakt
- **Zespół**: Pracownicy @vsprint.pl
- **Login**: Przez Google SSO z domeną @vsprint.pl
- **Admin**: admin@vsprint.pl

### Rozwiązywanie problemów
1. **Sprawdź logi**: `docker-compose logs [service]`
2. **Restart serwisów**: `docker-compose restart [service]`
3. **Health check**: `./deploy/deploy-production.sh health`
4. **Rollback**: W przypadku problemów automatyczny rollback w CI/CD

---

## 📋 Podsumowanie Zmian (Październik 2025)

### 🆕 Główne Nowe Funkcjonalności

#### 1. **System Uprawnień Modułowych**
- **25 modułów** z granularną kontrolą dostępu
- **Automatyczne zależności** między modułami
- **Real-time aktualizacje** uprawnień (nawigacja, refresh, co 2 min)
- **UI z blokadami** - ikony kłódki dla zablokowanych funkcji
- **Zarządzanie przez adminów** z masowym przydzielaniem
- **Wsteczna kompatybilność** - wszyscy istniejący użytkownicy mają pełne uprawnienia

#### 2. **Zaawansowane Zarządzanie Użytkownikami**
- **Dezaktywacja użytkowników** (odwracalna) z opcjonalnym powodem
- **Usuwanie użytkowników** (trwałe) z selektywnym transferem danych
- **Ochrona administratorów** - nie mogą być dezaktywowani/usunięci
- **Transfer danych** dla pracowników vsprint (konta, szablony, obrazy)
- **Archiwizacja danych analitycznych** z zachowaniem historii
- **Powiadomienia email** automatyczne dla wszystkich operacji
- **Wskaźniki wczytywania** w UI podczas długich operacji

### 🔧 Zmiany Techniczne

#### Backend (FastAPI/Python)
- **6 nowych tabel**: modules, user_module_permissions, module_dependencies + 3 archive tables
- **3 nowe serwisy**: UserManagementService, AnalyticsArchiveService, EmailService (rozszerzony)
- **15 nowych endpointów API** dla zarządzania uprawnieniami i użytkownikami
- **Migracje bezpieczne** - addytywne, z seed data, bez utraty danych
- **Foreign key fixes** - `SET NULL` zamiast CASCADE dla bezpieczeństwa

#### Frontend (React/TypeScript)
- **4 nowe hooki**: usePermissions, usePermissionGuard + rozszerzenia istniejących
- **3 nowe komponenty**: PermissionGuard, PermissionManager + rozszerzenia AdminUsers
- **Real-time permission refresh** - sprawdzanie przy nawigacji i focus
- **Conditional rendering** - dynamiczne ukrywanie elementów UI
- **Loading indicators** - UX podczas długich operacji

### 📊 Statystyki Implementacji

| Kategoria | Dodane | Zmodyfikowane | Usunięte |
|-----------|--------|---------------|----------|
| **Backend Files** | 3 | 8 | 0 |
| **Frontend Files** | 4 | 6 | 0 |
| **Database Tables** | 6 | 2 | 0 |
| **API Endpoints** | 15 | 0 | 0 |
| **Migracje** | 6 | 0 | 0 |
| **UI Components** | 3 | 4 | 0 |

### 🚀 Deployment & Compatibility

#### ✅ **Migration Safety**
- **Wszystkie migracje** są bezpieczne i addytywne
- **Seed data** automatycznie nadaje uprawnienia istniejącym użytkownikom
- **Foreign key constraints** naprawione z `SET NULL` dla bezpieczeństwa
- **Backward compatibility** - stary kod nadal działa
- **Current migration head**: `f5a2f36fde70`

#### ✅ **Production Ready**
- **GitHub Actions pipeline** przetestowany z nowymi migracjami
- **Health checks** zweryfikowane dla wszystkich serwisów
- **Database backup procedures** działają poprawnie
- **Rollback procedures** dostępne w `deploy/emergency-rollback.sh`

### 🔄 **Migration Sequence (w kolejności)**
1. `1cf67a6ef659` - Module Permissions System
2. `bd78175794a7` - User Management Fields  
3. `e8b329d4a71c` - Analytics Archive Tables
4. `7d538c3e5cf0` - Archive FK Constraints Fix
5. `341d3fcd2fd4` - Admin Emails FK Fix
6. `f5a2f36fde70` - Self-Referencing FK Fix
7. `2f984f8ae3ae` - Asystenciai Integration
8. `4b5c6d7e8f9a` - AI Config Defaults
9. `add_token_reauth_tracking` - Token Re-auth Tracking

### 🎯 **Benefits Delivered**
- **Granular access control** - każda funkcja może być osobno kontrolowana
- **Enhanced admin capabilities** - pełne zarządzanie użytkownikami + konfiguracja AI
- **Data preservation** - archiwizacja zamiast utraty danych
- **Better UX** - loading indicators, conditional UI, real-time updates
- **Production stability** - wszystkie migracje bezpieczne i przetestowane
- **AI customization** - administratorzy mogą dostosować prompty i parametry AI
- **Flexible architecture** - łatwe dodawanie nowych AI providerów (np. OpenAI)

---

### 🆕 AI Tytułomat (Październik 2025)

**Nowe komponenty:**
- `title_optimizer_service.py` - serwis optymalizacji z AI, cache parametrów ofert
- `AIOptimizationPanel.tsx`, `TitleComparisonView.tsx`, `OfferFilterPanel.tsx` - UI components
- `useOptimizeTitlesAI.ts`, `useOfferCategories.ts` - hooks

**Kluczowe feature'y:**
- Masowa optymalizacja (do 100 tytułów, 20 z parametrami) przez Claude/Gemini
- Parametry produktów z API Allegro opcjonalnie dołączane do prompta
- Wymuszenie limitu 75 znaków w systemowym prompcie AI
- Walidacja Allegro (długość, wielkie litery, emotikony)
- Szczegółowe błędy dla każdej oferty zamiast całkowitego failure
- Porównanie przed/po z akceptacją/odrzuceniem
- Persistencja localStorage dla pól tekstowych
- Uproszczony dropdown kategorii (bez wyszukiwania)

---

## 📋 Najnowsze Zmiany (Listopad 2025)

### 🚀 AI Tytułomat - Przeprojektowanie na Async

**Problem:** Synchroniczne przetwarzanie blokowało UI, brak feedbacku dla użytkownika, wolne pobieranie parametrów.

**Rozwiązanie:**
1. **Asynchroniczne zadania** - Celery task z `optimize_titles_ai_task` zamiast synchronicznego wywołania
2. **Real-time progress** - `self.update_state()` aktualizuje: status, progress %, processed/total, successful/failed
3. **Polling frontend** - `useAIOptimizationTaskStatus` odpytuje `/task-status/{task_id}` co 3s
4. **Równoległe API calls** - ThreadPoolExecutor (10 workers) dla parametrów: 3s → 0.3s (10x szybciej)
5. **Persistencja UI** - localStorage zachowuje wyniki przy nawigacji/refresh
6. **Polski interfejs** - "Przetwarzanie partii X/Y...", "Ponowna próba...", etc.
7. **Respektowanie konfiguracji** - Usunięto hardcoded override dla max_output_tokens
8. **Walidacja limitów** - Max 50/20 tytułów, error 400 przy przekroczeniu

**Pliki zmienione:**
- `backend/app/tasks.py` - nowy task `optimize_titles_ai_task` (220+ linii)
- `backend/app/services/title_optimizer_service.py` - równoległe pobieranie parametrów
- `backend/app/api/offers.py` - endpoint zwraca task_id zamiast rezultatów
- `frontend/src/hooks/useOptimizeTitlesAI.ts` - nowy hook `useAIOptimizationTaskStatus`
- `frontend/src/pages/Titles.tsx` - UI z paskiem postępu i licznikami, localStorage

**Performance:**
- Parametry: 3000ms → 300ms (10x szybciej)
- UI: non-blocking, responsywny podczas przetwarzania
- UX: użytkownik widzi co się dzieje w czasie rzeczywistym

### 🔄 Duplikacja Ofert z Nowymi Tytułami

**Problem:** Użytkownicy potrzebują możliwości testowania A/B różnych tytułów dla tych samych ofert (jak ma Allegro).

**Rozwiązanie:**
1. **Pełna duplikacja na tym samym koncie** - kopiowanie wszystkich danych (parametry, opis, zdjęcia, dostawa, zwroty, gwarancja)
2. **Równoległe przetwarzanie** - Celery Chord dla szybkiego duplikowania wielu ofert jednocześnie
3. **Real-time progress** - monitoring postępu z licznikami sukces/błąd
4. **Modal z wyborem statusu** - użytkownik decyduje czy oferty mają być ACTIVE czy INACTIVE
5. **Mapowanie ID** - wyświetlanie mapowania starych i nowych ID z opcją podmiany w textarea
6. **Zachowanie języka** - wykorzystanie `Accept-Language` header dla poprawnego języka ofert
7. **External logging** - automatyczne logowanie do Google Sheets (tylko admin/vsprint_employee)

**Pliki zmienione:**
- `backend/app/tasks.py` - nowe taski `duplicate_offer_with_title_task`, `batch_duplicate_offers_callback`
- `backend/app/api/offers.py` - nowy endpoint `/duplicate-offers-with-titles`
- `backend/app/db/schemas.py` - nowe schematy `DuplicateOfferItem`, `DuplicateOffersRequest`
- `backend/app/services/allegro.py` - rozszerzenie `create_product_offer()` o parametr `language`
- `backend/app/middleware/activity_tracker.py` - rejestracja nowego endpointu
- `frontend/src/hooks/useDuplicateOffers.ts` - nowy hook do duplikacji
- `frontend/src/pages/Titles.tsx` - UI z przyciskiem, modalami i progress trackerem

**Kluczowe funkcje:**
- Format wejściowy: `ID_oferty | Nowy_tytuł` (separatory: `,`, `;`, `|`, tab)
- Walidacja: format ID, długość tytułu (max 75 znaków), wykrywanie duplikatów
- Specjalna logika dla ofert katalogowych: `same_account_duplicate=True`
- Zachowanie wszystkich krytycznych pól: afterSalesServices, delivery, shippingRates
- Usuwanie pól powodujących konflikty: publication, isAiCoCreated, images/language z product

---

*Dokumentacja zaktualizowana: Listopad 2025*
*Wersja aplikacji: 1.0*
*Migration Head: add_token_reauth_tracking* 