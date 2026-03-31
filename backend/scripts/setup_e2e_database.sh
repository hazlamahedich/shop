#!/bin/bash
# Setup Database for E2E Tests (Story 11-1)
#
# This script sets up the database schema required for E2E tests,
# including the conversation_context tables.
#
# Usage: ./scripts/setup_e2e_database.sh
# Environment variables:
#   - DATABASE_URL: PostgreSQL connection string (default: postgresql://developer:developer@localhost:5432/shop_dev)
#   - SKIP_MIGRATIONS: Set to "true" to skip alembic migrations (default: false)

set -e  # Exit on error

# Default values
DATABASE_URL="${DATABASE_URL:-postgresql://developer:developer@localhost:5432/shop_dev}"
SKIP_MIGRATIONS="${SKIP_MIGRATIONS:-false}"

echo "=== Setting up database for E2E tests ==="
echo "Database: $DATABASE_URL"
echo ""

# Extract connection details from DATABASE_URL
DB_HOST=$(echo $DATABASE_URL | awk -F[@] '{print $2}' | awk -F[:] '{print $1}')
DB_PORT=$(echo $DATABASE_URL | awk -F[@] '{print $2}' | awk -F[:] '{print $2}' | awk -F[\/] '{print $1}')
DB_USER=$(echo $DATABASE_URL | awk -F[\/\/] '{print $2}' | awk -F[:] '{print $1}')
DB_NAME=$(echo $DATABASE_URL | awk -F[\/] '{print $4}' | awk -F[\?] '{print $1}')

echo "Connection details:"
echo "  Host: $DB_HOST"
echo "  Port: ${DB_PORT:-5432}"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"
echo ""

# Function to check if table exists
table_exists() {
    local table_name=$1
    psql -U "$DB_USER" -h "$DB_HOST" -p "${DB_PORT:-5432}" -d "$DB_NAME" -tAc \
        "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '$table_name');"
}

# Function to create conversation_context tables
create_conversation_context_tables() {
    echo "Creating conversation_context tables..."

    psql -U "$DB_USER" -h "$DB_HOST" -p "${DB_PORT:-5432}" -d "$DB_NAME" << 'EOF'
-- Create conversation_mode enum type
DO $$ BEGIN
    CREATE TYPE conversation_mode AS ENUM ('ecommerce', 'general');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create conversation_context table
CREATE TABLE IF NOT EXISTS conversation_context (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    mode conversation_mode NOT NULL,
    context_data JSONB NOT NULL,
    -- E-commerce fields
    viewed_products INTEGER[] NULL,
    cart_items INTEGER[] NULL,
    constraints JSONB NULL,
    search_history TEXT[] NULL,
    -- General mode fields
    topics_discussed TEXT[] NULL,
    documents_referenced INTEGER[] NULL,
    support_issues JSONB NULL,
    escalation_status VARCHAR(50) NULL,
    -- Universal fields
    preferences JSONB NULL,
    turn_count INTEGER NOT NULL DEFAULT 0,
    last_summarized_at TIMESTAMP NULL,
    expires_at TIMESTAMP NOT NULL DEFAULT NOW() + INTERVAL '24 hours',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_conversation_context_conversation ON conversation_context(conversation_id);
CREATE INDEX IF NOT EXISTS ix_conversation_context_mode ON conversation_context(mode);
CREATE INDEX IF NOT EXISTS ix_conversation_context_expires ON conversation_context(expires_at);

-- Create conversation_turns table
CREATE TABLE IF NOT EXISTS conversation_turns (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    extracted_context JSONB NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_conversation_turns_conversation ON conversation_turns(conversation_id);
EOF

    echo "✓ conversation_context tables created"
}

# Function to run alembic migrations
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        echo "Skipping migrations (SKIP_MIGRATIONS=true)"
        return
    fi

    echo "Running alembic migrations..."
    alembic upgrade head
    echo "✓ Migrations completed"
}

# Function to verify setup
verify_setup() {
    echo ""
    echo "Verifying database setup..."

    local tables=("conversation_context" "conversation_turns" "merchants" "conversations")
    local all_exist=true

    for table in "${tables[@]}"; do
        if [ "$(table_exists $table)" = "t" ]; then
            echo "  ✓ $table exists"
        else
            echo "  ✗ $table missing"
            all_exist=false
        fi
    done

    if [ "$all_exist" = true ]; then
        echo ""
        echo "✓ Database setup complete!"
        return 0
    else
        echo ""
        echo "✗ Database setup incomplete!"
        return 1
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

    # Create tables
    create_conversation_context_tables

    # Run migrations
    run_migrations

    # Verify
    verify_setup
}

main "$@"
