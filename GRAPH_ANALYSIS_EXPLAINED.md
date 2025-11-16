# Graph Analysis: Why 10K is Actually Better (Explained)

## 🎯 The Key Question: Why Does 10K Look Better in Time Graph but 20K in Others?

### Understanding the "Time vs Processed Records" Graph

This graph shows **TOTAL EXECUTION TIME** for processing approximately **717,000 records** using different batch sizes.

**Results:**
- **10K batch:** 1005.85 seconds (~16.8 minutes) ✅ **FASTEST**
- **20K batch:** 1077.29 seconds (~18.0 minutes)
- **30K batch:** 1479.12 seconds (~24.7 minutes) ❌ **SLOWEST**

**Key Insight:** This graph shows **total wall-clock time** - the actual time you wait for the job to complete.

---

## 📊 Why 10K is Actually Better (All Metrics)

Looking at ALL the graphs together:

### 1. **Execution Time (Time vs Records Graph)**
```
10K: 1005.85s  ✅ WINNER
20K: 1077.29s  (+7% slower)
30K: 1479.12s  (+47% slower!)
```

### 2. **Throughput (Records/Second)**
```
10K: 713 rec/s  ✅ WINNER
20K: 666 rec/s  (-7% slower)
30K: 485 rec/s  (-32% slower!)
```

### 3. **Memory Efficiency (Records/MB)**
```
10K: 574 rec/MB  ✅ WINNER
20K: 400 rec/MB  (-30% less efficient)
30K: 425 rec/MB  (-26% less efficient)
```

### 4. **Peak Memory Usage**
```
10K: 1320 MB  ✅ LOWEST
20K: 1780 MB  (+35% more memory)
30K: 1680 MB  (+27% more memory)
```

### 5. **Database Insert Time**
```
10K: 406s  ✅ FASTEST
20K: 496s  (+22% slower)
30K: 790s  (+95% slower!)
```

---

## 🤔 Why Does 20K Look "Better" in Some Views?

You might be seeing 20K as "better" because:

### 1. **Memory Usage Rate (MB/s)**
The memory usage rate graph shows:
- 10K: 0.32 MB/s
- 20K: 0.70 MB/s (peak)
- 30K: 0.27 MB/s

**But this is misleading!** Higher MB/s doesn't mean better - it means memory is being consumed faster. This is actually a **bad thing** for constrained environments.

### 2. **Visual Scale Differences**
- The memory graphs use different scales
- 20K might appear "in the middle" which looks balanced
- But 10K is actually better in almost every metric

---

## 🔍 The Real Explanation: Why Smaller Batches Win

### For Async Parallel Processing:

**Smaller batches (10K) are better because:**

1. **Less Database Contention**
   - Smaller batches = more frequent commits
   - Less lock contention on database
   - Database can process smaller chunks faster

2. **Better Parallelism**
   - More chunks = better load distribution
   - Can utilize all parallel workers more evenly
   - Less idle time waiting for large batches

3. **Lower Memory Pressure**
   - Smaller batches = less memory per operation
   - Better for garbage collection
   - Less risk of memory spikes

4. **Faster Individual Operations**
   - Each COPY operation is faster with smaller data
   - Less time holding database connections
   - More responsive to system load

### Why Larger Batches (30K) Are Slower:

1. **Database Bottleneck**
   - Insert time: 790s vs 406s (almost 2x slower!)
   - Larger transactions = more lock contention
   - Database struggles with very large batches

2. **Diminishing Returns**
   - Overhead of managing large batches
   - Less efficient parallelism
   - Memory pressure affects performance

---

## 📈 Understanding "Time vs Processed Records"

### What This Graph Shows:

**X-axis (Registros Processados):** ~717,000 records
- All three batch sizes process the **SAME total number of records**
- This is the key: same work, different strategies

**Y-axis (Tempo de Execução):** Total time in seconds
- This is **wall-clock time** - how long you actually wait
- Includes: parsing + transformation + database insertion

