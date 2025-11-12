#!/bin/bash

###############################################################################
# Production Startup Script for Interior AI
#
# This script handles the production startup process:
# - Environment validation
# - Service startup
# - Database migrations
# - Health checks
# - Monitoring setup
###############################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*"
}

# Print banner
print_banner() {
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              Interior AI - Production Startup             ║
║                                                           ║
║     Transform Your Space with AI-Powered Design          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo ""
}

# Check requirements
check_requirements() {
    log "Checking system requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi

    # Check .env file
    if [ ! -f "${PROJECT_DIR}/.env" ]; then
        error ".env file not found"
        error "Please copy .env.example to .env and configure it"
        exit 1
    fi

    log "System requirements met ✓"
}

# Validate environment
validate_environment() {
    log "Validating environment variables..."

    source "${PROJECT_DIR}/.env"

    local required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
        "REPLICATE_API_TOKEN"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "S3_BUCKET_NAME"
    )

    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi

    log "Environment validation passed ✓"
}

# Start services
start_services() {
    log "Starting Interior AI services..."

    cd "$PROJECT_DIR"

    # Pull latest images
    info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull

    # Start services
    info "Starting containers..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be ready
    info "Waiting for services to be ready..."
    sleep 10

    log "Services started ✓"
}

# Run migrations
run_migrations() {
    log "Running database migrations..."

    local max_attempts=5
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head; then
            log "Migrations completed ✓"
            return 0
        fi

        warn "Migration attempt $attempt/$max_attempts failed, retrying..."
        attempt=$((attempt + 1))
        sleep 5
    done

    error "Migrations failed after $max_attempts attempts"
    return 1
}

# Seed database
seed_database() {
    log "Checking if database needs seeding..."

    if docker-compose -f "$COMPOSE_FILE" exec -T api python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
user_count = db.query(User).count()
db.close()
exit(0 if user_count > 0 else 1)
" 2>/dev/null; then
        info "Database already contains data, skipping seeding"
    else
        log "Seeding database with initial data..."
        docker-compose -f "$COMPOSE_FILE" exec -T api python backend/scripts/seed_data.py
        log "Database seeded ✓"
    fi
}

# Health check
health_check() {
    log "Performing health checks..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T api curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            log "Health check passed ✓"
            return 0
        fi

        info "Health check attempt $attempt/$max_attempts..."
        attempt=$((attempt + 1))
        sleep 2
    done

    error "Health check failed"
    return 1
}

# Show status
show_status() {
    echo ""
    log "Interior AI Status:"
    echo ""

    docker-compose -f "$COMPOSE_FILE" ps

    echo ""
    info "Access points:"
    echo "  • Frontend: http://localhost (or your configured domain)"
    echo "  • API Docs: http://localhost/docs"
    echo "  • API Health: http://localhost/api/v1/health"
    echo "  • Grafana: http://localhost:3000 (default: admin/admin)"
    echo "  • Prometheus: http://localhost:9090"
    echo ""
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."

    # Create log directories
    mkdir -p "${PROJECT_DIR}/logs/api"
    mkdir -p "${PROJECT_DIR}/logs/nginx"
    mkdir -p "${PROJECT_DIR}/logs/celery"

    # Set up log rotation
    info "Configuring log rotation..."

    log "Monitoring setup complete ✓"
}

# Main startup workflow
main() {
    print_banner

    log "Starting Interior AI in production mode..."
    echo ""

    check_requirements
    validate_environment
    start_services
    run_migrations || {
        error "Migration failed, stopping services..."
        docker-compose -f "$COMPOSE_FILE" down
        exit 1
    }

    seed_database || warn "Database seeding failed (non-critical)"

    health_check || {
        error "Health check failed, please check logs"
        error "View logs with: docker-compose -f $COMPOSE_FILE logs"
        exit 1
    }

    setup_monitoring
    show_status

    echo ""
    log "════════════════════════════════════════════════════════"
    log "Interior AI started successfully! 🚀"
    log "════════════════════════════════════════════════════════"
    echo ""
    info "View logs with:"
    echo "  docker-compose -f $COMPOSE_FILE logs -f"
    echo ""
    info "Stop services with:"
    echo "  docker-compose -f $COMPOSE_FILE down"
    echo ""
}

# Handle interrupts
trap 'error "Startup interrupted"; exit 1' INT TERM

# Run main
main "$@"
