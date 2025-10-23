#!/bin/bash

echo "========================================================================"
echo "☁️  AWS Lambda Configuration Comparison"
echo "========================================================================"
echo ""

# Build once
echo "📦 Building Docker image..."
docker build -f Dockerfile.etl -t etl-app . > /dev/null 2>&1 || {
    echo "❌ Build failed!"
    exit 1
}
echo "✅ Build complete"
echo ""

# Create results directory
mkdir -p lambda_results

# Define configurations
declare -A configs
configs=(
    ["lambda-min"]="128MB"
    ["lambda-small"]="256MB"
    ["lambda-medium"]="512MB"
    ["lambda-large"]="1GB"
    ["lambda-xl"]="2GB"
    ["lambda-max"]="3GB"
)

# Results file
results_file="lambda_results/comparison_$(date +%Y%m%d_%H%M%S).txt"

echo "Testing AWS Lambda configurations..." | tee "$results_file"
echo "======================================================================" | tee -a "$results_file"
echo "" | tee -a "$results_file"

# Test each configuration
for profile in lambda-min lambda-small lambda-medium lambda-large lambda-xl lambda-max; do
    mem="${configs[$profile]}"
    
    echo "🧪 Testing: $mem ($profile)" | tee -a "$results_file"
    echo "-------------------------------------------------------------------" | tee -a "$results_file"
    
    # Run the test and capture output
    docker-compose -f docker-compose.etl.yml --profile $profile up 2>&1 | \
        tee "lambda_results/${profile}.log" | \
        grep -E "(Successfully processed|Average time per file|Throughput|Total processing time)" | \
        tee -a "$results_file"
    
    echo "" | tee -a "$results_file"
    
    # Clean up
    docker-compose -f docker-compose.etl.yml --profile $profile down > /dev/null 2>&1
    
    sleep 2
done

echo "======================================================================" | tee -a "$results_file"
echo "✨ Comparison complete!" | tee -a "$results_file"
echo "" | tee -a "$results_file"
echo "📊 Results saved to: $results_file" | tee -a "$results_file"
echo "📁 Detailed logs in: lambda_results/" | tee -a "$results_file"
echo "" | tee -a "$results_file"

# Generate summary table
echo "📈 SUMMARY TABLE" | tee -a "$results_file"
echo "======================================================================" | tee -a "$results_file"
printf "%-15s %-20s %-15s %-15s\n" "Configuration" "Files Processed" "Avg Time/File" "Throughput" | tee -a "$results_file"
echo "----------------------------------------------------------------------" | tee -a "$results_file"

for profile in lambda-min lambda-small lambda-medium lambda-large lambda-xl lambda-max; do
    mem="${configs[$profile]}"
    
    # Extract metrics from log
    files=$(grep "Successfully processed" "lambda_results/${profile}.log" 2>/dev/null | grep -oP '\d+(?= files)')
    avg_time=$(grep "Average time per file" "lambda_results/${profile}.log" 2>/dev/null | grep -oP '\d+\.\d+')
    throughput=$(grep "Throughput" "lambda_results/${profile}.log" 2>/dev/null | grep -oP '\d+\.\d+')
    
    if [ -n "$files" ]; then
        printf "%-15s %-20s %-15s %-15s\n" "$mem" "$files files" "${avg_time}s" "${throughput} files/s" | tee -a "$results_file"
    else
        printf "%-15s %-20s\n" "$mem" "Failed or incomplete" | tee -a "$results_file"
    fi
done

echo "" | tee -a "$results_file"
echo "💡 Recommendation for your thesis:" | tee -a "$results_file"
echo "   • Use 2GB for optimal performance/cost balance" | tee -a "$results_file"
echo "   • Compare against 512MB as baseline" | tee -a "$results_file"
echo "   • Document memory headroom and throughput improvements" | tee -a "$results_file"

