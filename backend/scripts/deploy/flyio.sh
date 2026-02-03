#!/bin/bash
# Fly.io Deployment Script for Shopping Assistant Bot
# Usage: ./flyio.sh <MERCHANT_KEY> <SECRET_KEY>
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Required arguments
MERCHANT_KEY="${1:-}"
SECRET_KEY="${2:-}"

# Validate arguments
if [[ -z "$MERCHANT_KEY" ]] || [[ -z "$SECRET_KEY" ]]; then
    echo -e "${RED}ERROR: Missing required arguments${NC}"
    echo "Usage: $0 <MERCHANT_KEY> <SECRET_KEY>"
    exit 1
fi

# Configuration
APP_NAME="shop-bot-${MERCHANT_KEY}"
ORGANIZATION="personal"
REGION="iad"  # Default region (US East)

# Progress tracking
PROGRESS=0
MAX_PROGRESS=100

log_progress() {
    local step=$1
    local message=$2
    PROGRESS=$3
    echo -e "${BLUE}[${PROGRESS}%]${NC} $step: $message"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Error handler with specific messaging and troubleshooting links
handle_error() {
    local step=$1
    local error_type=$2
    local troubleshooting_url=$3
    log_error "Deployment failed at step: $step"
    log_error "Error type: $error_type"
    if [[ -n "$troubleshooting_url" ]]; then
        log_error "Troubleshooting: $troubleshooting_url"
    fi
    exit 1
}

trap 'handle_error "Unknown error during deployment" "unknown" "https://fly.io/docs/troubleshooting"' ERR

# Check prerequisites
check_fly_cli() {
    if ! command -v fly &> /dev/null; then
        handle_error "CLI check" "fly-cli-missing" "https://fly.io/docs/hands-on/install/"
    fi
    log_success "Fly CLI detected"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        handle_error "Docker check" "docker-missing" "https://docs.docker.com/get-docker/"
    fi
    log_success "Docker detected"
}

# Deploy to Fly.io
deploy_flyio() {
    log_progress "Prerequisites" "Checking required tools" 10
    check_fly_cli
    check_docker

    # Login check (will prompt if not authenticated)
    log_progress "Authentication" "Verifying Fly.io authentication" 20
    if ! fly auth whoami &> /dev/null; then
        log_warning "Not authenticated with Fly.io. Please run: fly auth login"
        handle_error "Authentication" "not-authenticated" "https://fly.io/docs/hands-on/install/"
    fi
    log_success "Authenticated with Fly.io"

    # Check if app exists, create if not
    log_progress "App Setup" "Creating/checking Fly.io app" 30
    if fly apps list --json | grep -q "\"Name\":\"$APP_NAME\""; then
        log_warning "App $APP_NAME already exists, skipping creation"
    else
        fly apps create "$APP_NAME" --org "$ORGANIZATION" --json || {
            handle_error "App creation" "app-create-failed" "https://fly.io/docs/reference/apps/"
        }
        log_success "Created app: $APP_NAME"
    fi

    # Set regions (optional - uses default)
    log_progress "Configuration" "Setting app regions" 40
    fly regions set "$REGION" --app "$APP_NAME" --json || log_warning "Could not set region, using default"

    # Create fly.toml if it doesn't exist
    log_progress "Configuration" "Setting up fly.toml" 50
    cat > fly.toml << EOF
app = "$APP_NAME"
primary_region = "$REGION"

[build]
  dockerfile = "backend/Dockerfile"

[env]
  MERCHANT_KEY = "$MERCHANT_KEY"
  SECRET_KEY = "$SECRET_KEY"
  DEBUG = "false"
  LOG_LEVEL = "info"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[http_service.checks]]
  interval = "15s"
  timeout = "10s"
  grace_period = "5s"
  method = "GET"
  path = "/health"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
EOF
    log_success "Created fly.toml configuration"

    # Set secrets
    log_progress "Secrets" "Setting environment secrets" 60
    fly secrets set "MERCHANT_KEY=$MERCHANT_KEY" "SECRET_KEY=$SECRET_KEY" "DEBUG=false" --app "$APP_NAME" || {
        handle_error "Secrets configuration" "secrets-failed" "https://fly.io/docs/reference/secrets/"
    }
    log_success "Set environment secrets"

    # Deploy application
    log_progress "Deployment" "Building and deploying containers" 70
    deploy_output=$(fly deploy --app "$APP_NAME" --remote-only --json 2>&1)
    deploy_exit=$?

    if [[ $deploy_exit -ne 0 ]]; then
        if echo "$deploy_output" | grep -q "timeout"; then
            handle_error "Container build" "build-timeout" "https://fly.io/docs/reference/builds/"
        fi
        handle_error "Deployment" "deploy-failed" "https://fly.io/docs/troubleshooting/"
    fi
    log_success "Deployment completed successfully"

    # Wait for app to be healthy
    log_progress "Health Check" "Verifying deployment health" 90
    local max_attempts=30
    local attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        if fly status --app "$APP_NAME" --json 2>/dev/null | grep -q '"Running":true'; then
            log_success "App is running and healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [[ $attempt -eq $max_attempts ]]; then
        log_warning "App deployed but health check timed out"
    fi

    # Get app URL
    APP_URL=$(fly info --app "$APP_NAME" --json | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)
    log_progress "Complete" "Deployment successful!" 100
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo ""
    echo -e "App Name: ${BLUE}$APP_NAME${NC}"
    echo -e "App URL: ${BLUE}https://$APP_URL${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Connect your Facebook Page (Story 1.3)"
    echo "  2. Connect your Shopify Store (Story 1.4)"
    echo "  3. Configure LLM Provider (Story 1.5)"
    echo ""
    echo -e "Monitor logs: ${BLUE}fly logs --app $APP_NAME${NC}"
    echo -e "View status: ${BLUE}fly status --app $APP_NAME${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main deployment flow
main() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Fly.io Deployment Script${NC}"
    echo -e "${BLUE}Shopping Assistant Bot - One-Click Deployment${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""

    deploy_flyio

    echo ""
    log_success "STEP:SUCCESS"
}

# Run main function
main "$@"
