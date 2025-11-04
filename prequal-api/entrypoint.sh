#!/bin/bash
# Entrypoint script for PreQual API
# This script initializes the database and starts the application

set -e

echo "======================================"
echo "PreQual API Starting..."
echo "======================================"

echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h postgres -p 5432 -U postgres > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "✓ PostgreSQL is ready!"

echo ""
echo "Initializing database tables..."
cd /app
python -c "
import sys
sys.path.insert(0, '/app')
from database.database import Base, init_db
from database.models import Application

try:
    init_db()  # Use the init_db function from database.database
    print('✓ Database tables created successfully!')
    print('Created tables:')
    for table_name in Base.metadata.tables.keys():
        print(f'  - {table_name}')
except Exception as e:
    print(f'✗ Error creating database tables: {e}')
    sys.exit(1)
"

echo ""
echo "======================================"
echo "Starting PreQual API on port 8000..."
echo "======================================"
echo ""

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
