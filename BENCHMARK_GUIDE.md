# 📊 Performance Benchmark Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install matplotlib seaborn
# Or install all requirements:
pip install -r requirements.txt
```

### 2. Run Benchmark

```bash
python benchmark_performance.py
```

The script will:
- ✅ Build Docker image (if needed)
- ✅ Run ETL with different memory limits (64MB, 128MB, 256MB, 512MB, 1GB, 2GB, 3GB)
- ✅ Measure runtime for each configuration (3 runs each by default)
- ✅ Generate performance graphs automatically

### 3. View Results

Results are saved in `performance_results/` directory:
- `benchmark_results_TIMESTAMP.json` - Raw data (JSON)
- `benchmark_results_TIMESTAMP.csv` - Data for analysis (CSV)
- `runtime_vs_memory_TIMESTAMP.png` - Runtime vs Memory graph
- `throughput_vs_memory_TIMESTAMP.png` - Throughput vs Memory graph
- `runtime_distribution_TIMESTAMP.png` - Runtime distribution (box plot)
- `performance_summary_TIMESTAMP.png` - Comprehensive summary (4 subplots)

---

## Customization

### Change Test Configurations

Edit `TEST_CONFIGS` in `benchmark_performance.py`:

```python
TEST_CONFIGS = [
    ("64m", 10, 0.5, "64MB"),      # (memory, num_files, cpu, label)
    ("128m", 20, 0.5, "128MB"),
    # Add your own...
]
```

### Change Number of Runs

When running the script, you'll be prompted:
```
Enter number of runs per configuration (default: 3):
```

Or modify the code:
```python
benchmark.run_all_tests(num_runs=5)  # 5 runs per configuration
```

### Test Specific Configuration Only

Modify the script to test only one configuration:

```python
# In main() function, replace run_all_tests() with:
benchmark.run_docker_test("128m", 20, 0.5, "128MB", num_runs=3)
benchmark.save_results()
benchmark.generate_graphs()
```

---

## Understanding the Graphs

### 1. Runtime vs Memory
- **X-axis**: Memory limit (MB)
- **Y-axis**: Runtime (seconds)
- **Shows**: How runtime changes with available memory
- **Expected**: Runtime decreases as memory increases (up to a point)

### 2. Throughput vs Memory
- **X-axis**: Memory limit (MB)
- **Y-axis**: Throughput (files/second)
- **Shows**: Processing speed vs memory
- **Expected**: Throughput increases with memory (diminishing returns)

### 3. Runtime Distribution
- **Box plot** showing min, Q1, median, Q3, max
- **Shows**: Variability across multiple runs
- **Useful**: Identify consistency of performance

### 4. Performance Summary
- **4 subplots**: Runtime, Throughput, Time per File, Memory Efficiency
- **Comprehensive view** of all metrics

---

## Troubleshooting

### Docker Image Not Found
```bash
# Build manually:
docker build -f Dockerfile.etl -t etl-app .
```

### Out of Memory Errors
- Some configurations may fail (especially 64MB)
- This is expected and shows resource limits
- Failed runs are still recorded in results

### Timeout Errors
- Default timeout is 10 minutes per run
- Increase timeout in `run_docker_test()` if needed:
  ```python
  timeout=1200  # 20 minutes
  ```

### Missing Dependencies
```bash
pip install matplotlib seaborn pandas
```

---

## Example Output

```
======================================================================
📊 ETL Performance Benchmark Tool
======================================================================

📦 Checking Docker image...
✅ Docker image 'etl-app' already exists

🚀 Starting performance benchmark
📊 Test configurations: 7
🔄 Runs per configuration: 3
📁 Results will be saved to: performance_results

======================================================================
🧪 Testing: 64MB (Memory: 64m, Files: 10, CPU: 0.5)
======================================================================

  Run 1/3...
    ✅ Success - Runtime: 12.34s
  Run 2/3...
    ✅ Success - Runtime: 11.89s
  Run 3/3...
    ✅ Success - Runtime: 12.01s

...

📈 Generating graphs...
  ✅ Runtime vs Memory graph saved
  ✅ Throughput vs Memory graph saved
  ✅ Runtime Distribution graph saved
  ✅ Performance Summary graph saved

✅ Benchmark complete!
📊 Results saved to: performance_results
```

---

## For Your Thesis

### Key Metrics to Report:

1. **Runtime vs Memory**: Shows the impact of resource constraints
2. **Throughput**: Demonstrates processing efficiency
3. **Optimal Configuration**: Identify sweet spot (best performance/cost ratio)
4. **Diminishing Returns**: Show where more memory doesn't help much

### Statistical Analysis:

The script calculates:
- **Mean** runtime across runs
- **Standard deviation** (variability)
- **Min/Max** values

Use these for:
- Confidence intervals
- Statistical significance testing
- Performance predictions

---

## Advanced Usage

### Analyze Existing Results

```python
import pandas as pd
import json

# Load results
with open('performance_results/benchmark_results_20250101_120000.json') as f:
    results = json.load(f)

df = pd.DataFrame(results)

# Filter successful runs
df_success = df[df['success'] == True]

# Calculate statistics
stats = df_success.groupby('label').agg({
    'runtime_seconds': ['mean', 'std', 'min', 'max'],
    'throughput_files_per_sec': 'mean'
})

print(stats)
```

### Compare Different Batch Sizes

Modify `TEST_CONFIGS` to test different batch sizes with same memory:

```python
TEST_CONFIGS = [
    ("128m", 10, 0.5, "128MB-10files"),
    ("128m", 20, 0.5, "128MB-20files"),
    ("128m", 50, 0.5, "128MB-50files"),
]
```

This shows the impact of batch size on performance.

---

**Good luck with your thesis! 🎓**


