# 🚀 Ofertator  (Bot-sok)

Zaawansowana aplikacja webowa do zarządzania ofertami na róznych platformach e-commerce.

## 📖 Dokumentacja

**Kompletna dokumentacja projektu znajduje się w pliku:**  
👉 **[DOCUMENTATION.md](./DOCUMENTATION.md)**

## ⚡ Szybki start

### Development
```bash
# Sklonuj repozytorium
git clone https://github.com/sokol-vsprint/Bot-sok.git
cd Bot-sok

# Skonfiguruj środowisko
cp .env.example .env.dev
# Edytuj .env.dev z własnymi wartościami

# Zrób to analogicznie w folderze "frontend"
cd frontend
cp .env.example .env

# WAŻNE: Uruchom SSH tunnel do MinIO przed startowaniem Docker
ssh -N -L 9000:localhost:9000 sokol@34.140.91.224 &

# Uruchom Dockera w tle
docker-compose up -d

# Zastosuj migracje bazy danych
docker-compose exec backend alembic upgrade heads

# Uruchomienie frontendu
cd frontend
npm install
npm run dev
```

### 🧪 Deployment Testing (NEW!)
```bash
# 1. Walidacja przed deployment
./deploy/pre-deploy-check.sh

# 2. Test kompletnego procesu lokalnie
./test-local-deployment.sh

# 3. Deploy do produkcji
git push origin staging
```

### Dostęp do aplikacji
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **MinIO**: Dostęp przez SSH tunnel do produkcyjnego MinIO

### Najnowsze funkcjonalności

#### 🤖 AI Tytułomat (NEW!)
- **Inteligentna optymalizacja tytułów** - AI analizuje i optymalizuje tytuły według zasad Allegro
- **Asynchroniczne przetwarzanie** - Zadania w tle z real-time monitoringiem postępu
- **Progres w czasie rzeczywistym** - Pasek postępu, liczniki sukces/błąd, statusy partii
- **Przetwarzanie masowe** - Do 50 tytułów (20 z parametrami) z automatycznym batchingiem
- **Adaptacyjne retry** - Automatyczne dzielenie na mniejsze partie przy błędach MAX_TOKENS
- **Równoległe pobieranie parametrów** - 10x szybsze (ThreadPoolExecutor, 10 równoczesnych połączeń)
- **Cache parametrów ofert** - 30 min, unika powtórnych wywołań API Allegro
- **Persistencja localStorage** - Wyniki zachowane przy nawigacji/odświeżeniu strony
- **Polski interfejs** - Wszystkie komunikaty i statusy w języku polskim
- **Porównanie przed/po** - Intuicyjny widok z możliwością akceptacji/odrzucenia
- **Walidacja Allegro** - Sprawdzanie długości (max 75 znaków) i zgodności z regulaminem
- **Analiza AI** - Szczegółowe wyjaśnienie wprowadzonych zmian
- **Wizualny selektor ofert** - Przeglądanie i filtrowanie ofert (kategorie dropdown, ceny, zdjęcia)
- **Duplikacja ofert z nowymi tytułami** - Tworzenie kopii ofert na tym samym koncie dla testów A/B
- **Równoległe duplikowanie** - Celery Chord dla szybkiego przetwarzania wielu ofert
- **Wybór statusu** - Możliwość utworzenia ofert jako ACTIVE lub INACTIVE
- **Mapowanie ID** - Modal z mapowaniem starych i nowych ID ofert, opcja podmienienia w edytorze

