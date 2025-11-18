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
    
    # Synchronous benchmark (COPY method - single transaction)
    # print("\n" + "="*70)
    # print("🔵 BENCHMARK SÍNCRONO - Método COPY (Transação Única)")
    # print("="*70)
    # benchmark_sync = BenchmarkExecutor(
    #     files_to_process=total_files,
    #     offset=0,
    #     pipeline=analyzer.execute_batch_insert
    # )
    # benchmark_sync.processamento()
    
    # Uncomment below to run async benchmark for comparison
    # print("\n" + "="*70)
    # print("🟢 BENCHMARK ASSÍNCRONO - Método Paralelo")
    # print("="*70)
    # benchmark_async = BenchmarkExecutor(
    #     files_to_process=total_files,
    #     offset=0,
    #     pipeline=analyzer.execute_batch_parallel,
    #     max_tasks=4
    # )
    # asyncio.run(benchmark_async.processamento_async())
    # test = [ArtigoStaging(**row) for row in body_text_df.to_dict(orient="records")]

    # print('test', articles_df.to_dict(orient="records"))
    # while True:
    #     batch_count += 1
    #     print(f"\n{'─'*70}")
    #     print(f"BATCH {batch_count} - Offset: {offset:,}")
    #     print(f"{'─'*70}")
    #     start_batch = time.perf_counter()
    #     body_text_df, cite_text_df = analyzer.get_files_data_as_dataframe(
    #         number_of_files=batch_size, offset=offset
    #     )
    #     if len(body_text_df) == 0:
    #         print("✅ Nenhum dado retornado - processamento concluído!")
    #         break
    #     models_artigos = [
    #         ArtigoStaging(**row) for row in body_text_df.to_dict(orient="records")
    #     ]
    #     connector.insert_optimized_single_transaction(
    #         table_name="artigos_staging", data_model_list=models_artigos
    #     )

    #     # Calcula métricas do batch
    #     batch_time = time.perf_counter() - start_batch
    #     batch_rate = len(models_artigos) / batch_time if batch_time > 0 else 0
    #     jsons_neste_batch = min(batch_size, len(body_text_df))

    #     # Atualiza contadores ← IMPORTANTE!
    #     total_processado += len(models_artigos)
    #     total_jsons_processados += jsons_neste_batch
    #     offset += batch_size

    #     # Mostra progresso do batch
    #     print(f"⏱️  Tempo do batch: {batch_time:.2f}s")
    #     print(f"📊 Registros inseridos neste batch: {len(models_artigos):,}")
    #     print(f"⚡ Taxa do batch: {batch_rate:.0f} registros/s")
    #     print(f"📁 JSONs processados neste batch: ~{jsons_neste_batch:,}")
    #     print(
    #         f"✅ Total acumulado: {total_processado:,} registros de ~{total_jsons_processados:,} JSONs"
    #     )
    # # Métricas finais
    # end_total = time.perf_counter()
    # total_time = end_total - start_total
    # avg_rate = total_processado / total_time if total_time > 0 else 0

    # print(f"\n{'='*70}")
    # print("🎉 PROCESSAMENTO CONCLUÍDO - ARTIGOS STAGING")
    # print(f"{'='*70}")
    # print(f"📊 Total de batches processados: {batch_count}")
    # print(f"📁 Total de JSONs processados: ~{total_jsons_processados:,}")
    # print(f"📈 Total de registros inseridos: {total_processado:,}")
    # if total_jsons_processados > 0:
    #     print(
    #         f"📝 Média de registros por JSON: {total_processado/total_jsons_processados:.1f}"
    #     )
    # print(f"⏱️  Tempo total: {total_time:.2f}s ({total_time/60:.2f} minutos)")
    # print(f"⚡ Taxa média geral: {avg_rate:.0f} registros/segundo")
    # print(f"{'='*70}\n")
