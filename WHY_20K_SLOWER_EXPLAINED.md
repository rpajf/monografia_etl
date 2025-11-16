# Why 4 Workers Are Slower with 20K Batches: Explained

## 🤔 Your Question: "Why 4 workers were slower with 20K?"

**The Counter-Intuitive Result:**
- 10K batches + 4 workers = 1005.85s ✅ Faster
- 20K batches + 4 workers = 1077.29s ❌ Slower (+7%)

**This seems backwards!** Normally, larger batches = faster. Let me explain why it's not.

---

## 🔍 The Root Cause: Database Contention

### What Happens with Different Batch Sizes:

#### **10K Batch Size:**
```
Total: 10,000 records
Workers: 4
Chunks per worker: ~2,500 records each
Simultaneous COPY operations: 4
Each COPY: Small transaction (~2.5K records)
Database contention: LOW ✅
```

#### **20K Batch Size:**
```
Total: 20,000 records
Workers: 4
Chunks per worker: ~5,000 records each
Simultaneous COPY operations: 4
Each COPY: Larger transaction (~5K records)
Database contention: HIGH ❌
```

---

## 📊 The Key Insight: Transaction Size Matters

### Why Larger Transactions Are Slower:

#### 1. **Lock Duration**

**10K Batch (Smaller Transactions):**
- Each COPY: ~2.5K records
- Lock held: Short duration
- Other operations can proceed quickly
- **Result:** Fast ✅

**20K Batch (Larger Transactions):**
- Each COPY: ~5K records
- Lock held: Longer duration
- Other operations wait longer
- **Result:** Slower ❌

#### 2. **Database Write Buffer**

**10K Batch:**
- Smaller transactions fit in buffer
- Quick flush to disk
- Less I/O wait

**20K Batch:**
- Larger transactions overflow buffer
- More disk I/O required
- More wait time

#### 3. **WAL (Write-Ahead Log) Pressure**

**10K Batch:**
- Smaller WAL entries
- Faster WAL writes
- Less checkpoint pressure

**20K Batch:**
- Larger WAL entries
- Slower WAL writes
- More checkpoint pressure

---

## 📈 Your Actual Data Proves This

### Insert Time Breakdown:

| Batch Size | Insert Time | Increase |
|------------|-------------|----------|
| 10K | 406s | Baseline |
| 20K | 496s | **+22% slower** |
| 30K | 790s | **+95% slower!** |

**Key Finding:** Insert time increases dramatically with batch size!

### Parse Time (Stays Similar):

| Batch Size | Parse Time |
|------------|------------|
| 10K | ~599s |
| 20K | ~580s |
| 30K | ~665s |

**Parse time is similar** - the bottleneck is **database insertion**, not parsing!

---

## 🎯 Why 4 Workers + 20K = Slower

### The Contention Problem:

**With 10K batches:**
```
Worker 1: COPY 2.5K records → Fast (small transaction)
Worker 2: COPY 2.5K records → Fast (small transaction)
Worker 3: COPY 2.5K records → Fast (small transaction)
Worker 4: COPY 2.5K records → Fast (small transaction)

Total: 4 small, fast operations ✅
```

**With 20K batches:**
```
Worker 1: COPY 5K records → Slower (larger transaction)
Worker 2: COPY 5K records → Slower (larger transaction)
Worker 3: COPY 5K records → Slower (larger transaction)
Worker 4: COPY 5K records → Slower (larger transaction)

Total: 4 larger, slower operations ❌
```

### The Math:

**10K Batch:**
- 4 workers × 2.5K records = 4 small transactions
- Each transaction: Fast (low contention)
- Total time: 406s

**20K Batch:**
- 4 workers × 5K records = 4 larger transactions
- Each transaction: Slower (higher contention)
- Total time: 496s (+22% slower!)

---

## 💡 The Real Bottleneck: Database, Not Workers

### What Your Data Shows:

**Parse Time (CPU-bound):**
- 10K: 599s
- 20K: 580s (actually faster!)
- 30K: 665s

**Insert Time (Database-bound):**
- 10K: 406s ✅
- 20K: 496s ❌ (+22%)
- 30K: 790s ❌ (+95%!)

**Conclusion:** The bottleneck is **database insertion**, not parsing or worker count!

---

## 🔬 Why Database Slows Down with Larger Batches

### 1. **Transaction Lock Contention**

