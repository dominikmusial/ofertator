#!/bin/bash
set -e

echo "🚀 Deploying Client-Specific Instance..."
echo ""

# Load environment variables
if [ -f .env.client ]; then
    export $(cat .env.client | grep -v '^#' | xargs)
    echo "✓ Loaded .env.client"
else
    echo "❌ .env.client not found. Please create it from .env.client template"
    exit 1
fi

# Stop existing client containers if running
echo ""
echo "🛑 Stopping existing client containers..."
docker-compose -f docker-compose.client.yml -p bot-sok-client down

# Build and start services
echo ""
echo "🏗️  Building and starting client services..."
docker-compose -f docker-compose.client.yml -p bot-sok-client up -d --build

# Wait for database to be ready
echo ""
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo ""
echo "📊 Running database migrations..."
docker-compose -f docker-compose.client.yml -p bot-sok-client exec -T backend-client alembic upgrade head

echo ""
echo "✅ Client instance started!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:5174"
echo "   Backend:   http://localhost:8001"
echo "   MinIO:     http://localhost:9091 (Console)"
echo ""
echo "🔐 Admin credentials:"
echo "   Email:     ${CLIENT_ADMIN_EMAIL}"
echo "   Password:  ${CLIENT_ADMIN_PASSWORD}"
echo ""
echo "📊 Database:"
echo "   Host:      localhost"
echo "   Port:      5433"
echo "   Database:  allegro_bot_client"
echo ""
echo "💡 First time setup? Run:"
echo "   docker-compose -f docker-compose.client.yml exec backend-client python scripts/seed_client_config.py --client-mode"
echo ""
echo "💡 To view logs: docker-compose -f docker-compose.client.yml -p bot-sok-client logs -f"
echo "💡 To stop: docker-compose -f docker-compose.client.yml -p bot-sok-client down"
