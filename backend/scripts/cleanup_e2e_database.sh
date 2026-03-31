#!/bin/bash
# Cleanup Database after E2E Tests (Story 11-1)
#
# This script cleans up test data from E2E tests.
#
# Usage: ./scripts/cleanup_e2e_database.sh
# Environment variables:
#   - DATABASE_URL: PostgreSQL connection string (default: postgresql://developer:developer@localhost:5432/shop_dev)
#   - DRY_RUN: Set to "true" to see what would be deleted (default: false)

set -e  # Exit on error

# Default values
DATABASE_URL="${DATABASE_URL:-postgresql://developer:developer@localhost:5432/shop_dev}"
DRY_RUN="${DRY_RUN:-false}"

echo "=== Cleaning up database after E2E tests ==="
echo "Database: $DATABASE_URL"
echo "Dry run: $DRY_RUN"
echo ""

# Extract connection details from DATABASE_URL
DB_HOST=$(echo $DATABASE_URL | awk -F[@] '{print $2}' | awk -F[:] '{print $1}')
DB_PORT=$(echo $DATABASE_URL | awk -F[@] '{print $2}' | awk -F[:] '{print $2}' | awk -F[\/] '{print $1}')
DB_USER=$(echo $DATABASE_URL | awk -F[\/\/] '{print $2}' | awk -F[:] '{print $1}')
DB_NAME=$(echo $DATABASE_URL | awk -F[\/] '{print $4}' | awk -F[\?] '{print $1}')

# Function to execute SQL (with dry run support)
execute_sql() {
    local sql=$1
    if [ "$DRY_RUN" = "true" ]; then
        echo "[DRY RUN] Would execute: $sql"
    else
        psql -U "$DB_USER" -h "$DB_HOST" -p "${DB_PORT:-5432}" -d "$DB_NAME" -c "$sql"
    fi
}

# Function to cleanup test merchants
cleanup_test_merchants() {
    echo "Cleaning up test merchants..."

    execute_sql "
        DELETE FROM conversation_context
        WHERE merchant_id IN (
            SELECT id FROM merchants
            WHERE merchant_key LIKE 'test_%'
            OR merchant_key LIKE '%_test'
            OR merchant_key LIKE 'e2e_%'
        );
    "

    execute_sql "
        DELETE FROM conversations
        WHERE merchant_id IN (
            SELECT id FROM merchants
            WHERE merchant_key LIKE 'test_%'
            OR merchant_key LIKE '%_test'
            OR merchant_key LIKE 'e2e_%'
        );
    "

    execute_sql "
        DELETE FROM merchants
        WHERE merchant_key LIKE 'test_%'
        OR merchant_key LIKE '%_test'
        OR merchant_key LIKE 'e2e_%';
    "

    echo "✓ Test merchants cleaned up"
}

# Function to cleanup test conversations
cleanup_test_conversations() {
    echo "Cleaning up test conversations..."

    execute_sql "
        DELETE FROM conversation_context
        WHERE conversation_id IN (
            SELECT id FROM conversations
            WHERE platform_sender_id LIKE 'test_%'
            OR platform_sender_id LIKE '%_test'
            OR platform_sender_id LIKE 'e2e_%'
        );
    "

    execute_sql "
        DELETE FROM conversation_turns
        WHERE conversation_id IN (
            SELECT id FROM conversations
            WHERE platform_sender_id LIKE 'test_%'
            OR platform_sender_id LIKE '%_test'
            OR platform_sender_id LIKE 'e2e_%'
        );
    "

    execute_sql "
        DELETE FROM messages
        WHERE conversation_id IN (
            SELECT id FROM conversations
            WHERE platform_sender_id LIKE 'test_%'
            OR platform_sender_id LIKE '%_test'
            OR platform_sender_id LIKE 'e2e_%'
        );
    "

    execute_sql "
        DELETE FROM conversations
        WHERE platform_sender_id LIKE 'test_%'
        OR platform_sender_id LIKE '%_test'
        OR platform_sender_id LIKE 'e2e_%';
    "

    echo "✓ Test conversations cleaned up"
}

# Function to show summary
show_summary() {
    if [ "$DRY_RUN" = "true" ]; then
        echo ""
        echo "=== Dry Run Summary ==="
        echo "This would delete:"
        echo "  - Test merchants (merchant_key LIKE 'test_%' OR '%_test' OR 'e2e_%')"
        echo "  - Test conversations (platform_sender_id LIKE 'test_%' OR '%_test' OR 'e2e_%')"
        echo "  - Related conversation_context, conversation_turns, and messages"
    else
        echo ""
        echo "=== Cleanup Summary ==="

        local remaining_merchants=$(psql -U "$DB_USER" -h "$DB_HOST" -p "${DB_PORT:-5432}" -d "$DB_NAME" -tAc "
            SELECT COUNT(*) FROM merchants
            WHERE merchant_key LIKE 'test_%' OR merchant_key LIKE '%_test' OR merchant_key LIKE 'e2e_%';
        " 2>/dev/null || echo "0")

        local remaining_conversations=$(psql -U "$DB_USER" -h "$DB_HOST" -p "${DB_PORT:-5432}" -d "$DB_NAME" -tAc "
            SELECT COUNT(*) FROM conversations
            WHERE platform_sender_id LIKE 'test_%' OR platform_sender_id LIKE '%_test' OR platform_sender_id LIKE 'e2e_%';
        " 2>/dev/null || echo "0")

        echo "Remaining test data:"
        echo "  - Test merchants: $remaining_merchants"
        echo "  - Test conversations: $remaining_conversations"

        if [ "$remaining_merchants" = "0" ] && [ "$remaining_conversations" = "0" ]; then
            echo "✓ All test data cleaned up successfully!"
        else
            echo "⚠ Some test data remains. You may need to run cleanup again."
        fi
    fi
}

# Main execution
main() {
    # Check if PostgreSQL client is available
    if ! command -v psql &> /dev/null; then
        echo "Error: psql client not found. Please install PostgreSQL client tools."
        exit 1
    fi

    # Check connection
    echo "Testing database connection..."
    if ! psql -U "$DB_USER" -h "$DB_HOST" -p "${DB_PORT:-5432}" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
        echo "Error: Cannot connect to database. Please check your DATABASE_URL."
        exit 1
    fi
    echo "✓ Database connection successful"
    echo ""

    # Cleanup
    cleanup_test_merchants
    cleanup_test_conversations

    # Summary
    show_summary
}

main "$@"
