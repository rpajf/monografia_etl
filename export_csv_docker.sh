#!/bin/bash

echo "========================================================================"
echo "📊 Export JSON to CSV using Docker"
echo "========================================================================"
echo ""

# Create output directory
mkdir -p output

# Number of files to process
NUM_FILES=${1:-100}

echo "Configuration:"
echo "  Files to process: $NUM_FILES"
echo "  Output: ./output/json_data.csv"
echo ""

# Build if needed
if ! docker image inspect etl-app > /dev/null 2>&1; then
    echo "📦 Building Docker image..."
    docker build -f Dockerfile.etl -t etl-app .
fi

echo "🚀 Running CSV export..."
echo ""

# Run with CSV export enabled
docker run --rm \
  --memory=2g \
  --cpus=2.0 \
  -v $(pwd)/fetch_db_docker.py:/app/fetch_db.py:ro \
  -v /Users/raphaelportela/datasetcovid.zip:/data/datasetcovid.zip:ro \
  -v $(pwd)/output:/app/output \
  -e NUM_FILES=$NUM_FILES \
  -e SAVE_CSV=true \
  -e VERBOSE=false \
  etl-app python fetch_db.py

echo ""
echo "========================================================================"
echo "✅ CSV export complete!"
echo "📁 File location: ./output/json_data.csv"
echo ""
echo "To view:"
echo "  cat output/json_data.csv | head -20"
echo "  open output/json_data.csv  # Opens in Excel/default app"
echo "========================================================================"

