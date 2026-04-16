#!/bin/bash

# Production Deployment Manager for Bot-Sok
# This script provides deployment, rollback, and health check functionality

set -e

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="deployment-backups"
LOG_FILE="deployment.log"
DOMAIN="ofertator.vautomate.pl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}ℹ️  [$timestamp] INFO: $message${NC}" | tee -a $LOG_FILE
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ [$timestamp] SUCCESS: $message${NC}" | tee -a $LOG_FILE
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  [$timestamp] WARNING: $message${NC}" | tee -a $LOG_FILE
            ;;
        "ERROR")
            echo -e "${RED}❌ [$timestamp] ERROR: $message${NC}" | tee -a $LOG_FILE
            ;;
    esac
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        log "WARNING" "Running as root. This is not recommended for production deployments."
    fi
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check if docker and docker-compose are installed
    if ! command -v docker &> /dev/null; then
        log "ERROR" "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        log "ERROR" "Docker Compose is not available"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log "ERROR" ".env file not found. Please create one based on deploy/env.prod.example"
        exit 1
    fi
    
    # Check if docker-compose.prod.yml exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log "ERROR" "$COMPOSE_FILE not found"
        exit 1
    fi
    
    log "SUCCESS" "Prerequisites check passed"
}

# Create backup of current deployment
create_backup() {
    log "INFO" "Creating deployment backup..."
    
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/backup_$backup_timestamp.txt"
    
    mkdir -p $BACKUP_DIR
    
    # Save current container state
    docker compose -f $COMPOSE_FILE ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" > $backup_file
    
    # Save current docker-compose.prod.yml
    cp $COMPOSE_FILE "$BACKUP_DIR/docker-compose.prod.yml_$backup_timestamp"
    
    log "SUCCESS" "Backup created: $backup_file"
    echo $backup_timestamp
}

# SSL certificate management
manage_ssl_certificates() {
    log "INFO" "Managing SSL certificates..."
    
    if [ ! -f "ssl/nginx-selfsigned.crt" ] || [ ! -f "ssl/nginx-selfsigned.key" ]; then
        log "WARNING" "SSL certificates not found. Creating self-signed certificates..."
        mkdir -p ssl
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/nginx-selfsigned.key \
            -out ssl/nginx-selfsigned.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN" \
            2>/dev/null
        
        log "SUCCESS" "Self-signed SSL certificates created"
    else
        log "SUCCESS" "SSL certificates found"
        
        # Check certificate expiration
        local expiry_date=$(openssl x509 -in ssl/nginx-selfsigned.crt -noout -dates | grep notAfter | cut -d= -f2)
        local expiry_epoch=$(date -d "$expiry_date" +%s)
        local current_epoch=$(date +%s)
        local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [ $days_until_expiry -lt 30 ]; then
            log "WARNING" "SSL certificate expires in $days_until_expiry days. Consider renewing soon."
        else
            log "INFO" "SSL certificate valid for $days_until_expiry more days"
        fi
    fi
}