#### ⚙️ Panel Konfiguracji AI dla Adminów (NEW!)
- **Edycja promptów** - Administratorzy mogą modyfikować prompty dla optymalizacji tytułów (Titles)
- **Parametry API** - Pełna kontrola nad temperature, max_output_tokens, top_p, top_k, stop_sequences
- **Per-provider configuration** - Osobne ustawienia dla Anthropic (Claude) i Google (Gemini)
- **Walidacja w czasie rzeczywistym** - Sprawdzanie limitów specyficznych dla każdego providera (np. temperature 0.0-1.0 dla Anthropic, 0.0-2.0 dla Gemini)
- **Centralne zarządzanie** - Wszystkie zmiany wpływają na moduł Tytuły natychmiast
- **Bezpieczne przechowywanie** - Konfiguracja w tabeli SystemConfig z audytem zmian
- **Domyślne wartości** - Automatyczna migracja obecnych wartości jako domyślne
- **Interfejs po polsku** - Panel administracyjny w pełni spolszczony
- **Sekcja Administracja** - Dedykowana nawigacja dla funkcji administracyjnych

#### 👥 System Zarządzania Użytkownikami
- **Zatwierdzanie kont** - Zewnętrzni użytkownicy wymagają akceptacji admina
- **Powiadomienia email** - Automatyczne notyfikacje o nowych rejestracjach
- **Panel administracyjny** - Zarządzanie użytkownikami z wyszukiwaniem i filtrami
- **Paginacja użytkowników** - 25 użytkowników na stronę
- **Filtrowanie** - Po roli (admin/pracownik/użytkownik) i statusie
- **Wyszukiwanie** - Po nazwie lub adresie email
- **Przepływ zatwierdzania** - Email → Weryfikacja → Oczekiwanie na admina → Aktywacja
- **Auto-zatwierdzanie** - Pracownicy @vsprint.pl pomijają proces zatwierdzania

#### 🤖 Integracja z Asystenciai (NEW!)
- **Płynny transfer kont** - Użytkownicy Asystenciai mogą jednym kliknijęciem przejść do Ofertatora
- **Automatyczne logowanie** - Istniejący użytkownicy są automatycznie logowani
- **Proces rejestracji** - Nowi użytkownicy przechodzą przez formularz setup
- **Domyślny klucz AI** - Automatyczny dostęp do firmowego klucza Gemini bez konfiguracji
- **Konfiguracja AI** - Opcjonalne ustawienie własnego klucza Anthropic/Gemini z przełącznikiem
- **Uprawnienia "Tytuły"** - Automatyczne nadanie dostępu do modułu Tytuły
- **Obsługa błędów** - Pełna obsługa wygasłych tokenów i błędów
- **Bezpieczeństwo** - JWT z shared secret, logowanie wszystkich aktywności

#### 🔑 System Kluczy AI (NEW!)
- **Domyślne klucze dla wszystkich** - Wszyscy użytkownicy zewnętrzni mają dostęp do firmowego klucza Gemini
- **Toggle system** - Przełączanie między własnym a firmowym kluczem bez usuwania konfiguracji
- **Tracking źródła klucza** - Automatyczne śledzenie czy użyto klucza firmowego czy prywatnego
- **Stabilny UI** - Przełącznik pozostaje widoczny, bez problemów z zanikaniem
- **Auto-aktywacja** - Konfiguracja automatycznie aktywowana po zapisaniu

#### 📊 System Analityki i Śledzenia
- **Śledzenie zużycia AI** - Monitoring tokenów i kosztów Claude/Gemini z rozróżnieniem źródła klucza
- **Analityka zespołu** - Aktywność pracowników w czasie rzeczywistym z filtrami
- **Dashboard użytkownika** - Własne statystyki zużycia AI (/usage)
- **Panel managera** - Przegląd aktywności zespołu (/team-analytics)
- **Zaawansowane filtry** - Filtrowanie po roli, źródle rejestracji, źródle klucza API
- **Paginacja** - 10/25/50 użytkowników na stronę
- **Przycisk czyszczenia filtrów** - Szybki reset wszystkich kryteriów
- **Stabilny layout** - Tabela z horizontal scroll bez wpływu na szerokość sidebaru
- **Dynamiczne ceny** - Pobieranie aktualnych kosztów z API Anthropic/Google
- **Lokalizacja PL** - Wszystkie komunikaty w języku polskim

