#!/bin/bash
set -e

# Entrypoint script for backend API
# Waits for required services before starting

echo " Starting IKSAN AI Interview Backend API..."

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "⏳ Waiting for PostgreSQL to be ready..."
    until python -c "
import psycopg2
import os
import sys
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL', '')
if not db_url:
    print('❌ DATABASE_URL not set')
    sys.exit(1)

# Parse the URL
parsed = urlparse(db_url)
try:
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:],
        connect_timeout=3
    )
    conn.close()
    print('✅ PostgreSQL is ready!')
except Exception as e:
    print(f'❌ PostgreSQL not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
}

# Run database migrations
run_migrations() {
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        echo "🔄 Running database migrations..."
        alembic upgrade head
        echo "✅ Migrations completed"
    else
        echo "⏭️  Skipping migrations (RUN_MIGRATIONS not set to true)"
    fi
}

# Main execution
wait_for_postgres

# Only run migrations if explicitly enabled
run_migrations

echo "✅ All dependencies ready - starting application"

# Execute the main command
exec "$@"
