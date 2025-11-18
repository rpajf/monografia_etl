#!/bin/bash
# Script para executar benchmark ETL ASSÍNCRONO com limite de 4GB (ECS Fargate médio)
# Simula ambiente cloud containerizado típico

set -e

echo "🚀 Benchmark ETL ASSÍNCRONO - Ambiente Cloud 4GB (ECS Fargate Médio)"
echo "======================================================================"

# Check if dataset file exists
DATASET_PATH="${DATASET_PATH:-/Users/raphaelportela/datasetcovid.zip}"
if [ ! -f "$DATASET_PATH" ]; then
    echo "❌ Error: Dataset file not found at $DATASET_PATH"
    echo "   Please set DATASET_PATH environment variable or update the path"
    exit 1
fi

# Build the Docker image
echo ""
echo "📦 Building Docker image..."
docker build -f Dockerfile.cloud -t etl-cloud:latest .

# Stop and remove existing containers if they exist (only ETL app, keep postgres)
echo ""
echo "🧹 Cleaning up existing ETL containers..."
docker rm -f etl_app_cloud_4gb_async 2>/dev/null || true

# Check if PostgreSQL is running, if not start it
POSTGRES_CONTAINER=$(docker ps --filter "name=postgres" --format "{{.Names}}" | grep -E "(postgres|etl_postgres)" | head -n 1)

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo ""
    echo "🗄️  Starting PostgreSQL database..."
    docker-compose -f docker-compose.cloud.yml up -d postgres
    sleep 5
    POSTGRES_CONTAINER="etl_postgres_cloud"
else
    echo ""
    echo "✅ PostgreSQL already running: $POSTGRES_CONTAINER"
fi

# Wait for PostgreSQL to be ready
echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec "$POSTGRES_CONTAINER" pg_isready -U postgres -d etldb > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Get the actual network name created by docker-compose
NETWORK_NAME=$(docker network ls --filter "name=etl_network_cloud" --format "{{.Name}}" | head -n 1)

if [ -z "$NETWORK_NAME" ]; then
    echo "⚠️  Network not found with filter. Searching for network..."
    NETWORK_NAME=$(docker network ls --format "{{.Name}}" | grep "etl_network_cloud" | head -n 1)
fi

if [ -z "$NETWORK_NAME" ]; then
    echo "❌ Error: Could not find network. Available networks:"
    docker network ls
    exit 1
fi

echo "🌐 Using network: $NETWORK_NAME"

# Run the ETL application with 4GB memory limit (ASYNC)
echo ""
echo "🟢 Running ASYNC ETL pipeline with 4GB memory limit..."
echo "   Simulating: ECS Fargate Medium (4GB RAM, 2.0 vCPU)"
echo "   Method: Asynchronous Parallel Processing"
echo "   Workers: 4"
echo ""

docker run --rm \
    --name etl_app_cloud_4gb_async \
    --memory=4g \
    --memory-swap=4g \
    --cpus="2.0" \
    --network "$NETWORK_NAME" \
    -e DB_HOST=postgres \
    -e DB_PORT=5432 \
    -e DB_NAME=etldb \
    -e DB_USER=postgres \
    -e DB_PASSWORD="" \
    -e DATASET_PATH=/data/datasetcovid.zip \
    -e MEMORY_LIMIT="4g" \
    -e SCENARIO_NAME="ECS Fargate Medium - Async" \
    -e ASYNC_OUTPUT_DIR="async_docker" \
    -v "$(pwd):/app" \
    -v "$DATASET_PATH:/data/datasetcovid.zip:ro" \
    -v "$(pwd)/output:/app/output" \
    -v "$(pwd)/sync_result:/app/sync_result" \
    -v "$(pwd)/async_docker:/app/async_docker" \
    etl-cloud:latest python main_async.py

echo ""
echo "✅ ASYNC ETL pipeline completed!"
echo ""
echo "📊 Results saved to:"
echo "   - async_docker/ (async benchmark graphs)"
echo "   - sync_result/ (sync benchmark graphs - if any)"
echo "   - output/ (other outputs)"
echo ""
echo "💡 Memory Limit: 4GB (25% of your Mac's 16GB)"
echo "   This simulates a typical ECS Fargate medium container"
echo "   Method: Asynchronous parallel processing with 4 workers"
echo ""

# Optional: Keep PostgreSQL running for inspection
read -p "Stop PostgreSQL? (y/N): " stop_postgres
if [[ "$stop_postgres" =~ ^[Yy]$ ]]; then
    docker-compose -f docker-compose.cloud.yml down
    echo "✅ PostgreSQL stopped."
else
    echo "ℹ️  PostgreSQL continues running for inspection."
fi

