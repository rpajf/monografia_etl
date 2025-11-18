import asyncio
import zipfile
import os

from benchmark import BenchmarkExecutor
from etl_psycopg3 import DatabaseConnector
from fetch_db import ZipFileAnalyzer

# Get dataset path from environment variable or use default
zip_path = os.getenv("DATASET_PATH", "/Users/raphaelportela/datasetcovid.zip")


def get_total_files():
    with zipfile.ZipFile(zip_path, "r") as z:
        all_files = z.namelist()
        json_files = [f for f in all_files if f.endswith(".json")]
        return len(json_files)


if __name__ == "__main__":
    connector = DatabaseConnector()
    analyzer = ZipFileAnalyzer(zip_path)
    total_files = get_total_files()
    print(f"📊 Total de arquivos JSON encontrados: {total_files:,}")
    
    # Asynchronous benchmark (parallel method)
    print("\n" + "="*70)
    print("🟢 BENCHMARK ASSÍNCRONO - Método Paralelo")
    print("="*70)
    
    # Use async_docker directory when running in Docker
    async_output_dir = os.getenv("ASYNC_OUTPUT_DIR", "async_docker")
    
    benchmark_async = BenchmarkExecutor(
        files_to_process=total_files,
        offset=0,
        pipeline=analyzer.execute_batch_parallel,
        max_tasks=4,
        async_result_dir=async_output_dir
    )
    asyncio.run(benchmark_async.processamento_async())

