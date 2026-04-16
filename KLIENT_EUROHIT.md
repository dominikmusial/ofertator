# 🎯 Wersja Kliencka - Eurohit

## Czym jest wersja kliencka?

To wydzielona wersja aplikacji Ofertator stworzona specjalnie dla klienta **Eurohit**, z następującą konfiguracją:

### ✅ Włączone marketplace'y:
- **Decathlon** (Mirakl)
- **Castorama** (Mirakl)
- **Leroy Merlin** (Mirakl)

### ❌ Wyłączone funkcje:
- Allegro marketplace
- Rejestracja nowych użytkowników
- Logowanie przez Google (SSO)
- Konfiguracja AI
- Analityka zespołu
- Panel zużycia AI

---

## 🚀 Jak uruchomić lokalnie?

### 1. Upewnij się, że masz:
- Docker Desktop uruchomiony
- Plik `.env.client` w głównym katalogu

### 2. Uruchom skrypt:
```bash
./run_eurohit_client.sh
```

### 3. Pierwsze uruchomienie - skonfiguruj feature flagi:
```bash
docker-compose -f docker-compose.client.yml -p bot-sok-client exec backend-client python scripts/seed_client_config.py --client-mode
```

**To musisz zrobić tylko raz!** (lub gdy chcesz zresetować konfigurację)

### 4. Otwórz aplikację:
- **Frontend:** http://localhost:5174
- **Backend API:** http://localhost:8001/docs
- **MinIO Console:** http://localhost:9091

### 5. Zaloguj się:
- **Email:** `maciej.niechwiej@eurohit.com.pl`
- **Hasło:** `EurohitVautomate2026!*`

---

## 📦 Dostępne porty:

| Usługa | Port | Opis |
|--------|------|------|
| Frontend | 5174 | Aplikacja webowa |
| Backend | 8001 | API (Swagger: /docs) |
| Postgres | 5433 | Baza danych |
| MinIO | 9091 | Panel zarządzania plikami |
| MinIO API | 9001 | API MinIO |
| Redis | 6380 | Cache & Celery |

---

## 🛠️ Przydatne komendy:

### Zatrzymaj wszystko:
```bash
docker-compose -f docker-compose.client.yml -p bot-sok-client down
```

### Zobacz logi:
```bash
docker-compose -f docker-compose.client.yml -p bot-sok-client logs -f
```

### Zobacz logi tylko backendu:
```bash
docker-compose -f docker-compose.client.yml -p bot-sok-client logs -f backend-client
```

### Restart konkretnego kontenera:
```bash
docker-compose -f docker-compose.client.yml -p bot-sok-client restart backend-client
```

### Wejdź do kontenera backendu (shell):
```bash
docker-compose -f docker-compose.client.yml -p bot-sok-client exec backend-client bash
```

---

## 🔄 Różnice między wersją główną a kliencką:

| Aspekt | Wersja główna | Wersja kliencka (Eurohit) |
|--------|---------------|---------------------------|
| **Marketplace'y** | Allegro | Decathlon, Castorama, Leroy Merlin |
| **Porty frontend** | 5173 | 5174 |
| **Porty backend** | 8000 | 8001 |
| **Port bazy danych** | 5432 | 5433 |
| **Rejestracja** | Włączona | Wyłączona |
| **Google SSO** | Włączony | Wyłączony |
| **AI Config** | Włączona | Wyłączona |
| **Compose file** | `docker-compose.yml` | `docker-compose.client.yml` |

---

## 🚨 Troubleshooting:

### Problem: "service backend-client is not running"
**Rozwiązanie:** Dodaj flagę `-p bot-sok-client` do komendy:
```bash
docker-compose -f docker-compose.client.yml -p bot-sok-client exec backend-client [komenda]
```

### Problem: "Port already in use"
**Rozwiązanie:** Główna wersja aplikacji jest uruchomiona. Zatrzymaj ją:
```bash
docker-compose down
```

### Problem: Widzę Allegro w UI
**Rozwiązanie:** Nie uruchomiłeś seeda. Wykonaj krok 3 z "Jak uruchomić lokalnie?"

### Problem: Nie mogę się zalogować
**Rozwiązanie:** Upewnij się, że:
1. Uruchomiłeś seed (krok 3)
2. Używasz credentials z `.env.client` (domyślnie: `maciej.niechwiej@eurohit.com.pl`)

---

## 🌐 Wersja produkcyjna:

Wersja kliencka jest automatycznie deployowana na:
- **URL:** https://eurohit-ofertator.vautomate.pl
- **Branch:** `feature/mirakl`
- **Deploy:** GitHub Actions (automatyczny przy push do brancha)
