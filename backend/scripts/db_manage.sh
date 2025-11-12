#!/bin/bash

###############################################################################
# Database Management Script for Interior AI
#
# Provides database management commands:
# - migrate: Run database migrations
# - rollback: Rollback last migration
# - reset: Reset database (DANGEROUS)
# - seed: Seed database with initial data
# - console: Open database console
# - vacuum: Optimize database
###############################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"

# Load environment
if [ -f "${PROJECT_DIR}/.env" ]; then
    source "${PROJECT_DIR}/.env"
fi

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

# Run migrations
migrate() {
    log "Running database migrations..."

    docker-compose -f "$COMPOSE_FILE" exec api alembic upgrade head

    if [ $? -eq 0 ]; then
        log "Migrations completed successfully"
    else
        error "Migration failed"
        exit 1
    fi
}

# Rollback migration
rollback() {
    warn "Rolling back last migration..."

    read -p "Are you sure you want to rollback? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "Rollback cancelled"
        exit 0
    fi

    docker-compose -f "$COMPOSE_FILE" exec api alembic downgrade -1

    if [ $? -eq 0 ]; then
        log "Rollback completed successfully"
    else
        error "Rollback failed"
        exit 1
    fi
}

# Reset database
reset() {
    error "WARNING: This will DELETE ALL DATA in the database!"

    read -p "Type 'RESET DATABASE' to confirm: " confirm
    if [ "$confirm" != "RESET DATABASE" ]; then
        log "Reset cancelled"
        exit 0
    fi

    log "Dropping all tables..."

    docker-compose -f "$COMPOSE_FILE" exec api alembic downgrade base

    log "Running migrations..."
    migrate

    log "Database reset completed"
}

# Seed database
seed() {
    log "Seeding database with initial data..."

    docker-compose -f "$COMPOSE_FILE" exec api python -m app.scripts.seed_data

    if [ $? -eq 0 ]; then
        log "Database seeded successfully"
    else
        error "Seeding failed"
        exit 1
    fi
}

# Open database console
console() {
    log "Opening database console..."

    docker-compose -f "$COMPOSE_FILE" exec postgres psql \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-interior_ai}"
}

# Vacuum database
vacuum() {
    log "Optimizing database (VACUUM)..."

    docker-compose -f "$COMPOSE_FILE" exec postgres psql \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-interior_ai}" \
        -c "VACUUM ANALYZE;"

    if [ $? -eq 0 ]; then
        log "Database optimization completed"
    else
        error "Optimization failed"
        exit 1
    fi
}

# Show database status
status() {
    log "Database Status:"
    echo ""

    # Database size
    log "Database Size:"
    docker-compose -f "$COMPOSE_FILE" exec postgres psql \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-interior_ai}" \
        -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB:-interior_ai}'));"

    echo ""

    # Table sizes
    log "Top 5 Largest Tables:"
    docker-compose -f "$COMPOSE_FILE" exec postgres psql \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-interior_ai}" \
        -c "SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 5;"

    echo ""

    # Connection count
    log "Active Connections:"
    docker-compose -f "$COMPOSE_FILE" exec postgres psql \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-interior_ai}" \
        -c "SELECT count(*) FROM pg_stat_activity;"

    echo ""

    # Migration status
    log "Migration Status:"
    docker-compose -f "$COMPOSE_FILE" exec api alembic current
}

# Create new migration
create_migration() {
    local message="${1:-}"

    if [ -z "$message" ]; then
        error "Migration message is required"
        echo "Usage: $0 create-migration 'description of changes'"
        exit 1
    fi

    log "Creating new migration: $message"

    docker-compose -f "$COMPOSE_FILE" exec api alembic revision --autogenerate -m "$message"

    if [ $? -eq 0 ]; then
        log "Migration created successfully"
        log "Don't forget to review and edit the generated migration file!"
    else
        error "Migration creation failed"
        exit 1
    fi
}

# Show usage
usage() {
    cat << EOF
Database Management Script for Interior AI

Usage: $0 <command> [options]

Commands:
    migrate              Run database migrations
    rollback             Rollback last migration
    reset                Reset database (DELETES ALL DATA)
    seed                 Seed database with initial data
    console              Open database console
    vacuum               Optimize database with VACUUM
    status               Show database status
    create-migration     Create new migration (provide message)

Examples:
    $0 migrate
    $0 rollback
    $0 seed
    $0 create-migration "add user preferences table"
    $0 status

EOF
}

# Main
main() {
    local command="${1:-}"

    case "$command" in
        migrate)
            migrate
            ;;
        rollback)
            rollback
            ;;
        reset)
            reset
            ;;
        seed)
            seed
            ;;
        console)
            console
            ;;
        vacuum)
            vacuum
            ;;
        status)
            status
            ;;
        create-migration)
            shift
            create_migration "$@"
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main
main "$@"
