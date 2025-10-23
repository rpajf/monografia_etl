#!/bin/bash

echo "========================================================================"
echo "🐳 ETL Resource Constraint Testing Suite"
echo "========================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Build the image first
echo "📦 Building Docker image..."
docker build -f Dockerfile.etl -t etl-app . || {
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
}
echo -e "${GREEN}✅ Build complete${NC}"
echo ""

# Function to run a test
run_test() {
    local profile=$1
    local mem=$2
    local files=$3
    
    echo "========================================================================"
    echo "🧪 Testing: $profile ($mem memory, $files files)"
    echo "========================================================================"
    
    docker-compose -f docker-compose.etl.yml --profile $profile up --abort-on-container-exit 2>&1 | tee "logs/${profile}_test.log"
    
    exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ $profile test PASSED${NC}"
    else
        echo -e "${RED}❌ $profile test FAILED (exit code: $exit_code)${NC}"
    fi
    
    echo ""
    sleep 2
    
    # Clean up
    docker-compose -f docker-compose.etl.yml --profile $profile down > /dev/null 2>&1
}

# Create logs directory
mkdir -p logs

# Menu
echo "Select test scenario:"
echo "  1) Micro (2MB) - Expected to fail"
echo "  2) Tiny (64MB) - Minimal"
echo "  3) Small (128MB) - Basic"
echo "  4) Medium (512MB) - Comfortable"
echo "  5) Unlimited - Baseline"
echo "  6) Run all tests"
echo "  7) Quick comparison (tiny, small, medium)"
echo ""
read -p "Enter choice (1-7): " choice

case $choice in
    1)
        run_test "micro" "2MB" "5"
        ;;
    2)
        run_test "tiny" "64MB" "10"
        ;;
    3)
        run_test "small" "128MB" "50"
        ;;
    4)
        run_test "medium" "512MB" "500"
        ;;
    5)
        run_test "unlimited" "unlimited" "1000"
        ;;
    6)
        echo "Running all tests..."
        run_test "micro" "2MB" "5"
        run_test "tiny" "64MB" "10"
        run_test "small" "128MB" "50"
        run_test "medium" "512MB" "500"
        run_test "unlimited" "unlimited" "1000"
        
        echo ""
        echo "========================================================================"
        echo "📊 Test Summary"
        echo "========================================================================"
        grep -h "Successfully processed\|Average time per file\|Throughput" logs/*.log
        ;;
    7)
        echo "Running comparison tests..."
        run_test "tiny" "64MB" "10"
        run_test "small" "128MB" "50"
        run_test "medium" "512MB" "100"
        
        echo ""
        echo "========================================================================"
        echo "📊 Quick Comparison"
        echo "========================================================================"
        grep -h "Successfully processed\|Average time per file\|Throughput" logs/*.log
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "✨ Testing complete! Check logs/ directory for detailed output."
echo "========================================================================"

