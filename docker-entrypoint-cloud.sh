#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-etldb}" 2>/dev/null; do
    echo "   PostgreSQL is unavailable - sleeping..."
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Display memory limit information
if [ -f /sys/fs/cgroup/memory/memory.limit_in_bytes ]; then
    MEM_LIMIT=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)
    MEM_LIMIT_MB=$((MEM_LIMIT / 1024 / 1024))
    echo "💾 Container Memory Limit: ${MEM_LIMIT_MB} MB"
fi

# Display system information
echo "📊 System Information:"
echo "   Python: $(python --version)"
echo "   PostgreSQL Client: $(psql --version 2>/dev/null || echo 'Not available')"
echo "   Working Directory: $(pwd)"
echo "   Dataset Path: ${DATASET_PATH:-/data/datasetcovid.zip}"
echo ""

# Display database connection info (without password)
echo "🔌 Database Connection:"
echo "   Host: ${DB_HOST:-postgres}"
echo "   Port: ${DB_PORT:-5432}"
echo "   Database: ${DB_NAME:-etldb}"
echo "   User: ${DB_USER:-postgres}"
echo ""

# Execute the command passed as arguments
exec "$@"


