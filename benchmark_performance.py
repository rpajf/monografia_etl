#!/usr/bin/env python3
"""
ETL Performance Benchmark Script
Measures runtime performance with different Docker memory limits
and generates performance graphs for thesis analysis.
"""
import subprocess
import json
import re
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd

# Configuration
DOCKER_IMAGE = "etl-app"
ZIP_PATH = "/Users/raphaelportela/datasetcovid.zip"
SCRIPT_PATH = Path(__file__).parent / "fetch_db_docker.py"
RESULTS_DIR = Path(__file__).parent / "performance_results"
RESULTS_DIR.mkdir(exist_ok=True)

# Test configurations: (memory_limit, num_files, cpu_limit, label)
TEST_CONFIGS = [
    ("64m", 10, 0.5, "64MB"),
    ("128m", 20, 0.5, "128MB"),
    ("256m", 50, 0.75, "256MB"),
    ("512m", 100, 1.0, "512MB"),
    ("1g", 200, 1.5, "1GB"),
    ("2g", 500, 2.0, "2GB"),
    ("3g", 1000, 2.5, "3GB"),
]

# Set style for better-looking graphs
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class PerformanceBenchmark:
    """Benchmark ETL performance under different resource constraints"""
    
    def __init__(self):
        self.results: List[Dict] = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def build_docker_image(self) -> bool:
        """Build the Docker image if it doesn't exist"""
        print("📦 Checking Docker image...")
        try:
            # Check if image exists
            result = subprocess.run(
                ["docker", "images", "-q", DOCKER_IMAGE],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                print(f"✅ Docker image '{DOCKER_IMAGE}' already exists")
                return True
            
            # Build image
            print(f"🔨 Building Docker image '{DOCKER_IMAGE}'...")
            result = subprocess.run(
                ["docker", "build", "-f", "Dockerfile.etl", "-t", DOCKER_IMAGE, "."],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Docker image built successfully")
                return True
            else:
                print(f"❌ Failed to build Docker image:\n{result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error building Docker image: {e}")
            return False
    
    def run_docker_test(
        self, 
        memory_limit: str, 
        num_files: int, 
        cpu_limit: float,
        label: str,
        num_runs: int = 3
    ) -> List[Dict]:
        """Run Docker container with specified constraints and measure performance"""
        print(f"\n{'='*70}")
        print(f"🧪 Testing: {label} (Memory: {memory_limit}, Files: {num_files}, CPU: {cpu_limit})")
        print(f"{'='*70}")
        
        run_results = []
        
        for run_num in range(1, num_runs + 1):
            print(f"\n  Run {run_num}/{num_runs}...")
            
            # Prepare Docker command
            cmd = [
                "docker", "run", "--rm",
                f"--memory={memory_limit}",
                f"--memory-swap={memory_limit}",
                f"--cpus={cpu_limit}",
                "-v", f"{os.path.abspath(SCRIPT_PATH)}:/app/fetch_db.py:ro",
                "-v", f"{ZIP_PATH}:/data/datasetcovid.zip:ro",
                "-e", f"NUM_FILES={num_files}",
                "-e", "VERBOSE=false",
                DOCKER_IMAGE,
                "python", "fetch_db.py"
            ]
            
            # Measure runtime
            start_time = time.perf_counter()
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                runtime = time.perf_counter() - start_time
                exit_code = result.returncode
                
                # Parse output for metrics
                metrics = self._parse_output(result.stdout, result.stderr)
                
                if exit_code == 0:
                    metrics.update({
                        "memory_limit": memory_limit,
                        "memory_mb": self._parse_memory_mb(memory_limit),
                        "num_files": num_files,
                        "cpu_limit": cpu_limit,
                        "label": label,
                        "runtime_seconds": runtime,
                        "run_number": run_num,
                        "success": True,
                        "exit_code": exit_code
                    })
                    print(f"    ✅ Success - Runtime: {runtime:.2f}s")
                else:
                    metrics.update({
                        "memory_limit": memory_limit,
                        "memory_mb": self._parse_memory_mb(memory_limit),
                        "num_files": num_files,
                        "cpu_limit": cpu_limit,
                        "label": label,
                        "runtime_seconds": runtime,
                        "run_number": run_num,
                        "success": False,
                        "exit_code": exit_code,
                        "error": result.stderr[:200] if result.stderr else "Unknown error"
                    })
                    print(f"    ❌ Failed - Exit code: {exit_code}")
                
                run_results.append(metrics)
                
            except subprocess.TimeoutExpired:
                print(f"    ⏱️  Timeout after 10 minutes")
                run_results.append({
                    "memory_limit": memory_limit,
                    "memory_mb": self._parse_memory_mb(memory_limit),
                    "num_files": num_files,
                    "cpu_limit": cpu_limit,
                    "label": label,
                    "runtime_seconds": 600.0,
                    "run_number": run_num,
                    "success": False,
                    "exit_code": -1,
                    "error": "Timeout"
                })
            except Exception as e:
                print(f"    ❌ Error: {e}")
                run_results.append({
                    "memory_limit": memory_limit,
                    "memory_mb": self._parse_memory_mb(memory_limit),
                    "num_files": num_files,
                    "cpu_limit": cpu_limit,
                    "label": label,
                    "runtime_seconds": 0,
                    "run_number": run_num,
                    "success": False,
                    "exit_code": -1,
                    "error": str(e)
                })
        
        return run_results
    
    def _parse_memory_mb(self, memory_str: str) -> float:
        """Convert memory string (e.g., '128m', '1g') to MB"""
        memory_str = memory_str.lower().strip()
        if memory_str.endswith('g'):
            return float(memory_str[:-1]) * 1024
        elif memory_str.endswith('m'):
            return float(memory_str[:-1])
        else:
            return float(memory_str)
    
    def _parse_output(self, stdout: str, stderr: str) -> Dict:
        """Parse Docker output to extract performance metrics"""
        metrics = {
            "files_processed": 0,
            "total_processing_time": 0.0,
            "avg_time_per_file": 0.0,
            "throughput_files_per_sec": 0.0,
            "total_data_mb": 0.0,
            "errors": 0
        }
        
        # Extract files processed
        match = re.search(r"Successfully processed:\s*(\d+)", stdout)
        if match:
            metrics["files_processed"] = int(match.group(1))
        
        # Extract total processing time
        match = re.search(r"Total processing time:\s*([\d.]+)s", stdout)
        if match:
            metrics["total_processing_time"] = float(match.group(1))
        
        # Extract average time per file
        match = re.search(r"Average time per file:\s*([\d.]+)s", stdout)
        if match:
            metrics["avg_time_per_file"] = float(match.group(1))
        
        # Extract throughput
        match = re.search(r"Throughput:\s*([\d.]+)\s*files/sec", stdout)
        if match:
            metrics["throughput_files_per_sec"] = float(match.group(1))
        
        # Extract total data processed
        match = re.search(r"Total data processed:\s*([\d.]+)\s*MB", stdout)
        if match:
            metrics["total_data_mb"] = float(match.group(1))
        
        # Extract errors
        match = re.search(r"Errors encountered:\s*(\d+)", stdout)
        if match:
            metrics["errors"] = int(match.group(1))
        
        return metrics
    
    def run_all_tests(self, num_runs: int = 3):
        """Run all test configurations"""
        if not self.build_docker_image():
            print("❌ Cannot proceed without Docker image")
            sys.exit(1)
        
        print(f"\n🚀 Starting performance benchmark")
        print(f"📊 Test configurations: {len(TEST_CONFIGS)}")
        print(f"🔄 Runs per configuration: {num_runs}")
        print(f"📁 Results will be saved to: {RESULTS_DIR}")
        
        for memory_limit, num_files, cpu_limit, label in TEST_CONFIGS:
            run_results = self.run_docker_test(
                memory_limit, num_files, cpu_limit, label, num_runs
            )
            self.results.extend(run_results)
            
            # Small delay between tests
            time.sleep(2)
        
        # Save results
        self.save_results()
        
        # Generate graphs
        self.generate_graphs()
        
        print(f"\n✅ Benchmark complete!")
        print(f"📊 Results saved to: {RESULTS_DIR}")
    
    def save_results(self):
        """Save results to JSON and CSV"""
        # Save as JSON
        json_path = RESULTS_DIR / f"benchmark_results_{self.timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {json_path}")
        
        # Save as CSV
        df = pd.DataFrame(self.results)
        csv_path = RESULTS_DIR / f"benchmark_results_{self.timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"💾 CSV saved to: {csv_path}")
    
    def generate_graphs(self):
        """Generate performance graphs"""
        if not self.results:
            print("⚠️  No results to graph")
            return
        
        df = pd.DataFrame(self.results)
        
        # Filter successful runs only
        df_success = df[df['success'] == True].copy()
        
        if df_success.empty:
            print("⚠️  No successful runs to graph")
            return
        
        # Calculate averages per configuration
        df_avg = df_success.groupby('label').agg({
            'runtime_seconds': ['mean', 'std', 'min', 'max'],
            'throughput_files_per_sec': ['mean', 'std'],
            'avg_time_per_file': ['mean', 'std'],
            'memory_mb': 'first',
            'num_files': 'first'
        }).reset_index()
        
        df_avg.columns = ['label', 'runtime_mean', 'runtime_std', 'runtime_min', 'runtime_max',
                          'throughput_mean', 'throughput_std', 'avg_time_mean', 'avg_time_std',
                          'memory_mb', 'num_files']
        
        # Sort by memory
        df_avg = df_avg.sort_values('memory_mb')
        
        print(f"\n📈 Generating graphs...")
        
        # Graph 1: Runtime vs Memory
        self._plot_runtime_vs_memory(df_avg)
        
        # Graph 2: Throughput vs Memory
        self._plot_throughput_vs_memory(df_avg)
        
        # Graph 3: Runtime Distribution (box plot)
        self._plot_runtime_distribution(df_success)
        
        # Graph 4: Performance Summary (multiple metrics)
        self._plot_performance_summary(df_avg)
        
        print(f"✅ Graphs saved to: {RESULTS_DIR}")
    
    def _plot_runtime_vs_memory(self, df_avg: pd.DataFrame):
        """Plot runtime vs memory limit"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = df_avg['memory_mb']
        y_mean = df_avg['runtime_mean']
        y_std = df_avg['runtime_std']
        
        ax.errorbar(x, y_mean, yerr=y_std, marker='o', linestyle='-', 
                   linewidth=2, markersize=8, capsize=5, capthick=2,
                   color='#2E86AB', label='Mean Runtime')
        
        ax.set_xlabel('Memory Limit (MB)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Runtime (seconds)', fontsize=12, fontweight='bold')
        ax.set_title('ETL Runtime vs Memory Limit\n(Error bars show standard deviation)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add labels for each point
        for _, row in df_avg.iterrows():
            ax.annotate(f"{row['label']}\n({row['num_files']} files)",
                       xy=(row['memory_mb'], row['runtime_mean']),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / f"runtime_vs_memory_{self.timestamp}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Runtime vs Memory graph saved")
    
    def _plot_throughput_vs_memory(self, df_avg: pd.DataFrame):
        """Plot throughput vs memory limit"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = df_avg['memory_mb']
        y_mean = df_avg['throughput_mean']
        y_std = df_avg['throughput_std']
        
        ax.errorbar(x, y_mean, yerr=y_std, marker='s', linestyle='-',
                   linewidth=2, markersize=8, capsize=5, capthick=2,
                   color='#A23B72', label='Mean Throughput')
        
        ax.set_xlabel('Memory Limit (MB)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Throughput (files/second)', fontsize=12, fontweight='bold')
        ax.set_title('ETL Throughput vs Memory Limit\n(Higher is better)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / f"throughput_vs_memory_{self.timestamp}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Throughput vs Memory graph saved")
    
    def _plot_runtime_distribution(self, df_success: pd.DataFrame):
        """Plot runtime distribution as box plot"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Prepare data for box plot
        data_for_box = []
        labels = []
        positions = []
        
        for i, label in enumerate(df_success['label'].unique()):
            subset = df_success[df_success['label'] == label]
            data_for_box.append(subset['runtime_seconds'].values)
            labels.append(label)
            positions.append(i + 1)
        
        bp = ax.boxplot(data_for_box, labels=labels, patch_artist=True)
        
        # Color the boxes
        colors = plt.cm.viridis([i / len(labels) for i in range(len(labels))])
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_xlabel('Memory Configuration', fontsize=12, fontweight='bold')
        ax.set_ylabel('Runtime (seconds)', fontsize=12, fontweight='bold')
        ax.set_title('Runtime Distribution Across Multiple Runs\n(Box plot shows min, Q1, median, Q3, max)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / f"runtime_distribution_{self.timestamp}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Runtime Distribution graph saved")
    
    def _plot_performance_summary(self, df_avg: pd.DataFrame):
        """Plot comprehensive performance summary"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        x = df_avg['memory_mb']
        
        # Subplot 1: Runtime
        ax1.errorbar(x, df_avg['runtime_mean'], yerr=df_avg['runtime_std'],
                    marker='o', linestyle='-', linewidth=2, markersize=6, capsize=4)
        ax1.set_xlabel('Memory (MB)', fontweight='bold')
        ax1.set_ylabel('Runtime (s)', fontweight='bold')
        ax1.set_title('Runtime vs Memory', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Subplot 2: Throughput
        ax2.errorbar(x, df_avg['throughput_mean'], yerr=df_avg['throughput_std'],
                    marker='s', linestyle='-', linewidth=2, markersize=6, capsize=4, color='green')
        ax2.set_xlabel('Memory (MB)', fontweight='bold')
        ax2.set_ylabel('Throughput (files/s)', fontweight='bold')
        ax2.set_title('Throughput vs Memory', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Subplot 3: Average time per file
        ax3.errorbar(x, df_avg['avg_time_mean'], yerr=df_avg['avg_time_std'],
                    marker='^', linestyle='-', linewidth=2, markersize=6, capsize=4, color='orange')
        ax3.set_xlabel('Memory (MB)', fontweight='bold')
        ax3.set_ylabel('Time per File (s)', fontweight='bold')
        ax3.set_title('Time per File vs Memory', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Subplot 4: Efficiency (files processed per MB of memory)
        efficiency = df_avg['num_files'] / df_avg['memory_mb']
        ax4.bar(range(len(df_avg)), efficiency, color='purple', alpha=0.7)
        ax4.set_xticks(range(len(df_avg)))
        ax4.set_xticklabels(df_avg['label'], rotation=45, ha='right')
        ax4.set_ylabel('Files per MB', fontweight='bold')
        ax4.set_title('Memory Efficiency\n(Files processed per MB)', fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('ETL Performance Summary - Resource Constrained Environment', 
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / f"performance_summary_{self.timestamp}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Performance Summary graph saved")


def main():
    """Main execution"""
    print("="*70)
    print("📊 ETL Performance Benchmark Tool")
    print("="*70)
    print("\nThis script will:")
    print("  1. Build Docker image (if needed)")
    print("  2. Run ETL with different memory limits")
    print("  3. Measure runtime performance")
    print("  4. Generate performance graphs")
    print()
    
    benchmark = PerformanceBenchmark()
    
    # Ask user for number of runs
    try:
        num_runs = int(input("Enter number of runs per configuration (default: 3): ") or "3")
    except ValueError:
        num_runs = 3
    
    # Run all tests
    benchmark.run_all_tests(num_runs=num_runs)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    df = pd.DataFrame(benchmark.results)
    df_success = df[df['success'] == True]
    
    if not df_success.empty:
        df_summary = df_success.groupby('label').agg({
            'runtime_seconds': ['mean', 'std'],
            'throughput_files_per_sec': 'mean',
            'memory_mb': 'first'
        }).round(2)
        
        print("\nPerformance by Configuration:")
        print(df_summary.to_string())
    else:
        print("⚠️  No successful runs to summarize")
    
    print(f"\n📁 All results saved to: {RESULTS_DIR}")
    print("="*70)


if __name__ == "__main__":
    main()

