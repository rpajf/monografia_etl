#!/bin/bash
# Script para executar benchmarks com limites realistas de cloud
# Testa múltiplos cenários: 512MB, 1GB, 2GB, 4GB

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Benchmark Realista de Cloud Environments${NC}"
echo "============================================================"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "   Este script testa limites REALISTAS de cloud:"
echo "   - 512MB: AWS Lambda básico / Cloud Run mínimo"
echo "   - 1GB:   AWS Lambda comum / Cloud Run médio"
echo "   - 2GB:   AWS Lambda premium / ECS Fargate pequeno"
echo "   - 4GB:   ECS Fargate médio"
echo ""
echo -e "${RED}❌ NÃO usa 10GB (não é representativo de recursos limitados!)${NC}"
echo ""

# Check if dataset file exists
DATASET_PATH="${DATASET_PATH:-/Users/raphaelportela/datasetcovid.zip}"
if [ ! -f "$DATASET_PATH" ]; then
    echo -e "${RED}❌ Error: Dataset file not found at $DATASET_PATH${NC}"
    echo "   Please set DATASET_PATH environment variable or update the path"
    exit 1
fi

# Build the Docker image
echo ""
echo -e "${BLUE}📦 Building Docker image...${NC}"
docker build -f Dockerfile.cloud -t etl-cloud:latest .

# Stop and remove existing containers if they exist
echo ""
echo -e "${BLUE}🧹 Cleaning up existing containers...${NC}"
docker-compose -f docker-compose.cloud.yml down 2>/dev/null || true

# Start PostgreSQL first
echo ""
echo -e "${BLUE}🗄️  Starting PostgreSQL database...${NC}"
docker-compose -f docker-compose.cloud.yml up -d postgres

# Wait for PostgreSQL to be ready
echo ""
echo -e "${BLUE}⏳ Waiting for PostgreSQL to be ready...${NC}"
sleep 5

# Get the actual container name
POSTGRES_CONTAINER=$(docker ps --filter "name=postgres" --format "{{.Names}}" | grep -E "(postgres|etl_postgres)" | head -n 1)

if [ -z "$POSTGRES_CONTAINER" ]; then
    POSTGRES_CONTAINER="etl_postgres_cloud"
fi

echo "   Using PostgreSQL container: $POSTGRES_CONTAINER"

until docker exec "$POSTGRES_CONTAINER" pg_isready -U postgres -d etldb > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"

# Get the actual network name
NETWORK_NAME=$(docker network ls --filter "name=etl_network_cloud" --format "{{.Name}}" | head -n 1)

if [ -z "$NETWORK_NAME" ]; then
    NETWORK_NAME=$(docker network ls --format "{{.Name}}" | grep "etl_network_cloud" | head -n 1)
fi

if [ -z "$NETWORK_NAME" ]; then
    echo -e "${RED}❌ Error: Could not find network.${NC}"
    docker network ls
    exit 1
fi

echo "🌐 Using network: $NETWORK_NAME"
echo ""

# Define memory limits to test
declare -a MEMORY_LIMITS=("512m" "1g" "2g" "4g")
declare -a CPU_LIMITS=("1.0" "1.5" "2.0" "2.0")
declare -a SCENARIOS=("AWS Lambda Básico" "AWS Lambda Comum" "AWS Lambda Premium" "ECS Fargate Médio")

# Ask user which scenarios to run
echo -e "${YELLOW}Escolha os cenários para testar:${NC}"
echo "1) Todos os cenários (512MB, 1GB, 2GB, 4GB)"
echo "2) Apenas Serverless (512MB, 1GB, 2GB)"
echo "3) Apenas 1GB e 2GB (mais representativos)"
echo "4) Apenas 2GB (serverless premium)"
echo "5) Customizado"
echo ""
read -p "Escolha (1-5): " choice

case $choice in
    1)
        SELECTED_INDICES=(0 1 2 3)
        ;;
    2)
        SELECTED_INDICES=(0 1 2)
        ;;
    3)
        SELECTED_INDICES=(1 2)
        ;;
    4)
        SELECTED_INDICES=(2)
        ;;
    5)
        echo ""
        echo "Escolha os índices (0=512MB, 1=1GB, 2=2GB, 3=4GB):"
        read -p "Índices (separados por espaço): " indices
        SELECTED_INDICES=($indices)
        ;;
    *)
        echo -e "${RED}Opção inválida. Executando todos os cenários.${NC}"
        SELECTED_INDICES=(0 1 2 3)
        ;;
