"""
ETL Performance Comparison: Sequential vs Parallel Processing
Demonstrates the impact of parallelism on ETL performance

This script:
1. Reads COVID-19 research papers from ZIP file
2. Processes and loads data into PostgreSQL
3. Compares sequential vs parallel execution
4. Provides detailed performance metrics
"""
import psycopg
import zipfile
import json
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count
from typing import List, Tuple, Dict
import os

# Database connection
CONN_STRING = "host=localhost port=5432 dbname=etldb user=postgres"
ZIP_PATH = "/Users/raphaelportela/datasetcovid.zip"

# Configuration
BATCH_SIZE = 1000  # Records per batch insert
NUM_FILES_TO_PROCESS = 100  # Limit for demo purposes


def create_papers_table():
    """Create the papers table for storing COVID-19 research data"""
    print("🔨 Setting up database table...\n")
    
    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS covid_papers CASCADE;
                
                CREATE TABLE covid_papers (
                    paper_id VARCHAR(100) PRIMARY KEY,
                    title TEXT,
                    abstract TEXT,
                    authors TEXT,
                    publish_time VARCHAR(50),
                    source VARCHAR(100),
                    file_name VARCHAR(255),
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create indexes for better query performance
                CREATE INDEX IF NOT EXISTS idx_papers_title ON covid_papers(title);
                CREATE INDEX IF NOT EXISTS idx_papers_publish_time ON covid_papers(publish_time);
            """)
        conn.commit()
    print("✅ Table created successfully\n")


def extract_paper_data(json_data: dict, file_name: str) -> dict:
    """Extract relevant fields from JSON paper data"""
    try:
        # Extract authors
        authors = []
        if 'metadata' in json_data and 'authors' in json_data['metadata']:
            authors = [
                f"{a.get('first', '')} {a.get('last', '')}".strip()
                for a in json_data['metadata']['authors']
            ]
        
        # Extract abstract
        abstract = ""
        if 'abstract' in json_data and json_data['abstract']:
            abstract_parts = [item.get('text', '') for item in json_data['abstract']]
            abstract = ' '.join(abstract_parts)
        
        return {
            'paper_id': json_data.get('paper_id', f'unknown_{file_name}'),
            'title': json_data.get('metadata', {}).get('title', 'No Title'),
            'abstract': abstract[:5000],  # Limit size
            'authors': ', '.join(authors[:10]),  # Limit authors
            'publish_time': json_data.get('metadata', {}).get('publish_time', ''),
            'source': json_data.get('source', 'unknown'),
            'file_name': file_name
        }
    except Exception as e:
        print(f"⚠️  Error extracting data from {file_name}: {e}")
        return None


def read_files_from_zip(num_files: int = NUM_FILES_TO_PROCESS) -> List[Tuple[str, bytes]]:
    """Read JSON files from ZIP archive"""
    print(f"📦 Reading {num_files} files from ZIP archive...\n")
    
    files_data = []
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        # Get list of JSON files
        json_files = [f for f in z.namelist() if f.endswith('.json')][:num_files]
        
        for file_name in json_files:
            try:
                content = z.read(file_name)
                files_data.append((file_name, content))
            except Exception as e:
                print(f"⚠️  Error reading {file_name}: {e}")
    
    print(f"✅ Read {len(files_data)} files\n")
    return files_data


def process_single_file(file_data: Tuple[str, bytes]) -> dict:
    """Process a single JSON file (used in parallel processing)"""
    file_name, content = file_data
    try:
        json_data = json.loads(content)
        return extract_paper_data(json_data, file_name)
    except Exception as e:
        return None


def bulk_insert_papers(papers: List[dict], conn_string: str):
    """Bulk insert papers using executemany for better performance"""
    if not papers:
        return
    
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            # Filter out None values
            valid_papers = [p for p in papers if p is not None]
            
            if not valid_papers:
                return
            
            # Use executemany for batch insert
            cur.executemany(
                """
                INSERT INTO covid_papers 
                (paper_id, title, abstract, authors, publish_time, source, file_name)
                VALUES (%(paper_id)s, %(title)s, %(abstract)s, %(authors)s, 
                        %(publish_time)s, %(source)s, %(file_name)s)
                ON CONFLICT (paper_id) DO NOTHING
                """,
                valid_papers
            )
        conn.commit()


# ============================================================================
# STRATEGY 1: SEQUENTIAL PROCESSING (BASELINE)
# ============================================================================

def etl_sequential(files_data: List[Tuple[str, bytes]]) -> Dict:
    """Sequential ETL: Process files one by one"""
    print("=" * 70)
    print("📊 STRATEGY 1: SEQUENTIAL PROCESSING (BASELINE)")
    print("=" * 70)
    print(f"Processing {len(files_data)} files sequentially...\n")
    
    start_time = time.time()
    
    # Process files
    papers = []
    for i, file_data in enumerate(files_data, 1):
        paper = process_single_file(file_data)
        if paper:
            papers.append(paper)
        
        # Insert in batches
        if len(papers) >= BATCH_SIZE:
            bulk_insert_papers(papers, CONN_STRING)
            papers = []
        
        if i % 20 == 0:
            print(f"   Processed {i}/{len(files_data)} files...")
    
    # Insert remaining papers
    if papers:
        bulk_insert_papers(papers, CONN_STRING)
    
    duration = time.time() - start_time
    
    print(f"\n✅ Sequential processing complete!")
    print(f"   ⏱️  Total time: {duration:.2f}s")
    print(f"   📈 Rate: {len(files_data)/duration:.1f} files/sec")
    print(f"   🔄 Processing: {duration:.2f}s")
    
    return {
        'strategy': 'Sequential',
        'duration': duration,
        'files_processed': len(files_data),
        'rate': len(files_data)/duration
    }


# ============================================================================
# STRATEGY 2: PARALLEL PROCESSING (OPTIMIZED)
# ============================================================================

def etl_parallel(files_data: List[Tuple[str, bytes]], num_workers: int = None) -> Dict:
    """Parallel ETL: Process files using multiprocessing"""
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)  # Leave one core free
    
    print("\n" + "=" * 70)
    print(f"🚀 STRATEGY 2: PARALLEL PROCESSING ({num_workers} workers)")
    print("=" * 70)
    print(f"Processing {len(files_data)} files in parallel...\n")
    
    start_time = time.time()
    
    # Process files in parallel using Pool
    with Pool(processes=num_workers) as pool:
        papers = pool.map(process_single_file, files_data)
    
    processing_time = time.time() - start_time
    
    # Insert into database (still sequential for data integrity)
    insert_start = time.time()
    
    # Batch insert
    valid_papers = [p for p in papers if p is not None]
    for i in range(0, len(valid_papers), BATCH_SIZE):
        batch = valid_papers[i:i + BATCH_SIZE]
        bulk_insert_papers(batch, CONN_STRING)
        print(f"   Inserted batch {i//BATCH_SIZE + 1}/{(len(valid_papers)//BATCH_SIZE) + 1}")
    
    insert_time = time.time() - insert_start
    total_duration = time.time() - start_time
    
    print(f"\n✅ Parallel processing complete!")
    print(f"   ⏱️  Total time: {total_duration:.2f}s")
    print(f"   📈 Rate: {len(files_data)/total_duration:.1f} files/sec")
    print(f"   🔄 Processing: {processing_time:.2f}s")
    print(f"   💾 Database insert: {insert_time:.2f}s")
    
    return {
        'strategy': f'Parallel ({num_workers} workers)',
        'duration': total_duration,
        'processing_time': processing_time,
        'insert_time': insert_time,
        'files_processed': len(files_data),
        'rate': len(files_data)/total_duration,
        'workers': num_workers
    }


# ============================================================================
# COMPARISON AND ANALYSIS
# ============================================================================

def print_comparison(results: List[Dict]):
    """Print detailed comparison of all strategies"""
    print("\n" + "=" * 70)
    print("📊 PERFORMANCE COMPARISON SUMMARY")
    print("=" * 70)
    
    # Find baseline
    baseline = next((r for r in results if 'Sequential' in r['strategy']), results[0])
    
    print(f"\n{'Strategy':<30} {'Time (s)':<12} {'Rate (files/s)':<15} {'Speedup':<10}")
    print("-" * 70)
    
    for result in results:
        speedup = baseline['duration'] / result['duration']
        speedup_str = f"{speedup:.2f}x" if speedup != 1.0 else "baseline"
        
        print(f"{result['strategy']:<30} {result['duration']:<12.2f} "
              f"{result['rate']:<15.1f} {speedup_str:<10}")
    
    # Recommendations
    best = min(results, key=lambda x: x['duration'])
    print(f"\n🏆 WINNER: {best['strategy']}")
    print(f"   Speedup: {baseline['duration']/best['duration']:.2f}x faster than baseline")
    
    print("\n💡 KEY INSIGHTS:")
    print("   • Parallel processing significantly reduces file parsing time")
    print("   • CPU-bound operations (JSON parsing) benefit most from parallelism")
    print("   • Database insertion remains sequential for data integrity")
    print(f"   • Optimal workers: {cpu_count() - 1} (leaving 1 core free)")
    
    # System info
    print(f"\n🖥️  SYSTEM INFO:")
    print(f"   CPU Cores: {cpu_count()}")
    print(f"   Files Processed: {results[0]['files_processed']}")
    print(f"   Batch Size: {BATCH_SIZE}")


def verify_data():
    """Verify that data was inserted correctly"""
    print("\n" + "=" * 70)
    print("🔍 VERIFYING DATA")
    print("=" * 70)
    
    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cur:
            # Count total papers
            cur.execute("SELECT COUNT(*) FROM covid_papers")
            count = cur.fetchone()[0]
            print(f"\n✅ Total papers in database: {count}")
            
            # Sample data
            cur.execute("""
                SELECT paper_id, title, LEFT(abstract, 100) as abstract_preview
                FROM covid_papers 
                LIMIT 3
            """)
            
            print("\n📄 Sample papers:")
            for row in cur.fetchall():
                print(f"\n   Paper ID: {row[0]}")
                print(f"   Title: {row[1][:80]}...")
                print(f"   Abstract: {row[2]}...")


def main():
    """Main execution function"""
    print("=" * 70)
    print("🧪 ETL PERFORMANCE COMPARISON: SEQUENTIAL vs PARALLEL")
    print("=" * 70)
    print(f"\nDataset: COVID-19 Research Papers")
    print(f"Source: {os.path.basename(ZIP_PATH)}")
    print(f"Files to process: {NUM_FILES_TO_PROCESS}")
    print(f"CPU Cores available: {cpu_count()}")
    print()
    
    try:
        # Setup
        create_papers_table()
        
        # Load data from ZIP
        files_data = read_files_from_zip(NUM_FILES_TO_PROCESS)
        
        if not files_data:
            print("❌ No files found in ZIP archive!")
            return
        
        results = []
        
        # Test 1: Sequential
        result_seq = etl_sequential(files_data)
        results.append(result_seq)
        
        # Clear table for next test
        with psycopg.connect(CONN_STRING) as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE covid_papers")
            conn.commit()
        
        # Test 2: Parallel
        result_par = etl_parallel(files_data)
        results.append(result_par)
        
        # Print comparison
        print_comparison(results)
        
        # Verify data
        verify_data()
        
        print("\n" + "=" * 70)
        print("✨ DEMO COMPLETE!")
        print("=" * 70)
        print("\n📝 Next steps:")
        print("   1. Adjust NUM_FILES_TO_PROCESS to test with more files")
        print("   2. Experiment with different BATCH_SIZE values")
        print("   3. Try different numbers of parallel workers")
        print("   4. Monitor CPU and memory usage during processing")
        
    except FileNotFoundError:
        print(f"❌ ZIP file not found: {ZIP_PATH}")
        print("   Please update ZIP_PATH variable with correct path")
    except psycopg.OperationalError as e:
        print(f"❌ Database connection error: {e}")
        print("\n💡 Make sure:")
        print("   1. Docker container is running: docker-compose up -d")
        print("   2. PostgreSQL is accessible on localhost:5432")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


