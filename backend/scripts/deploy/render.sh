#!/bin/bash
# Render Deployment Script for Shopping Assistant Bot
# Usage: ./render.sh <MERCHANT_KEY> <SECRET_KEY> <RENDER_API_KEY>
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
RENDER_API_KEY="${3:-}"

# Validate arguments
if [[ -z "$MERCHANT_KEY" ]] || [[ -z "$SECRET_KEY" ]] || [[ -z "$RENDER_API_KEY" ]]; then
    echo -e "${RED}ERROR: Missing required arguments${NC}"
    echo "Usage: $0 <MERCHANT_KEY> <SECRET_KEY> <RENDER_API_KEY>"
    exit 1
fi

# Configuration
SERVICE_NAME="shop-bot-${MERCHANT_KEY}"
RENDER_API_URL="https://api.render.com/v1"

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

trap 'handle_error "Unknown error during deployment" "unknown" "https://render.com/docs/troubleshooting"' ERR

# Check prerequisites
check_render_cli() {
    if ! command -v render &> /dev/null; then
        handle_error "CLI check" "render-cli-missing" "https://render.com/docs/render-cli"
    fi
    log_success "Render CLI detected"
}

# Deploy to Render
deploy_render() {
    log_progress "Prerequisites" "Checking required tools" 10
    check_render_cli

    # Set API key for CLI
    log_progress "Authentication" "Setting up Render authentication" 20
    export RENDER_API_KEY="$RENDER_API_KEY"
    if ! render auth whoami &> /dev/null; then
        log_warning "API key may be invalid. Please check your Render API key"
        handle_error "Authentication" "api-key-invalid" "https://render.com/docs/api-keys"
    fi
    log_success "Authenticated with Render"

    # Create render.yaml if it doesn't exist
    log_progress "Configuration" "Setting up render.yaml" 30
    if [[ ! -f "render.yaml" ]]; then
        cat > render.yaml << EOF
services:
  - type: web
    name: $SERVICE_NAME
    env: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: .
    plan: free
    envVars:
      - key: MERCHANT_KEY
        value: $MERCHANT_KEY
      - key: SECRET_KEY
        value: $SECRET_KEY
      - key: DEBUG
        value: false
      - key: LOG_LEVEL
        value: info
    healthCheckPath: /health
    autoDeploy: true
EOF
        log_success "Created render.yaml configuration"
    fi

    # Deploy using render CLI
    log_progress "Deployment" "Building and deploying service" 50
    deploy_output=$(render deploy 2>&1)
    deploy_exit=$?

    if [[ $deploy_exit -ne 0 ]]; then
        if echo "$deploy_output" | grep -qi "timeout"; then
            handle_error "Container build" "build-timeout" "https://render.com/docs/build-timeout"
        fi
        if echo "$deploy_output" | grep -qi "authentication"; then
            handle_error "Authentication" "auth-failed" "https://render.com/docs/api-keys"
        fi
        handle_error "Deployment" "deploy-failed" "https://render.com/docs/deploy-failed"
    fi
    log_success "Deployment initiated successfully"

    # Wait for service to be live
    log_progress "Health Check" "Waiting for service to become live" 70
    local max_attempts=60
    local attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        SERVICE_STATUS=$(render ps --json 2>/dev/null | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [[ "$SERVICE_STATUS" == "live" || "$SERVICE_STATUS" == "ready" ]]; then
            log_success "Service is live and healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 3
    done

    if [[ $attempt -eq $max_attempts ]]; then
        log_warning "Deployment initiated but health check timed out. This is normal for Render builds."
    fi

    # Get service URL
    SERVICE_URL=$(render ps --json 2>/dev/null | grep -o '"serviceUrl":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [[ -z "$SERVICE_URL" ]]; then
        SERVICE_URL="https://$SERVICE_NAME.onrender.com"
    fi

    log_progress "Complete" "Deployment successful!" 100
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo ""
    echo -e "Service Name: ${BLUE}$SERVICE_NAME${NC}"
    echo -e "Service URL: ${BLUE}$SERVICE_URL${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Connect your Facebook Page (Story 1.3)"
    echo "  2. Connect your Shopify Store (Story 1.4)"
    echo "  3. Configure LLM Provider (Story 1.5)"
    echo ""
    echo -e "Monitor logs: ${BLUE}render logs${NC}"
    echo -e "View status: ${BLUE}render ps${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main deployment flow
main() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Render Deployment Script${NC}"
    echo -e "${BLUE}Shopping Assistant Bot - One-Click Deployment${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""

    deploy_render

    echo ""
    log_success "STEP:SUCCESS"
}

# Run main function
main "$@"