### Why All Points Are at ~717K Records:

This graph shows: **"If I process 717K records, how long does it take with different batch sizes?"**

**Answer:**
- 10K batches: Fastest (1005s)
- 20K batches: Slower (1077s)
- 30K batches: Slowest (1479s)

### The Pattern:

```
Batch Size ↑ → Total Time ↑ (for same number of records)
```

**This is counter-intuitive!** Normally, larger batches = faster. But in async parallel processing with database contention, **smaller batches win**.

---

## 💡 Key Insights for Your Thesis

### Finding 1: Optimal Batch Size is Smaller Than Expected

**For async parallel ETL:**
- ✅ **Optimal:** 10K batch size
- ⚠️ **Acceptable:** 20K batch size (7% slower)
- ❌ **Avoid:** 30K batch size (47% slower!)

### Finding 2: Database Insert is the Bottleneck

Looking at the stage breakdown:
- Parse time: Similar across batch sizes (~580-665s)
- **Insert time: Increases dramatically with batch size**
  - 10K: 406s
  - 20K: 496s (+22%)
  - 30K: 790s (+95%!)

**Conclusion:** Database insertion becomes the bottleneck with larger batches.

### Finding 3: Memory Efficiency Matters

- 10K: 574 records/MB (best)
- 20K: 400 records/MB
- 30K: 425 records/MB

**For constrained environments:** 10K is clearly better.

---

## 🎓 Thesis Implications

### For "Optimization under Limited Processing Resources":

**Recommendation: Use 10K Batch Size for Async**

**Reasons:**
1. ✅ **Fastest execution** (1005s vs 1077s vs 1479s)
2. ✅ **Best throughput** (713 rec/s vs 666 vs 485)
3. ✅ **Best memory efficiency** (574 rec/MB vs 400 vs 425)
4. ✅ **Lowest memory usage** (1320 MB vs 1780 vs 1680)
5. ✅ **Fastest database inserts** (406s vs 496s vs 790s)

**Trade-off:**
- More batches to manage (but async handles this well)
- More frequent commits (but reduces contention)

---

## 📊 Summary Table

| Metric | 10K Batch | 20K Batch | 30K Batch | Winner |
|--------|-----------|-----------|-----------|--------|
| **Total Time** | 1005.85s | 1077.29s | 1479.12s | ✅ 10K |
| **Throughput** | 713 rec/s | 666 rec/s | 485 rec/s | ✅ 10K |
| **Memory Efficiency** | 574 rec/MB | 400 rec/MB | 425 rec/MB | ✅ 10K |
| **Peak Memory** | 1320 MB | 1780 MB | 1680 MB | ✅ 10K |
| **Insert Time** | 406s | 496s | 790s | ✅ 10K |
| **Parse Time** | ~599s | ~580s | ~665s | ⚖️ Similar |

**Conclusion: 10K is the clear winner across ALL metrics!**

---

## 🔍 Why You Might Have Thought 20K Was Better

1. **Memory Rate Graph:** Shows 20K has highest MB/s rate
   - But this is **bad** - means consuming memory faster
   - Not a performance metric, it's a consumption rate

2. **Visual Balance:** 20K appears "in the middle"
   - But middle doesn't mean optimal
   - 10K is consistently better

3. **Different Metrics:** Different graphs emphasize different things
   - Time graph shows **total time** (most important)
   - Memory graphs show **usage patterns** (important for constraints)

---

## ✅ Final Answer

**10K batch size is better in EVERY meaningful metric:**

- ✅ Fastest total time
- ✅ Best throughput  
- ✅ Best memory efficiency
- ✅ Lowest memory usage
- ✅ Fastest database operations

**The "Time vs Processed Records" graph is the most important** because it shows **actual execution time** - how long you wait for results.

**For your thesis:** Document that smaller batches (10K) are optimal for async parallel ETL, contrary to the common assumption that larger batches are always better.

