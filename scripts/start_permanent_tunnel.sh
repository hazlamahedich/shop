#!/bin/bash

# Configuration
LOCAL_PORT=8000
# zrok unique names must be STRICTLY alphanumeric (no dashes) and < 32 chars.
USER_SHORT=$(echo $(whoami) | tr -cd '[:alnum:]' | cut -c 1-10)
TUNNEL_NAME="shopdev${USER_SHORT}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ENV_FILE="$SCRIPT_DIR/../backend/.env"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Permanent Tunnel Manager (zrok) ===${NC}"

# Check if zrok is installed
if ! command -v zrok &> /dev/null; then
    echo -e "${YELLOW}zrok is not installed. Please run 'brew install zrok' first.${NC}"
    exit 1
fi

# Check if zrok is enabled
if ! zrok status &> /dev/null; then
    echo -e "${YELLOW}zrok is not enabled.${NC}"
    echo -e "Please follow the instructions in docs/zrok_setup.md to activate your free account."
    exit 1
fi

# Step 1: Reserve the share (if not already reserved)
echo -e "Checking for reserved share: ${GREEN}${TUNNEL_NAME}${NC}..."
# Attempt to reserve. If it fails because it already exists, that's fine.
RESERVE_OUT=$(zrok reserve public localhost:${LOCAL_PORT} --unique-name ${TUNNEL_NAME} 2>&1)
RESERVE_EXIT=$?

if [ $RESERVE_EXIT -eq 0 ]; then
    echo -e "${GREEN}Share '${TUNNEL_NAME}' reserved successfully!${NC}"
elif echo "$RESERVE_OUT" | grep -q -E "already exists|shareConflict"; then
    echo -e "${BLUE}Share '${TUNNEL_NAME}' already exists and is ready to use.${NC}"
else
    echo -e "${RED}Error reserving share:${NC}"
    echo "$RESERVE_OUT"
    exit 1
fi

TUNNEL_URL="https://${TUNNEL_NAME}.share.zrok.io"
echo -e "${BLUE}Your Permanent URL:${NC} ${YELLOW}${TUNNEL_URL}${NC}"

# Step 2: Update .env file automatically
if [ -f "$ENV_FILE" ]; then
    echo -e "Updating ${BLUE}.env${NC} with the permanent URL..."
    
    # Update APP_URL
    sed -i '' "s|^APP_URL=.*|APP_URL=${TUNNEL_URL}|" "$ENV_FILE"
    
    # Update CORS_ORIGINS (only if not already there)
    if ! grep -q "${TUNNEL_URL}" "$ENV_FILE"; then
        sed -i '' "s|^CORS_ORIGINS=|CORS_ORIGINS=${TUNNEL_URL},|" "$ENV_FILE"
    fi
    
    echo -e "${GREEN}.env file successfully updated!${NC}"
else
    echo -e "${YELLOW}Warning: .env file not found at $ENV_FILE. Skipping auto-update.${NC}"
fi

# Step 3: Start the tunnel
echo -e "${GREEN}Starting tunnel... Press Ctrl+C to stop.${NC}"
zrok share reserved ${TUNNEL_NAME} --headless
