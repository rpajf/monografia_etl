"""
Docker-ready version of fetch_db.py
Reads configuration from environment variables
"""
import time
import os
import sys
import zipfile
import json
from itertools import islice

# Configuration from environment variables
ZIP_PATH = os.getenv('ZIP_PATH', '/data/datasetcovid.zip')
NUM_FILES = int(os.getenv('NUM_FILES', '10'))
VERBOSE = os.getenv('VERBOSE', 'false').lower() == 'true'

print("=" * 70)
print("🐳 ETL Docker Runner - Resource Constrained Environment")
print("=" * 70)
print(f"📦 ZIP Path: {ZIP_PATH}")
print(f"📊 Files to process: {NUM_FILES}")
print(f"💬 Verbose mode: {VERBOSE}")
print()


class ResourceConstrainedAnalyzer:
    """Memory-efficient JSON file analyzer for constrained environments"""
    
    def __init__(self, zip_path):
        self.zip_path = zip_path
        
    def analyze_json_files_lightweight(self, num_files=10, verbose=False):
        """
        Memory-efficient analysis - doesn't store full data
        
        Args:
            num_files (int): Number of files to process
            verbose (bool): Print detailed info
        """
        if not os.path.exists(self.zip_path):
            print(f"❌ Error: ZIP file not found at {self.zip_path}")
            sys.exit(1)
            
        print(f"🔍 Starting analysis of {num_files} files...")
        print(f"💾 Process memory limit: {self._get_memory_limit()}")
        print()
        
        results_summary = []
        total_size = 0
        total_processing_time = 0
        errors = 0
        
        try:
            with zipfile.ZipFile(self.zip_path, "r") as z:
                json_files = [f for f in z.namelist() if f.endswith('.json')]
                
                if not json_files:
                    print("⚠️  No JSON files found!")
                    return []
                
                print(f"📊 Total JSON files available: {len(json_files):,}")
                files_to_process = min(num_files, len(json_files))
                print(f"🎯 Processing: {files_to_process} files")
                print("-" * 70)
                
                for i, file_name in enumerate(json_files[:files_to_process], 1):
                    try:
                        # Measure processing time
                        start_time = time.time()
                        
                        # Read and parse (then discard to save memory)
                        content = z.read(file_name)
                        data = json.loads(content)
                        
                        processing_time = time.time() - start_time
                        
                        # Extract minimal info
                        file_info = {
                            'index': i,
                            'file_name': file_name,
                            'size': len(content),
                            'keys': list(data.keys()) if isinstance(data, dict) else [],
                            'processing_time': processing_time
                        }
                        
                        total_size += len(content)
                        total_processing_time += processing_time
                        
                        # Print progress
                        if verbose:
                            print(f"📄 [{i}/{files_to_process}] {file_name[:50]}")
                            print(f"   Size: {len(content):,} bytes | Time: {processing_time:.4f}s")
                            print(f"   Keys: {file_info['keys']}")
                        elif i % 10 == 0:
                            # Progress indicator
                            print(f"   ✓ Processed {i}/{files_to_process} files... "
                                  f"(Avg: {total_processing_time/i:.4f}s/file)")
                        
                        # Store minimal summary (not full data!)
                        results_summary.append({
                            'file': file_name.split('/')[-1][:30],  # Short name
                            'size_kb': len(content) / 1024,
                            'time': processing_time
                        })
                        
                        # Clear data to free memory immediately
                        del content
                        del data
                        
                    except json.JSONDecodeError as e:
                        errors += 1
                        if verbose:
                            print(f"   ⚠️  JSON Error in {file_name}: {str(e)[:50]}")
                    except Exception as e:
                        errors += 1
                        if verbose:
                            print(f"   ⚠️  Error in {file_name}: {str(e)[:50]}")
                    
                    # Check if we're running out of memory
                    if i % 50 == 0:
                        self._check_memory()
        
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            sys.exit(1)
        
        # Print summary
        print()
        print("=" * 70)
        print("📊 PROCESSING SUMMARY")
        print("=" * 70)
        print(f"✅ Successfully processed: {len(results_summary)} files")
        print(f"❌ Errors encountered: {errors}")
        print(f"📦 Total data processed: {total_size / (1024**2):.2f} MB")
        print(f"⏱️  Total processing time: {total_processing_time:.2f}s")
        print(f"⏱️  Average time per file: {total_processing_time / len(results_summary):.4f}s")
        print(f"📈 Throughput: {len(results_summary) / total_processing_time:.2f} files/sec")
        
        # Show size distribution
        if results_summary:
            sizes = [r['size_kb'] for r in results_summary]
            print()
            print("📊 File Size Statistics:")
            print(f"   Smallest: {min(sizes):.2f} KB")
            print(f"   Largest: {max(sizes):.2f} KB")
            print(f"   Average: {sum(sizes)/len(sizes):.2f} KB")
        
        print()
        print("✨ Analysis complete!")
        
        return results_summary
    
    def _get_memory_limit(self):
        """Try to detect container memory limit"""
        try:
            with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
                limit_bytes = int(f.read().strip())
                # Check if it's a real limit (not max value)
                if limit_bytes < 9223372036854771712:  # Less than max int64
                    return f"{limit_bytes / (1024**2):.0f} MB"
        except:
            pass
        return "Unlimited"
    
    def _check_memory(self):
        """Check current memory usage"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024**2)
            print(f"   💾 Current memory usage: {mem_mb:.1f} MB")
        except ImportError:
            pass  # psutil not available
    
   


def main():
    """Main execution"""
    print("🚀 Starting ETL process...")
    print()
    
    # Check if we should save to CSV
    SAVE_CSV = os.getenv('SAVE_CSV', 'false').lower() == 'true'
    
    try:
        analyzer = ResourceConstrainedAnalyzer(ZIP_PATH)
        
        if SAVE_CSV:
            # Save to CSV
            analyzer.save_json_to_csv(
                num_files=NUM_FILES,
                output_file='/app/output/json_data.csv'
            )
        else:
            # Just analyze (default)
            results = analyzer.analyze_json_files_lightweight(
                num_files=NUM_FILES,
                verbose=VERBOSE
            )
        
        print()
        print("=" * 70)
        print("🎓 For your thesis:")
        print("   • This demonstrates ETL in resource-constrained environments")
        print("   • Memory-efficient processing (streaming, no caching)")
        print("   • Suitable for serverless/edge computing scenarios")
        print("=" * 70)
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except MemoryError:
        print("\n❌ OUT OF MEMORY!")
        print("   The container ran out of memory.")
        print("   Try: Reduce NUM_FILES or increase memory limit")
        sys.exit(137)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

