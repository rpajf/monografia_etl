# Docker Setup Guide - Two Approaches

## 📋 Overview

You have **two ways** to run your ETL project:

1. **Approach 1:** PostgreSQL in Docker + Python on Host (✅ Recommended for development)
2. **Approach 2:** Both PostgreSQL and Python in Docker (production-like)

---

## 🎯 Approach 1: Python on Host (Recommended)

### Why this is better for your thesis:
- ✅ Fast iteration (no Docker rebuilds)
- ✅ Easy debugging
- ✅ Direct access to your dataset
- ✅ Use your IDE normally

### Setup:

```bash
# 1. Start only PostgreSQL
docker-compose up -d postgres

# 2. Install Python dependencies locally
pip install -r requirements.txt

# 3. Run your ETL code
python etl_psycopg3.py

# 4. Connection settings in your Python code:
# DB_HOST = "localhost"  (not "postgres")
# DB_PORT = 5432
# DB_NAME = "etldb"
# DB_USER = "postgres"
```

### Daily workflow:
```bash
# Start database
docker-compose up -d postgres

# Edit and run Python code
python etl_psycopg3.py
python compare_psycopg_versions.py

# Stop database
docker-compose stop
```

---

## 🐳 Approach 2: Everything in Docker

### Why use this:
- ✅ Consistent environment
- ✅ Easy deployment
- ✅ Good for final demo

### Setup:

```bash
# 1. Uncomment the etl_app service in docker-compose.yml
# (Lines starting with # etl_app:)

# 2. Build and start all services
docker-compose up --build

# Or run services separately:
docker-compose up -d postgres  # Start database
docker-compose up etl_app      # Run ETL (see logs)
```

### Important changes in Python code:

```python
# When running in Docker, use SERVICE NAME not "localhost"
DB_HOST = "postgres"  # ← Service name from docker-compose.yml
DB_PORT = 5432
DB_NAME = "etldb"
DB_USER = "postgres"
```

---

## 🔧 Key Differences

| Setting | On Host | In Docker |
|---------|---------|-----------|
| DB_HOST | `localhost` | `postgres` (service name) |
| Dataset Path | `/Users/raphaelportela/datasetcovid.zip` | `/data/datasetcovid.zip` |
| Code changes | Instant | Need rebuild |
| Debugging | Easy | Harder |

---

## 📝 Common Commands

### Approach 1 (Python on Host):
```bash
# Start database
docker-compose up -d postgres

# Check status
docker-compose ps

# View PostgreSQL logs
docker-compose logs -f postgres

# Connect to PostgreSQL
docker exec -it etl_postgres psql -U postgres -d etldb

# Stop
docker-compose stop
```

### Approach 2 (Everything in Docker):
```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View ETL logs
docker-compose logs -f etl_app

# Run one-off ETL command
docker-compose run --rm etl_app python compare_psycopg_versions.py

# Rebuild after code changes
docker-compose up --build etl_app

# Stop everything
docker-compose down
```

---

## 🎓 For Your Thesis Defense

### During Development: **Use Approach 1**
- Fast iteration
- Easy to test different strategies
- Can show live coding

### For Final Demo: **Use Approach 2**
- Professional setup
- Reproducible environment
- Easy to share

---

## 💡 Pro Tip: Environment Variables

Create a `.env` file to switch between approaches:

```bash
# .env file
DB_HOST=localhost  # Change to "postgres" for Docker approach
DB_PORT=5432
DB_NAME=etldb
DB_USER=postgres
DB_PASSWORD=
DATASET_PATH=/Users/raphaelportela/datasetcovid.zip
```

Then in your Python code:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
# ... etc
```

---

## ❓ Which Should You Use?

### Start with **Approach 1** because:
1. You're still developing and testing
2. Need to iterate quickly
3. Want to benchmark different approaches
4. Easier debugging

### Switch to **Approach 2** when:
1. Ready for final demo
2. Want to show reproducible deployment
3. Preparing for production

---

## 🚀 Quick Start (Recommended):

```bash
# 1. Start PostgreSQL only
docker-compose up -d postgres

# 2. Install dependencies locally
pip install -r requirements.txt

# 3. Test connection
docker exec -it etl_postgres psql -U postgres -d etldb

# 4. Run your ETL
python etl_psycopg3.py

# Done! Start coding your thesis project 🎓
```



