# Cloud Environment Simulation Guide

## 🎯 Overview

This guide explains how to run your ETL pipeline in Docker with a **10GB memory limit** to simulate cloud environment constraints (similar to AWS EC2, Google Cloud, etc.).

---

## 📋 Prerequisites

1. **Docker** installed and running
2. **Docker Compose** installed
3. **Dataset file** available at `/Users/raphaelportela/datasetcovid.zip` (or set `DATASET_PATH`)

---

## 🚀 Quick Start

### Option 1: Using the Script (Recommended)

```bash
# Make script executable (if not already)
chmod +x run_cloud_benchmark.sh

# Run the benchmark
./run_cloud_benchmark.sh
```

### Option 2: Using Docker Compose

```bash
# Start PostgreSQL
docker-compose -f docker-compose.cloud.yml up -d postgres

# Run ETL with memory limit
docker run --rm \
    --memory=10g \
    --network etl_network_cloud \
    -e DB_HOST=postgres \
    -e DATASET_PATH=/data/datasetcovid.zip \
    -v "$(pwd):/app" \
    -v "/Users/raphaelportela/datasetcovid.zip:/data/datasetcovid.zip:ro" \
    etl-cloud:latest python main.py
```

### Option 3: Manual Docker Run

```bash
# Build image
docker build -f Dockerfile.cloud -t etl-cloud:latest .

# Run with 10GB memory limit
docker run --rm \
    --memory=10g \
    --memory-swap=10g \
    --cpus="4.0" \
    --network host \
    -e DB_HOST=localhost \
    -e DB_PORT=5432 \
    -e DB_NAME=etldb \
    -e DB_USER=postgres \
    -e DATASET_PATH=/data/datasetcovid.zip \
    -v "$(pwd):/app" \
    -v "/Users/raphaelportela/datasetcovid.zip:/data/datasetcovid.zip:ro" \
    etl-cloud:latest python main.py
```

---

## 🔧 Configuration

### Memory Limits

The setup uses **10GB memory limit** to simulate cloud environments:

```bash
--memory=10g          # Hard limit: 10GB
--memory-swap=10g     # Total memory + swap: 10GB (no swap)
--cpus="4.0"          # CPU limit: 4 cores
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `etldb` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `""` | Database password (empty for local) |
| `DATASET_PATH` | `/data/datasetcovid.zip` | Path to dataset ZIP file |

---

## 📊 What Gets Executed

The pipeline runs `main.py` which:

1. ✅ Connects to PostgreSQL using psycopg3
2. ✅ Processes COVID-19 dataset from Kaggle
3. ✅ Runs sync benchmark (COPY method)
4. ✅ Generates performance graphs
5. ✅ Tracks memory usage (limited to 10GB)

---

## 🔍 Monitoring Memory Usage

### During Execution

The container will display:
- Container memory limit
- Current memory usage
- Peak memory usage

### Check Memory Usage Manually

```bash
# While container is running
docker stats etl_app_cloud

# Check memory limit
docker inspect etl_app_cloud | grep -i memory
```

---

## 📁 Output Files

Results are saved to:

- `sync_result/` - Sync benchmark graphs
- `async_result/` - Async benchmark graphs (if enabled)
- `output/` - Other outputs

These directories are mounted as volumes, so files persist on your host machine.

---

## 🐛 Troubleshooting

### PostgreSQL Connection Issues

**Problem:** Cannot connect to PostgreSQL

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs etl_postgres_cloud

# Test connection manually
docker exec etl_postgres_cloud psql -U postgres -d etldb -c "SELECT 1;"
```

### Memory Limit Issues

**Problem:** Container killed (OOM - Out of Memory)

**Solution:**
- Increase memory limit: `--memory=12g`
- Or optimize batch sizes in `main.py`

### Dataset Not Found

**Problem:** Dataset file not found

**Solution:**
```bash
# Set DATASET_PATH environment variable
export DATASET_PATH=/path/to/your/datasetcovid.zip

# Or update the volume mount in docker run command
-v "/your/path/datasetcovid.zip:/data/datasetcovid.zip:ro"
```

---

## 🎓 For Your Thesis

### Key Points to Document:

1. **Memory Constraint Simulation:**
   - 10GB limit simulates cloud VM (e.g., AWS EC2 t3.xlarge)
   - Real-world constraint for ETL optimization

2. **Connection Configuration:**
   - Uses environment variables (cloud-native approach)
   - Supports both Docker network and host network

3. **Resource Monitoring:**
   - Memory usage tracked within container limits
   - Performance metrics reflect constrained environment

---

## 📝 Example Output

```
🚀 Starting Cloud Environment Simulation (10GB Memory Limit)
============================================================

📦 Building Docker image...
🧹 Cleaning up existing containers...
🗄️  Starting PostgreSQL database...
⏳ Waiting for PostgreSQL to be ready...
✅ PostgreSQL is ready!

🔵 Running ETL pipeline with 10GB memory limit...
   This simulates a cloud environment constraint

💾 Container Memory Limit: 10240 MB
📊 System Information:
   Python: Python 3.11.x
   PostgreSQL Client: psql (PostgreSQL) 16.x
   Working Directory: /app
   Dataset Path: /data/datasetcovid.zip

🔌 Database Connection:
   Host: postgres
   Port: 5432
   Database: etldb
   User: postgres

📊 Total de arquivos JSON encontrados: 716,956
...
```

---

## 🔄 Next Steps

1. **Run the benchmark:**
   ```bash
   ./run_cloud_benchmark.sh
   ```

2. **Compare results:**
   - Local (16GB): vs Cloud (10GB)
   - Document memory efficiency differences

3. **Analyze:**
   - How does 10GB limit affect performance?
   - Which method (sync/async) works better under constraint?

---

**Ready to simulate cloud environment!** 🚀


