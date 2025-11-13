#!/usr/bin/env python3
"""
Quick Performance Test - Run a few configurations quickly
Useful for testing before running full benchmark
"""
import subprocess
import sys
from pathlib import Path

# Add parent directory to path to import benchmark
sys.path.insert(0, str(Path(__file__).parent))
from benchmark_performance import PerformanceBenchmark

# Quick test configurations (fewer runs, fewer configs)
QUICK_TEST_CONFIGS = [
    ("128m", 20, 0.5, "128MB"),
    ("512m", 100, 1.0, "512MB"),
    ("2g", 500, 2.0, "2GB"),
]


def quick_test():
    """Run a quick test with fewer configurations"""
    print("="*70)
    print("⚡ Quick Performance Test")
    print("="*70)
    print("\nThis will test 3 configurations with 2 runs each")
    print("(Much faster than full benchmark)\n")
    
    benchmark = PerformanceBenchmark()
    
    if not benchmark.build_docker_image():
        print("❌ Cannot proceed without Docker image")
        sys.exit(1)
    
    print("🧪 Running quick tests...\n")
    
    for memory_limit, num_files, cpu_limit, label in QUICK_TEST_CONFIGS:
        run_results = benchmark.run_docker_test(
            memory_limit, num_files, cpu_limit, label, num_runs=2
        )
        benchmark.results.extend(run_results)
    
    # Save and generate graphs
    benchmark.save_results()
    benchmark.generate_graphs()
    
    print("\n✅ Quick test complete!")
    print(f"📁 Results saved to: performance_results/")


if __name__ == "__main__":
    quick_test()

