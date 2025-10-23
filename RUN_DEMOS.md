# How to Run the ETL Parallelism Demos 🚀

## Prerequisites
```bash
# Make sure PostgreSQL is running
docker-compose up -d

# Activate your virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install psycopg pandas
```

---

## Demo 1: Quick Parallel Comparison (5 seconds) ⚡

This is the fastest demo to understand the concept.

```bash
python quick_parallel_demo.py
```

**What it does:**
- Loads 50 JSON files from your COVID-19 ZIP
- Processes them sequentially
- Processes them in parallel
- Shows you the speedup!

**Expected output:**
```
🧪 QUICK PARALLELISM DEMO
Files to process: 50
CPU cores: 8

⏱️  SEQUENTIAL PROCESSING
✅ Processed 50 files
⏱️  Time: 2.45 seconds

🚀 PARALLEL PROCESSING (7 workers)
✅ Processed 50 files
⏱️  Time: 0.89 seconds

📊 RESULTS
Speedup: 2.75x faster! 🚀
```

---

## Demo 2: Full ETL with Database (30 seconds) 🔥

This shows real-world ETL with PostgreSQL.

```bash
python etl_parallel_demo.py
```

**What it does:**
- Creates a `covid_papers` table
- Loads 100 files from ZIP
- Processes and inserts into PostgreSQL
- Compares sequential vs parallel
- Shows detailed metrics

**Expected output:**
```
📊 STRATEGY 1: SEQUENTIAL PROCESSING
⏱️  Total time: 15.32s
📈 Rate: 6.5 files/sec

🚀 STRATEGY 2: PARALLEL PROCESSING (7 workers)
⏱️  Total time: 5.47s
📈 Rate: 18.3 files/sec

🏆 WINNER: Parallel (7 workers)
Speedup: 2.80x faster than baseline
```

---

## Customizing the Demos

### Process more files:
```python
# In quick_parallel_demo.py
NUM_FILES = 200  # Change from 50 to 200

# In etl_parallel_demo.py
NUM_FILES_TO_PROCESS = 500  # Change from 100 to 500
```

### Adjust batch size:
```python
# In etl_parallel_demo.py
BATCH_SIZE = 5000  # Change from 1000 to 5000
```

### Test with different worker counts:
```python
# In etl_parallel_demo.py, modify the etl_parallel call:
result_par = etl_parallel(files_data, num_workers=4)  # Try 2, 4, 8, etc.
```

---

## Understanding the Results

### Key Metrics

1. **Duration**: Total time to complete the task
2. **Rate**: Files processed per second
3. **Speedup**: How much faster parallel is (e.g., 2.5x)
4. **Workers**: Number of parallel processes

### What affects performance?

| Factor | Impact | Recommendation |
|--------|--------|----------------|
| CPU cores | More cores = faster | Use `cpu_count() - 1` |
| File size | Larger files = more gain | Good for your JSON files |
| I/O speed | Slow disk limits gains | SSD recommended |
| Batch size | Larger batches = fewer DB round trips | 1000-5000 is optimal |

### Expected Speedups

| CPU Cores | Expected Speedup | Your System (8 cores) |
|-----------|------------------|------------------------|
| 2 cores   | 1.5-1.8x        | Not applicable         |
| 4 cores   | 2.5-3.2x        | If you limit workers   |
| 8 cores   | 3.5-5.0x        | **Your current setup** |
| 16 cores  | 5.0-8.0x        | Upgrade if needed      |

---

## Troubleshooting

### Error: "File not found"
```bash
# Update the ZIP_PATH in the scripts:
ZIP_PATH = "/path/to/your/datasetcovid.zip"
```

### Error: "Database connection failed"
```bash
# Start PostgreSQL
docker-compose up -d

# Check if running
docker-compose ps
```

### Error: "Out of memory"
```python
# Reduce the number of files
NUM_FILES = 50  # Start small
```

### Performance not improving?
- Check if you're actually CPU-bound (use `htop`)
- Your dataset might be too small
- Try with more files (1000+)
- Check if disk I/O is the bottleneck

---

## Next Steps

1. ✅ Run `quick_parallel_demo.py` to see basic parallelism
2. ✅ Run `etl_parallel_demo.py` to see full ETL comparison
3. ✅ Read `ETL_PARALLELISM_GUIDE.md` for deep dive
4. ✅ Experiment with different settings
5. ✅ Apply to your actual production ETL

### For Your Thesis

These demos provide concrete evidence for:
- ✅ Performance optimization techniques
- ✅ Quantifiable improvements (2-5x speedup)
- ✅ Real-world ETL scenarios
- ✅ Best practices in data engineering

Good luck! 🎓


