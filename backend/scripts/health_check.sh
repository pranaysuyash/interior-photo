#!/bin/bash

###############################################################################
# Health Check Script for Interior AI
#
# Monitors the health of all services:
# - API endpoints
# - Database connectivity
# - Redis connectivity
# - Celery workers
# - Disk space
# - Memory usage
###############################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
API_URL="${API_URL:-http://localhost:8000}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Status tracking
OVERALL_STATUS=0

print_status() {
    local status=$1
    local message=$2

    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
        OVERALL_STATUS=1
    fi
}

# Check API health endpoint
check_api() {
    echo "Checking API health..."

    if curl -sf "${API_URL}/api/v1/health" > /dev/null 2>&1; then
        print_status 0 "API is healthy"
    else
        print_status 1 "API is not responding"
    fi
}

# Check database connectivity
check_database() {
    echo "Checking database connectivity..."

    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; then
        print_status 0 "Database is healthy"

        # Check database size
        local db_size=$(docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-interior_ai}" -t -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB:-interior_ai}'));" 2>/dev/null | xargs)
        echo "  Database size: $db_size"

        # Check active connections
        local connections=$(docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-interior_ai}" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | xargs)
        echo "  Active connections: $connections"
    else
        print_status 1 "Database is not responding"
    fi
}

# Check Redis connectivity
check_redis() {
    echo "Checking Redis connectivity..."

    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_status 0 "Redis is healthy"

        # Check memory usage
        local mem_usage=$(docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        echo "  Memory usage: $mem_usage"

        # Check connected clients
        local clients=$(docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli client list | wc -l)
        echo "  Connected clients: $clients"
    else
        print_status 1 "Redis is not responding"
    fi
}

# Check Celery workers
check_celery() {
    echo "Checking Celery workers..."

    local worker_status=$(docker-compose -f "$COMPOSE_FILE" exec -T celery_worker celery -A app.tasks.celery_app inspect active 2>/dev/null)

    if [ -n "$worker_status" ]; then
        print_status 0 "Celery workers are running"

        # Check active tasks
        local active_tasks=$(docker-compose -f "$COMPOSE_FILE" exec -T celery_worker celery -A app.tasks.celery_app inspect active 2>/dev/null | grep -c "id" || echo "0")
        echo "  Active tasks: $active_tasks"
    else
        print_status 1 "Celery workers are not responding"
    fi
}

# Check disk space
check_disk_space() {
    echo "Checking disk space..."

    local disk_usage=$(df -h "${PROJECT_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ "$disk_usage" -lt 80 ]; then
        print_status 0 "Disk space is adequate (${disk_usage}% used)"
    elif [ "$disk_usage" -lt 90 ]; then
        print_status 0 "Disk space is getting low (${disk_usage}% used)"
        echo -e "${YELLOW}  WARNING: Consider cleaning up or expanding storage${NC}"
    else
        print_status 1 "Disk space is critically low (${disk_usage}% used)"
    fi
}

# Check memory usage
check_memory() {
    echo "Checking memory usage..."

    local mem_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')

    if [ "$mem_usage" -lt 80 ]; then
        print_status 0 "Memory usage is normal (${mem_usage}% used)"
    elif [ "$mem_usage" -lt 90 ]; then
        print_status 0 "Memory usage is elevated (${mem_usage}% used)"
        echo -e "${YELLOW}  WARNING: Monitor for memory leaks${NC}"
    else
        print_status 1 "Memory usage is critical (${mem_usage}% used)"
    fi
}

# Check container status
check_containers() {
    echo "Checking container status..."

    local expected_containers=("postgres" "redis" "api" "celery_worker" "nginx")
    local all_running=true

    for container in "${expected_containers[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "$container.*Up"; then
            echo -e "  ${GREEN}✓${NC} $container is running"
        else
            echo -e "  ${RED}✗${NC} $container is not running"
            all_running=false
        fi
    done

    if [ "$all_running" = true ]; then
        print_status 0 "All containers are running"
    else
        print_status 1 "Some containers are not running"
    fi
}

# Check response times
check_response_time() {
    echo "Checking API response time..."

    local start_time=$(date +%s%N)
    curl -sf "${API_URL}/api/v1/health" > /dev/null 2>&1
    local end_time=$(date +%s%N)

    local response_time=$(( (end_time - start_time) / 1000000 ))

    if [ "$response_time" -lt 1000 ]; then
        print_status 0 "API response time is good (${response_time}ms)"
    elif [ "$response_time" -lt 3000 ]; then
        print_status 0 "API response time is acceptable (${response_time}ms)"
    else
        print_status 1 "API response time is slow (${response_time}ms)"
    fi
}

# Main health check
main() {
    echo "================================"
    echo "Interior AI Health Check"
    echo "$(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================"
    echo ""

    check_containers
    echo ""

    check_api
    echo ""

    check_response_time
    echo ""

    check_database
    echo ""

    check_redis
    echo ""

    check_celery
    echo ""

    check_disk_space
    echo ""

    check_memory
    echo ""

    echo "================================"
    if [ "$OVERALL_STATUS" -eq 0 ]; then
        echo -e "${GREEN}Overall Status: HEALTHY${NC}"
        exit 0
    else
        echo -e "${RED}Overall Status: UNHEALTHY${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
