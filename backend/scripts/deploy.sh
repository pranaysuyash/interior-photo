#!/bin/bash

###############################################################################
# Production Deployment Script for Interior AI
#
# This script handles the complete deployment process:
# - Environment validation
# - Docker image building
# - Database migrations
# - Service deployment
# - Health checks
# - Rollback on failure
###############################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="${PROJECT_DIR}/logs/deployment.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
        exit 1
    fi
}

# Validate environment file
validate_env() {
    log "Validating environment configuration..."

    if [ ! -f "${PROJECT_DIR}/.env" ]; then
        error ".env file not found"
        exit 1
    fi

    # Check required environment variables
    required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
        "REPLICATE_API_TOKEN"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "S3_BUCKET_NAME"
    )

    source "${PROJECT_DIR}/.env"

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done

    log "Environment validation passed"
}

# Create backup
create_backup() {
    log "Creating database backup..."

    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).sql"

    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U "${POSTGRES_USER:-postgres}" \
        "${POSTGRES_DB:-interior_ai}" > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        log "Backup created: $BACKUP_FILE"
        # Keep only last 7 backups
        ls -t "${BACKUP_DIR}"/backup_*.sql | tail -n +8 | xargs -r rm
    else
        error "Backup failed"
        exit 1
    fi
}

# Build and pull images
build_images() {
    log "Building Docker images..."

    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" build --no-cache

    if [ $? -ne 0 ]; then
        error "Docker build failed"
        exit 1
    fi

    log "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull

    log "Images built successfully"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    docker-compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head

    if [ $? -eq 0 ]; then
        log "Migrations completed successfully"
    else
        error "Migration failed"
        return 1
    fi
}

# Deploy services
deploy_services() {
    log "Deploying services..."

    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" up -d --remove-orphans

    if [ $? -eq 0 ]; then
        log "Services deployed successfully"
    else
        error "Service deployment failed"
        return 1
    fi
}

# Health check
health_check() {
    log "Performing health check..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log "Health check attempt $attempt/$max_attempts"

        # Check API health
        if docker-compose -f "$COMPOSE_FILE" exec -T api curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            log "API health check passed"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 2
    done

    error "Health check failed after $max_attempts attempts"
    return 1
}

# Rollback deployment
rollback() {
    error "Deployment failed. Rolling back..."

    # Stop new containers
    docker-compose -f "$COMPOSE_FILE" down

    # Restore from backup if available
    LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/backup_*.sql 2>/dev/null | head -1)

    if [ -n "$LATEST_BACKUP" ]; then
        warn "Restoring from backup: $LATEST_BACKUP"
        docker-compose -f "$COMPOSE_FILE" up -d postgres
        sleep 5
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql \
            -U "${POSTGRES_USER:-postgres}" \
            -d "${POSTGRES_DB:-interior_ai}" < "$LATEST_BACKUP"
    fi

    error "Rollback completed"
    exit 1
}

# Cleanup old resources
cleanup() {
    log "Cleaning up old resources..."

    # Remove unused Docker images
    docker image prune -af --filter "until=72h"

    # Remove old logs (keep last 30 days)
    find "${PROJECT_DIR}/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true

    log "Cleanup completed"
}

# Main deployment workflow
main() {
    log "=== Starting Interior AI Deployment ==="

    check_root
    validate_env

    # Create backup before deployment
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "postgres"; then
        create_backup
    else
        warn "Database not running, skipping backup"
    fi

    # Build and deploy
    build_images || rollback
    deploy_services || rollback

    # Wait for services to be ready
    sleep 10

    # Run migrations
    run_migrations || rollback

    # Verify deployment
    health_check || rollback

    # Cleanup
    cleanup

    log "=== Deployment completed successfully ==="
    log "Services are now running:"
    docker-compose -f "$COMPOSE_FILE" ps
}

# Run main function
main "$@"