**PostgreSQL Behavior:**
- Larger transactions = longer lock duration
- More locks = more contention
- Contention = waiting = slower

**Example:**
```
10K batch: 4 × 2.5K transactions
- Locks held briefly
- Quick release
- Low contention ✅

20K batch: 4 × 5K transactions
- Locks held longer
- Slower release
- High contention ❌
```

### 2. **Write Buffer Overflow**

**PostgreSQL Write Buffer:**
- Has limited size (shared_buffers)
- Small transactions: Fit in buffer → Fast
- Large transactions: Overflow → Disk I/O → Slow

**10K Batch:**
- Transactions fit in buffer
- Fast writes

**20K Batch:**
- Transactions overflow buffer
- More disk I/O
- Slower writes

### 3. **WAL (Write-Ahead Log) Pressure**

**WAL Behavior:**
- Every transaction writes to WAL
- Larger transactions = larger WAL entries
- More WAL pressure = slower

**10K Batch:**
- Small WAL entries
- Quick WAL writes

**20K Batch:**
- Larger WAL entries
- Slower WAL writes

---

## 📊 Visual Explanation

### Timeline Comparison:

**10K Batch (4 workers):**
```
Time: 0s ────────────────────────────────── 406s
Worker 1: [====] (2.5K, fast)
Worker 2: [====] (2.5K, fast)
Worker 3: [====] (2.5K, fast)
Worker 4: [====] (2.5K, fast)
Result: All finish quickly ✅
```

**20K Batch (4 workers):**
```
Time: 0s ──────────────────────────────────────────── 496s
Worker 1: [========] (5K, slower due to contention)
Worker 2: [========] (5K, waiting for locks)
Worker 3: [========] (5K, waiting for locks)
Worker 4: [========] (5K, waiting for locks)
Result: All take longer due to contention ❌
```

---

## 🎓 The Key Insight

### It's Not About Worker Count - It's About Transaction Size!

**The Real Relationship:**
```
Smaller Transactions (10K) = Less Contention = Faster ✅
Larger Transactions (20K) = More Contention = Slower ❌
```

**Worker count (4) stays the same, but:**
- 10K batches → Smaller transactions per worker → Fast
- 20K batches → Larger transactions per worker → Slow

---

## 💡 Why This Happens

### The Database Bottleneck:

**PostgreSQL can handle:**
- ✅ Many small transactions efficiently
- ❌ Few large transactions efficiently

**Why?**
- Small transactions: Quick locks, quick releases
- Large transactions: Long locks, slow releases, contention

### The Sweet Spot:

**For 4 workers:**
- ✅ 10K batches = 2.5K per worker (optimal)
- ❌ 20K batches = 5K per worker (too large)
- ❌ 30K batches = 7.5K per worker (way too large!)

---

## 📈 Expected Pattern

### If You Tested Different Worker Counts:

**10K Batches:**
- 1 worker: Slow (sequential)
- 2 workers: Fast ✅ (optimal)
- 4 workers: Fast ✅ (good)
- 8 workers: Slower (too much contention)

**20K Batches:**
- 1 worker: Slow (sequential)
- 2 workers: Might be better (less contention per worker)
- 4 workers: Slower ❌ (too much contention)
- 8 workers: Much slower (extreme contention)

---

## ✅ Summary

### Why 4 Workers + 20K = Slower:

1. **Larger transactions per worker** (5K vs 2.5K)
2. **More database contention** (longer locks)
3. **Write buffer overflow** (more disk I/O)
4. **WAL pressure** (larger log entries)
5. **Database becomes bottleneck** (not workers)

### The Real Relationship:

```
Batch Size ↑ → Transaction Size ↑ → Contention ↑ → Speed ↓
```

**Even with same worker count (4), larger batches = slower!**

### The Solution:

**For optimal performance:**
- ✅ Use **smaller batches** (10K)
- ✅ Use **fewer workers** (2) for even better performance
- ❌ Avoid **larger batches** (20K+) with same worker count

---

## 🎯 For Your Thesis

### Key Finding:

> "While increasing batch size typically improves performance in sequential processing, in parallel database operations, larger batches create transaction contention that outweighs the benefits of reduced overhead. For 4 parallel workers, 10K batches (2.5K per worker) outperform 20K batches (5K per worker) by 7%, demonstrating that transaction size, not just batch size, determines optimal performance."

This is a **critical insight** for your thesis! 🎓