#### 🔄 Import z plików (Excel/CSV)
- **FileImportButton** - Uniwersalny komponent do importu plików
- **useFileImport** - Hook do parsowania Excel/CSV z ID ofert
- **Automatyczna walidacja** - Sprawdzanie poprawności ID ofert
- **Wsparcie formatów** - .xlsx, .csv, .txt

#### 📦 Masowe pobieranie obrazów
- `POST /api/v1/offers/saved-images/{account_id}/bulk-download/{image_type}` - Start masowego pobierania
- `GET /api/v1/offers/saved-images/{account_id}/bulk-download/status/{task_id}` - Status zadania
- `GET /api/v1/offers/saved-images/{account_id}/bulk-download/download/{filename}` - Pobieranie ZIP

### Konfiguracja środowiska
Szczegółowe instrukcje konfiguracji znajdują się w:
- **[ENV_FILES_GUIDE.md](./ENV_FILES_GUIDE.md)** - Konfiguracja zmiennych środowiskowych
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Wdrażanie na produkcję

## 🌐 Produkcja

Aplikacja jest wdrożona pod adresem: **https://ofertator.vautomate.pl**

- **Automatyczne wdrażanie**: GitHub Actions przy push do branch `staging`
- **Logowanie**: Google SSO dla domeny @vsprint.pl
- **Dokumentacja API**: https://ofertator.vautomate.pl/api/docs

### 🔄 Kompatybilność Wdrożenia
✅ **Migracje bazy danych**: Automatyczne (`alembic upgrade heads`)  
✅ **Nowe zależności**: `aiohttp` dodana do `requirements.txt`  
✅ **API endpoints**: `/api/v1/analytics/*` włączone automatycznie  
✅ **Frontend routes**: `/usage` i `/team-analytics` dostępne po wdrożeniu  
✅ **Backwards compatibility**: Wszystkie istniejące funkcje zachowane

## 🏗️ Architektura

- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI + Python + Celery (asynchroniczne zadania)
- **Baza danych**: PostgreSQL
- **Storage**: MinIO (S3-compatible)
- **Deployment**: Docker + GitHub Actions

## 📋 Główne funkcjonalności

✅ **System autoryzacji** (JWT + Google SSO)  
✅ **Zarządzanie kontami Allegro** (re-autoryzacja, tracking tokenów)  
✅ **Masowa edycja ofert** z AI  
✅ **Kopiowanie ofert** między kontami  
✅ **Duplikacja ofert** na tym samym koncie z nowymi tytułami (testy A/B)  
✅ **Zarządzanie obrazami** (upload, przetwarzanie)  
✅ **Zapisane zdjęcia** (masowe pobieranie ZIP)  
✅ **Import z plików** (Excel/CSV z ID ofert)  
✅ **Generowanie PDF** (karty produktowe)  
✅ **Promocje i rabaty**  
✅ **Szablony opisów**  
✅ **Backup i restore** ofert  
✅ **Logowanie operacji** (Google Sheets webhook, konfigurowalny URL przez API)  
🆕 **AI Tytułomat** (optymalizacja tytułów z AI, porównanie i walidacja)  
🆕 **Panel Konfiguracji AI** (admin może edytować prompty i parametry dla Titles)  
🆕 **Zarządzanie użytkownikami** (zatwierdzanie, powiadomienia, panel admina)  
🆕 **System analityki** (śledzenie AI/aktywności użytkowników)  
🆕 **Monitoring tokenów** (koszty Claude/Gemini w czasie rzeczywistym)  
🆕 **Panel managera** (aktywność zespołu vsprint)  
🆕 **Integracja Asystenciai** (płynny transfer kont, automatyczne logowanie)  
🆕 **Re-autoryzacja Allegro** (Device Flow, weryfikacja konta, statusy tokenów)  

## 📞 Wsparcie

- **Zespół**: Pracownicy @vautomate.pl
- **Admin**: pogadajmy@vautomate.pl
- **Dokumentacja**: [DOCUMENTATION.md](./DOCUMENTATION.md)

---

*Wersja: 1.0 | Ostatnia aktualizacja: Styczeń 2026* 