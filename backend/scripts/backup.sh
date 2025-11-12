#!/bin/bash

###############################################################################
# Database Backup Script for Interior AI
#
# This script creates automated backups of the PostgreSQL database
# Features:
# - Compressed backups
# - Retention policy (keeps last N backups)
# - S3 upload for off-site storage
# - Email notifications on failure
###############################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/interior_ai_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"
RETENTION_DAYS=30

# Load environment
if [ -f "${PROJECT_DIR}/.env" ]; then
    source "${PROJECT_DIR}/.env"
fi

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Create database backup
create_backup() {
    log "Starting database backup..."

    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-interior_ai}" \
        --verbose \
        --no-owner \
        --no-acl > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        log "Database dump created: $BACKUP_FILE"

        # Compress backup
        gzip "$BACKUP_FILE"
        log "Backup compressed: $COMPRESSED_FILE"

        # Calculate size
        SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
        log "Backup size: $SIZE"

        return 0
    else
        error "Database backup failed"
        return 1
    fi
}

# Upload to S3 (optional)
upload_to_s3() {
    if command -v aws &> /dev/null && [ -n "${S3_BACKUP_BUCKET:-}" ]; then
        log "Uploading backup to S3..."

        aws s3 cp "$COMPRESSED_FILE" \
            "s3://${S3_BACKUP_BUCKET}/backups/$(basename $COMPRESSED_FILE)" \
            --storage-class GLACIER

        if [ $? -eq 0 ]; then
            log "Backup uploaded to S3"
        else
            error "S3 upload failed"
        fi
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."

    find "$BACKUP_DIR" -name "interior_ai_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

    local remaining=$(find "$BACKUP_DIR" -name "interior_ai_backup_*.sql.gz" | wc -l)
    log "Remaining backups: $remaining"
}

# Verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."

    if gunzip -t "$COMPRESSED_FILE" 2>/dev/null; then
        log "Backup integrity verified"
        return 0
    else
        error "Backup integrity check failed"
        return 1
    fi
}

# Main backup workflow
main() {
    log "=== Starting Interior AI Database Backup ==="

    if create_backup && verify_backup; then
        upload_to_s3
        cleanup_old_backups
        log "=== Backup completed successfully ==="
        exit 0
    else
        error "=== Backup failed ==="
        exit 1
    fi
}

# Run main function
main "$@"