# Health check functions
check_container_health() {
    log "INFO" "Checking container health..."
    
    local unhealthy_containers=()
    
    # Check if all containers are running
    while IFS= read -r line; do
        if [[ $line == *"Exited"* ]] || [[ $line == *"Restarting"* ]]; then
            unhealthy_containers+=("$line")
        fi
    done < <(docker compose -f $COMPOSE_FILE ps --format "table {{.Names}}\t{{.Status}}")
    
    if [ ${#unhealthy_containers[@]} -gt 0 ]; then
        log "ERROR" "Unhealthy containers found:"
        for container in "${unhealthy_containers[@]}"; do
            log "ERROR" "  $container"
        done
        return 1
    fi
    
    log "SUCCESS" "All containers are healthy"
    return 0
}

check_backend_health() {
    log "INFO" "Checking backend health..."
    
    for i in {1..12}; do
        if curl -f http://localhost:8000/docs 2>/dev/null; then
            log "SUCCESS" "Backend is healthy"
            return 0
        elif [ $i -eq 12 ]; then
            log "ERROR" "Backend health check failed after 2 minutes"
            docker compose -f $COMPOSE_FILE logs backend | tail -10
            return 1
        else
            log "INFO" "Backend not ready yet, waiting... ($i/12)"
            sleep 10
        fi
    done
}

check_frontend_health() {
    log "INFO" "Checking frontend health..."
    
    for i in {1..6}; do
        if curl -f https://$DOMAIN/health -k 2>/dev/null; then
            log "SUCCESS" "Frontend is healthy"
            return 0
        elif [ $i -eq 6 ]; then
            log "ERROR" "Frontend health check failed after 1 minute"
            docker compose -f $COMPOSE_FILE logs nginx | tail -10
            return 1
        else
            log "INFO" "Frontend not ready yet, waiting... ($i/6)"
            sleep 10
        fi
    done
}

# Main deployment function
deploy() {
    local docker_hub_username=$1
    
    if [ -z "$docker_hub_username" ]; then
        # Try to get from .env file
        docker_hub_username=$(grep DOCKER_HUB_USERNAME .env | cut -d'=' -f2)
        if [ -z "$docker_hub_username" ]; then
            log "ERROR" "Docker Hub username not provided and not found in .env file"
            exit 1
        fi
    fi
    
    log "INFO" "Starting deployment for Docker Hub user: $docker_hub_username"
    
    # Create backup
    local backup_id=$(create_backup)
    
    # Manage SSL certificates
    manage_ssl_certificates
    
    # Pull latest images
    log "INFO" "Pulling latest images..."
    docker pull $docker_hub_username/bot-sok-backend:latest
    docker pull $docker_hub_username/bot-sok-frontend:latest
    
    # Stop services
    log "INFO" "Stopping services..."
    docker compose -f $COMPOSE_FILE down
    
    # Run migrations
    log "INFO" "Running database migrations..."
    docker compose -f $COMPOSE_FILE run --rm backend alembic upgrade heads
    
    # Create SSL-enabled frontend image
    log "INFO" "Creating SSL-enabled frontend image..."
    docker compose -f $COMPOSE_FILE run -d --name nginx-ssl-temp nginx sleep 3600
    sleep 3
    
    docker exec nginx-ssl-temp mkdir -p /etc/nginx/ssl
    docker cp ssl/nginx-selfsigned.crt nginx-ssl-temp:/etc/nginx/ssl/
    docker cp ssl/nginx-selfsigned.key nginx-ssl-temp:/etc/nginx/ssl/
    
    docker commit nginx-ssl-temp $docker_hub_username/bot-sok-frontend:ssl-enabled
    docker rm -f nginx-ssl-temp
    
    # Update docker-compose to use SSL-enabled image
    sed -i "s|bot-sok-frontend:latest|bot-sok-frontend:ssl-enabled|g" $COMPOSE_FILE
    sed -i "s|bot-sok-frontend:ssl-enabled|bot-sok-frontend:ssl-enabled|g" $COMPOSE_FILE  # In case already updated
    
    # Start services
    log "INFO" "Starting services..."
    docker compose -f $COMPOSE_FILE up -d
    
    # Wait for services to start
    log "INFO" "Waiting for services to start..."
    sleep 30
    
    # Health checks
    if ! check_container_health || ! check_backend_health || ! check_frontend_health; then
        log "ERROR" "Health checks failed. Attempting rollback..."
        rollback $backup_id
        exit 1
    fi
    
    # Clean up
    log "INFO" "Cleaning up unused images..."
    docker image prune -f
    
    log "SUCCESS" "Deployment completed successfully!"
    log "INFO" "Application available at: https://$DOMAIN"
    log "INFO" "Backup ID for rollback: $backup_id"
}

# Rollback function
rollback() {
    local backup_id=$1
    
    if [ -z "$backup_id" ]; then
        # List available backups
        log "INFO" "Available backups:"
        ls -la $BACKUP_DIR/backup_*.txt 2>/dev/null | awk '{print $9}' | sed 's/.*backup_//' | sed 's/.txt//' || log "WARNING" "No backups found"
        read -p "Enter backup ID (YYYYMMDD_HHMMSS): " backup_id
    fi
    
    local backup_file="$BACKUP_DIR/backup_$backup_id.txt"
    local compose_backup="$BACKUP_DIR/docker-compose.prod.yml_$backup_id"
    
    if [ ! -f "$backup_file" ]; then
        log "ERROR" "Backup file not found: $backup_file"
        exit 1
    fi
    
    log "INFO" "Rolling back to backup: $backup_id"
    
    # Stop current services
    docker compose -f $COMPOSE_FILE down
    
    # Restore docker-compose.prod.yml if available
    if [ -f "$compose_backup" ]; then
        cp "$compose_backup" $COMPOSE_FILE
        log "SUCCESS" "Restored docker-compose.prod.yml from backup"
    fi
    
    # Show previous state
    log "INFO" "Previous deployment state:"
    cat $backup_file
    
    # Start services
    log "INFO" "Starting services with previous configuration..."
    docker compose -f $COMPOSE_FILE up -d
    
    # Basic health check
    sleep 15
    if check_container_health; then
        log "SUCCESS" "Rollback completed successfully"
    else
        log "ERROR" "Rollback may have failed. Please check manually."
    fi
}

# Status check function
status() {
    log "INFO" "Current deployment status:"
    
    echo ""
    echo "=== Container Status ==="
    docker compose -f $COMPOSE_FILE ps
    
    echo ""
    echo "=== SSL Certificate Status ==="
    if [ -f "ssl/nginx-selfsigned.crt" ]; then
        openssl x509 -in ssl/nginx-selfsigned.crt -noout -dates -subject
    else
        echo "No SSL certificate found"
    fi
    
    echo ""
    echo "=== Health Check ==="
    check_container_health && echo "✅ Containers: Healthy" || echo "❌ Containers: Issues detected"
    check_backend_health && echo "✅ Backend: Healthy" || echo "❌ Backend: Issues detected"
    check_frontend_health && echo "✅ Frontend: Healthy" || echo "❌ Frontend: Issues detected"
    
    echo ""
    echo "=== Recent Logs ==="
    echo "Backend logs (last 5 lines):"
    docker compose -f $COMPOSE_FILE logs backend | tail -5
    echo ""
    echo "Frontend logs (last 5 lines):"
    docker compose -f $COMPOSE_FILE logs nginx | tail -5
}

# Main script logic
case "${1:-}" in
    "deploy")
        check_permissions
        check_prerequisites
        deploy "${2:-}"
        ;;
    "rollback")
        check_permissions
        check_prerequisites
        rollback "${2:-}"
        ;;
    "status")
        check_prerequisites
        status
        ;;
    "health")
        check_prerequisites
        check_container_health && check_backend_health && check_frontend_health
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|status|health} [options]"
        echo ""
        echo "Commands:"
        echo "  deploy [docker_hub_username]  - Deploy latest version"
        echo "  rollback [backup_id]          - Rollback to previous version"
        echo "  status                        - Show current deployment status"
        echo "  health                        - Run health checks"
        echo ""
        echo "Examples:"
        echo "  $0 deploy igorsokolvsprint"
        echo "  $0 rollback 20250702_143000"
        echo "  $0 status"
        echo "  $0 health"
        exit 1
        ;;
esac 