esac

echo ""
echo -e "${GREEN}📊 Executando ${#SELECTED_INDICES[@]} cenário(s)...${NC}"
echo ""

# Create results directory
RESULTS_DIR="cloud_benchmark_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# Run benchmarks for each selected scenario
for idx in "${SELECTED_INDICES[@]}"; do
    MEM_LIMIT="${MEMORY_LIMITS[$idx]}"
    CPU_LIMIT="${CPU_LIMITS[$idx]}"
    SCENARIO="${SCENARIOS[$idx]}"
    
    echo ""
    echo "============================================================"
    echo -e "${BLUE}🔵 Cenário: $SCENARIO${NC}"
    echo -e "${BLUE}   Memória: $MEM_LIMIT | CPU: $CPU_LIMIT${NC}"
    echo "============================================================"
    echo ""
    
    # Create scenario-specific result directories
    SCENARIO_DIR="$RESULTS_DIR/${MEM_LIMIT}"
    mkdir -p "$SCENARIO_DIR/sync_result"
    mkdir -p "$SCENARIO_DIR/async_result"
    mkdir -p "$SCENARIO_DIR/output"
    
    # Run the ETL application with memory limit
    docker run --rm \
        --name "etl_app_cloud_${MEM_LIMIT}" \
        --memory="$MEM_LIMIT" \
        --memory-swap="$MEM_LIMIT" \
        --cpus="$CPU_LIMIT" \
        --network "$NETWORK_NAME" \
        -e DB_HOST=postgres \
        -e DB_PORT=5432 \
        -e DB_NAME=etldb \
        -e DB_USER=postgres \
        -e DB_PASSWORD="" \
        -e DATASET_PATH=/data/datasetcovid.zip \
        -e MEMORY_LIMIT="$MEM_LIMIT" \
        -e SCENARIO_NAME="$SCENARIO" \
        -v "$(pwd):/app" \
        -v "$DATASET_PATH:/data/datasetcovid.zip:ro" \
        -v "$(pwd)/$SCENARIO_DIR/sync_result:/app/sync_result" \
        -v "$(pwd)/$SCENARIO_DIR/async_result:/app/async_result" \
        -v "$(pwd)/$SCENARIO_DIR/output:/app/output" \
        etl-cloud:latest python main.py || {
            echo -e "${RED}❌ Erro ao executar com $MEM_LIMIT${NC}"
            echo "   Possível OOM (Out of Memory) ou outro erro"
            continue
        }
    
    echo ""
    echo -e "${GREEN}✅ Cenário $SCENARIO ($MEM_LIMIT) concluído!${NC}"
    echo "   Resultados salvos em: $SCENARIO_DIR/"
done

echo ""
echo "============================================================"
echo -e "${GREEN}✅ Todos os benchmarks concluídos!${NC}"
echo "============================================================"
echo ""
echo -e "${BLUE}📊 Resultados salvos em: $RESULTS_DIR/${NC}"
echo ""
echo "Estrutura:"
echo "  $RESULTS_DIR/"
for idx in "${SELECTED_INDICES[@]}"; do
    MEM_LIMIT="${MEMORY_LIMITS[$idx]}"
    echo "    ├── $MEM_LIMIT/"
    echo "    │   ├── sync_result/    (gráficos benchmark síncrono)"
    echo "    │   ├── async_result/   (gráficos benchmark assíncrono)"
    echo "    │   └── output/        (outros outputs)"
done
echo ""
echo -e "${YELLOW}💡 Dica: Compare os resultados para analisar trade-offs de memória vs performance${NC}"
echo ""

# Optional: Keep PostgreSQL running for inspection
read -p "Parar PostgreSQL? (s/N): " stop_postgres
if [[ "$stop_postgres" =~ ^[Ss]$ ]]; then
    docker-compose -f docker-compose.cloud.yml down
    echo -e "${GREEN}✅ PostgreSQL parado.${NC}"
else
    echo -e "${BLUE}ℹ️  PostgreSQL continua rodando para inspeção.${NC}"
fi


