================================================================================
BENCHMARK COMPARISON: SYNC (COPY) vs ASYNC (PARALLEL)
================================================================================

📊 KEY METRICS TO COMPARE:

1. PERFORMANCE METRICS
--------------------------------------------------------------------------------
   Throughput (records/second):
   • Sync (COPY): Single transaction, optimized bulk insert
   • Async (Parallel): Multiple concurrent connections
   • Winner: Depends on batch size and I/O vs CPU bound

   Total Execution Time:
   • Sync: Sequential processing
   • Async: Parallel processing (should be faster)
   • Winner: Async typically wins for large datasets

   Latency per Record:
   • Sync: Lower overhead per record
   • Async: May have async overhead
   • Winner: Sync for small batches, Async for large

2. RESOURCE USAGE
--------------------------------------------------------------------------------
   Peak Memory:
   • Sync: Lower (single connection, single transaction)
   • Async: Higher (multiple connections, parallel buffers)
   • Winner: Sync (better for constrained environments)

   Memory Efficiency (Records/MB):
   • Sync: Better - less overhead
   • Async: Worse - more connections
   • Winner: Sync

3. STAGE BREAKDOWN
--------------------------------------------------------------------------------
   Parse Time:
   • Should be similar (same parsing logic)
   • Key insight: Compare insert_time ratios

   Insert Time:
   • Sync: COPY method - very efficient
   • Async: Parallel inserts - may be faster
   • Key comparison: This is where optimization matters

4. SCALABILITY ANALYSIS
--------------------------------------------------------------------------------
   Batch Size Impact:
   • Sync: COPY benefits significantly from larger batches
   • Async: May have optimal batch size (not too small, not too large)
   • Analysis: Compare how performance scales

================================================================================
RECOMMENDATIONS FOR THESIS
================================================================================

For Limited Processing Resources:

✅ Use SYNC (COPY) when:
   • Memory is constrained (< 512MB)
   • Batch sizes are large (> 20,000 records)
   • Single-threaded performance is acceptable
   • Cost optimization is priority

✅ Use ASYNC (PARALLEL) when:
   • CPU cores are available (4+)
   • I/O is the bottleneck
   • Memory is available (> 1GB)
   • Speed is priority over cost

💡 Key Insight:
   The trade-off is: Memory vs Speed
   Sync = Lower memory, potentially slower
   Async = Higher memory, potentially faster


## Graph Availability

Sync graphs available: {'dashboard': True, 'memory_perf': True, 'time_vs_rows': True, 'memory_timeline': True}
Async graphs available: {'dashboard': True, 'memory_perf': True, 'time_vs_rows': True, 'memory_timeline': True}
