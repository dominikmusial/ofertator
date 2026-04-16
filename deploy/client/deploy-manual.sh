#!/bin/bash

# Manual Deployment Script for Bot-Sok Client (Eurohit)
# Use this script to deploy manually from your local machine
# Alternative to GitHub Actions deployment

set -e

# Configuration - UPDATE THESE VALUES
SERVER_IP="57.128.237.213"
SERVER_USER="ubuntu"
DOCKER_HUB_USERNAME="your_docker_hub_username"  # Update this
DOMAIN="eurohit-ofertator.vautomate.pl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Manual Deployment - Bot-Sok Client${NC}"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.client.prod.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.client.prod.yml not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if Docker Hub username is configured
if [ "$DOCKER_HUB_USERNAME" = "your_docker_hub_username" ]; then
    echo -e "${RED}❌ Error: Please configure DOCKER_HUB_USERNAME in this script${NC}"
    exit 1
fi

# Build images locally
echo -e "${BLUE}🔨 Building Docker images...${NC}"

echo "Building backend..."
docker build -t $DOCKER_HUB_USERNAME/bot-sok-backend-client:latest -f backend/Dockerfile.prod backend/

echo "Building frontend..."
docker build -t $DOCKER_HUB_USERNAME/bot-sok-frontend-client:latest -f frontend/Dockerfile frontend/

echo -e "${GREEN}✅ Images built successfully${NC}"

# Push images to Docker Hub
echo -e "${BLUE}📤 Pushing images to Docker Hub...${NC}"

echo "Logging in to Docker Hub..."
docker login

echo "Pushing backend..."
docker push $DOCKER_HUB_USERNAME/bot-sok-backend-client:latest

echo "Pushing frontend..."
docker push $DOCKER_HUB_USERNAME/bot-sok-frontend-client:latest

echo -e "${GREEN}✅ Images pushed successfully${NC}"

# Copy files to server
echo -e "${BLUE}📁 Copying files to server...${NC}"

ssh $SERVER_USER@$SERVER_IP "mkdir -p /opt/bot-sok-client/deploy/client /opt/bot-sok-client/backend/scripts /opt/bot-sok-client/frontend"

scp docker-compose.client.prod.yml $SERVER_USER@$SERVER_IP:/opt/bot-sok-client/
scp deploy/env.client.prod.example $SERVER_USER@$SERVER_IP:/opt/bot-sok-client/deploy/
scp deploy/client/*.sh $SERVER_USER@$SERVER_IP:/opt/bot-sok-client/deploy/client/
scp frontend/nginx.client.conf $SERVER_USER@$SERVER_IP:/opt/bot-sok-client/frontend/
scp backend/scripts/seed_client_config.py $SERVER_USER@$SERVER_IP:/opt/bot-sok-client/backend/scripts/

echo -e "${GREEN}✅ Files copied successfully${NC}"

# Deploy on server
echo -e "${BLUE}🚀 Deploying on server...${NC}"

ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /opt/bot-sok-client
export DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}

echo "📦 Creating backup..."
docker compose -f docker-compose.client.prod.yml images --format json > deployment_backup.json 2>/dev/null || echo "No previous deployment"

# Check if .env.client.prod exists
if [ ! -f ".env.client.prod" ]; then
    echo "⚠️  .env.client.prod not found. Please create it before deploying!"
    exit 1
fi

# Use production env
rm -f .env
cp .env.client.prod .env

# Make scripts executable
chmod +x deploy/client/*.sh 2>/dev/null || true

echo "📥 Pulling images..."
sudo docker compose -f docker-compose.client.prod.yml pull

echo "⏹️  Stopping services..."
sudo docker compose -f docker-compose.client.prod.yml down

echo "🗄️  Running migrations..."
sudo docker compose -f docker-compose.client.prod.yml up -d db-client redis-client
sleep 10
sudo docker compose -f docker-compose.client.prod.yml run --rm backend-client alembic upgrade head

echo "🚀 Starting all services..."
sudo docker compose -f docker-compose.client.prod.yml up -d

echo "⏳ Waiting for services..."
sleep 30

echo "🌱 Seeding client configuration..."
sudo docker compose -f docker-compose.client.prod.yml exec -T backend-client python scripts/seed_client_config.py --client-mode

echo "🏥 Running health checks..."
for i in {1..12}; do
    if sudo docker compose -f docker-compose.client.prod.yml exec -T backend-client python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
        echo "✅ Backend is healthy"
        break
    else
        echo "⏳ Waiting for backend... ($i/12)"
        sleep 5
    fi
done

echo "🧹 Cleaning up..."
sudo docker image prune -f

echo "📊 Deployment status:"
sudo docker compose -f docker-compose.client.prod.yml ps

echo ""
echo "✅ Deployment completed!"
echo "🌐 Application: https://eurohit-ofertator.vautomate.pl"
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Manual deployment completed successfully!${NC}"
    echo ""
    echo "Your application is now available at:"
    echo -e "${GREEN}https://$DOMAIN${NC}"
    echo ""
    echo "If using self-signed certificates, setup Let's Encrypt:"
    echo "  ssh $SERVER_USER@$SERVER_IP"
    echo "  cd /opt/bot-sok-client"
    echo "  ./deploy/client/setup-letsencrypt.sh"
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo "Check server logs: ssh $SERVER_USER@$SERVER_IP 'cd /opt/bot-sok-client && docker compose -f docker-compose.client.prod.yml logs'"
    exit 1
fi
