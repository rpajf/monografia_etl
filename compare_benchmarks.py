"""
Benchmark Comparison Analysis Tool
Compares sync (COPY) vs async (parallel) ETL approaches
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class BenchmarkComparator:
    """Compare sync and async benchmark results"""
    
    def __init__(self, sync_dir: str, async_dir: str):
        self.sync_dir = Path(sync_dir)
        self.async_dir = Path(async_dir)
        
    def analyze_graphs(self) -> Dict:
        """Analyze available graphs and provide comparison framework"""
        
        sync_graphs = {
            "dashboard": self.sync_dir / "sync_benchmark_dashboard.png",
            "memory_perf": self.sync_dir / "sync_benchmark_memory_and_performance.png",
            "time_vs_rows": self.sync_dir / "sync_benchmark_time_vs_rows.png",
            "memory_timeline": self.sync_dir / "sync_benchmark_memory_timeline.png",
        }
        
        async_graphs = {
            "dashboard": self.async_dir / "async_benchmark_dashboard.png",
            "memory_perf": self.async_dir / "async_benchmark_memory_and_performance.png",
            "time_vs_rows": self.async_dir / "async_benchmark_time_vs_rows.png",
            "memory_timeline": self.async_dir / "async_benchmark_memory_timeline.png",
        }
        
        # Check which graphs exist
        sync_available = {k: v.exists() for k, v in sync_graphs.items()}
        async_available = {k: v.exists() for k, v in async_graphs.items()}
        
        return {
            "sync_graphs": sync_available,
            "async_graphs": async_available,
            "comparison_framework": self._get_comparison_framework()
        }
    
    def _get_comparison_framework(self) -> Dict:
        """Framework for comparing benchmarks"""
        return {
            "performance_metrics": {
                "throughput": {
                    "description": "Records per second",
                    "sync_expected": "COPY method - typically higher for large batches",
                    "async_expected": "Parallel inserts - may have overhead but better for I/O bound",
                    "better_when": "Higher is better"
                },
                "latency": {
                    "description": "Time per record (ms)",
                    "sync_expected": "Lower overhead, single transaction",
                    "async_expected": "May have async overhead but parallel execution",
                    "better_when": "Lower is better"
                },
                "total_time": {
                    "description": "Total execution time",
                    "sync_expected": "Single-threaded, predictable",
                    "async_expected": "Parallel execution should be faster",
                    "better_when": "Lower is better"
                }
            },
            "resource_metrics": {
                "peak_memory": {
                    "description": "Maximum memory usage (MB)",
                    "sync_expected": "Lower - single transaction, less overhead",
                    "async_expected": "Higher - multiple connections, parallel processing",
                    "better_when": "Lower is better (for constrained environments)",
                    "context": "For 16GB system, both should be reasonable"
                },
                "memory_efficiency": {
                    "description": "Records per MB",
                    "sync_expected": "Better - less overhead per record",
                    "async_expected": "Worse - more connections/overhead",
                    "better_when": "Higher is better"
                },
                "memory_rate": {
                    "description": "Memory growth rate (MB/s)",
                    "sync_expected": "Lower - steady single transaction",
                    "async_expected": "Higher - parallel operations",
                    "better_when": "Lower is better (more stable)"
                }
            },
            "stage_breakdown": {
                "parse_time": {
                    "description": "Time spent parsing JSON files",
                    "sync_vs_async": "Should be similar (same parsing logic)",
                    "note": "Not affected by insert method"
                },
                "insert_time": {
                    "description": "Time spent inserting to database",
                    "sync_expected": "COPY method - very fast, single transaction",
                    "async_expected": "Parallel inserts - may be faster for I/O bound",
                    "key_comparison": "This is where the difference matters"
                }
            },
            "scalability": {
                "batch_size_impact": {
                    "description": "How performance changes with batch size",
                    "sync_expected": "COPY benefits from larger batches",
                    "async_expected": "Parallel may have optimal batch size",
                    "analysis": "Compare slopes of performance curves"
                }
            }
        }
    
    def generate_comparison_report(self) -> str:
        """Generate a structured comparison report"""
        framework = self._get_comparison_framework()
        
        report = []
        report.append("=" * 80)
        report.append("BENCHMARK COMPARISON: SYNC (COPY) vs ASYNC (PARALLEL)")
        report.append("=" * 80)
        report.append("")
        
        report.append("📊 KEY METRICS TO COMPARE:")
        report.append("")
        
        report.append("1. PERFORMANCE METRICS")
        report.append("-" * 80)
        report.append("   Throughput (records/second):")
        report.append("   • Sync (COPY): Single transaction, optimized bulk insert")
        report.append("   • Async (Parallel): Multiple concurrent connections")
        report.append("   • Winner: Depends on batch size and I/O vs CPU bound")
        report.append("")
        
        report.append("   Total Execution Time:")
        report.append("   • Sync: Sequential processing")
        report.append("   • Async: Parallel processing (should be faster)")
        report.append("   • Winner: Async typically wins for large datasets")
        report.append("")
        
        report.append("   Latency per Record:")
        report.append("   • Sync: Lower overhead per record")
        report.append("   • Async: May have async overhead")
        report.append("   • Winner: Sync for small batches, Async for large")
        report.append("")
        
        report.append("2. RESOURCE USAGE")
        report.append("-" * 80)
        report.append("   Peak Memory:")
        report.append("   • Sync: Lower (single connection, single transaction)")
        report.append("   • Async: Higher (multiple connections, parallel buffers)")
        report.append("   • Winner: Sync (better for constrained environments)")
        report.append("")
        
        report.append("   Memory Efficiency (Records/MB):")
        report.append("   • Sync: Better - less overhead")
        report.append("   • Async: Worse - more connections")
        report.append("   • Winner: Sync")
        report.append("")
        
        report.append("3. STAGE BREAKDOWN")
        report.append("-" * 80)
        report.append("   Parse Time:")
        report.append("   • Should be similar (same parsing logic)")
        report.append("   • Key insight: Compare insert_time ratios")
        report.append("")
        
        report.append("   Insert Time:")
        report.append("   • Sync: COPY method - very efficient")
        report.append("   • Async: Parallel inserts - may be faster")
        report.append("   • Key comparison: This is where optimization matters")
        report.append("")
        
        report.append("4. SCALABILITY ANALYSIS")
        report.append("-" * 80)
        report.append("   Batch Size Impact:")
        report.append("   • Sync: COPY benefits significantly from larger batches")
        report.append("   • Async: May have optimal batch size (not too small, not too large)")
        report.append("   • Analysis: Compare how performance scales")
        report.append("")
        
        report.append("=" * 80)
        report.append("RECOMMENDATIONS FOR THESIS")
        report.append("=" * 80)
        report.append("")
        report.append("For Limited Processing Resources:")
        report.append("")
        report.append("✅ Use SYNC (COPY) when:")
        report.append("   • Memory is constrained (< 512MB)")
        report.append("   • Batch sizes are large (> 20,000 records)")
        report.append("   • Single-threaded performance is acceptable")
        report.append("   • Cost optimization is priority")
        report.append("")
        report.append("✅ Use ASYNC (PARALLEL) when:")
        report.append("   • CPU cores are available (4+)")
        report.append("   • I/O is the bottleneck")
        report.append("   • Memory is available (> 1GB)")
        report.append("   • Speed is priority over cost")
        report.append("")
        report.append("💡 Key Insight:")
        report.append("   The trade-off is: Memory vs Speed")
        report.append("   Sync = Lower memory, potentially slower")
        report.append("   Async = Higher memory, potentially faster")
        report.append("")
        
        return "\n".join(report)


def main():
    sync_dir = "sync_result"
    async_dir = "last_async_memory"
    
    comparator = BenchmarkComparator(sync_dir, async_dir)
    
    # Analyze available graphs
    analysis = comparator.analyze_graphs()
    
    # Generate report
    report = comparator.generate_comparison_report()
    
    print(report)
    
    # Save report
    with open("BENCHMARK_COMPARISON_ANALYSIS.md", "w") as f:
        f.write(report)
        f.write("\n\n")
        f.write("## Graph Availability\n\n")
        f.write(f"Sync graphs available: {analysis['sync_graphs']}\n")
        f.write(f"Async graphs available: {analysis['async_graphs']}\n")
    
    print("\n📄 Report saved to BENCHMARK_COMPARISON_ANALYSIS.md")


if __name__ == "__main__":
    main()

