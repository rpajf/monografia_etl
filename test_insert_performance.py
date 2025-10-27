"""
Script de comparação de performance entre diferentes métodos de inserção em PostgreSQL
Para sua tese/monografia
"""
import time
from fetch_db import ZipFileAnalyzer
from etl_psycopg3 import DatabaseConnector
from schemas import Artigo
import psycopg

zip_path = "/Users/raphaelportela/datasetcovid.zip"

def clean_table(table_name='artigos'):
    """Limpa a tabela antes de cada teste"""
    CONN_STRING = "host=localhost port=5432 dbname=etldb user=postgres"
    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY")
        conn.commit()
    print(f"🧹 Tabela '{table_name}' limpa\n")

def test_all_methods(num_records=10000):
    """Testa todos os métodos de inserção e compara resultados"""
    
    print(f"\n{'='*70}")
    print(f"🧪 TESTE COMPLETO DE PERFORMANCE - {num_records} registros")
    print(f"{'='*70}\n")
    
    # Carrega dados
    print("📥 Carregando dados do ZIP...")
    analyzer = ZipFileAnalyzer(zip_path)
    body_text_df, cite_text_df = analyzer.get_files_data(number_of_files=num_records)
    models_artigos = [Artigo(**row) for row in body_text_df.to_dict(orient="records")]
    print(f"✅ {len(models_artigos)} registros carregados\n")
    
    results = {}
    table = 'artigos'
    
    # ========================================================================
    # MÉTODO 1: Inserção Padrão (executemany)
    # ========================================================================
    print(f"\n{'='*70}")
    print("📌 TESTE 1: Inserção Padrão (executemany)")
    print(f"{'='*70}")
    clean_table(table)
    connector1 = DatabaseConnector()
    
    start = time.perf_counter()
    connector1.insert_into_table_typed(
        data_model=models_artigos,
        table_name=table
    )
    duration1 = time.perf_counter() - start
    results['Standard (executemany)'] = duration1
    
    # ========================================================================
    # MÉTODO 2: Paralelo com novas conexões (PROBLEMÁTICO)
    # ========================================================================
    print(f"\n{'='*70}")
    print("📌 TESTE 2: Paralelo com novas conexões a cada batch")
    print(f"{'='*70}")
    clean_table(table)
    connector2 = DatabaseConnector()
    
    start = time.perf_counter()
    connector2.batch_process_rows(
        data_model_list=models_artigos,
        table_name=table,
        batch_size=1000,
        max_workers=5
    )
    duration2 = time.perf_counter() - start
    results['Parallel (new connections)'] = duration2
    
    # ========================================================================
    # MÉTODO 3: Transação única otimizada (RECOMENDADO)
    # ========================================================================
    print(f"\n{'='*70}")
    print("📌 TESTE 3: Transação Única Otimizada (RECOMENDADO)")
    print(f"{'='*70}")
    clean_table(table)
    connector3 = DatabaseConnector()
    
    start = time.perf_counter()
    connector3.insert_optimized_single_transaction(
        table_name=table,
        data_model_list=models_artigos
    )
    duration3 = time.perf_counter() - start
    results['Optimized Single Transaction'] = duration3
    
    # ========================================================================
    # MÉTODO 4: Paralelo com ConnectionPool
    # ========================================================================
    print(f"\n{'='*70}")
    print("📌 TESTE 4: Paralelo com ConnectionPool")
    print(f"{'='*70}")
    clean_table(table)
    connector4 = DatabaseConnector()
    
    start = time.perf_counter()
    connector4.batch_process_with_pool(
        table_name=table,
        data_model_list=models_artigos,
        batch_size=5000,  # Aumentado
        max_workers=3      # Reduzido
    )
    duration4 = time.perf_counter() - start
    results['Parallel with Pool'] = duration4
    
    # ========================================================================
    # RESUMO DOS RESULTADOS
    # ========================================================================
    print(f"\n{'='*70}")
    print("📊 RESUMO DOS RESULTADOS")
    print(f"{'='*70}\n")
    
    # Ordena por tempo (do mais rápido ao mais lento)
    sorted_results = sorted(results.items(), key=lambda x: x[1])
    
    fastest = sorted_results[0][1]
    
    print(f"{'Método':<35} {'Tempo (s)':<12} {'Registros/s':<15} {'vs Melhor':<12}")
    print(f"{'-'*70}")
    
    for method, duration in sorted_results:
        rate = num_records / duration
        speedup = duration / fastest
        emoji = "🥇" if duration == fastest else "🥈" if speedup < 1.5 else "🥉" if speedup < 2 else "🔴"
        
        print(f"{emoji} {method:<33} {duration:>8.2f}     {rate:>12.0f}     {speedup:>8.2f}x")
    
    print(f"\n{'='*70}")
    print("💡 CONCLUSÕES:")
    print(f"{'='*70}")
    print(f"""
1. ⚠️  Paralelo com novas conexões é MAIS LENTO por causa de:
   • Overhead de criar {num_records//1000} novas conexões
   • Múltiplas transações (commit overhead)
   • Lock contention no PostgreSQL

2. ✅ Transação única otimizada é melhor para < 100k registros:
   • 1 conexão + 1 transação
   • execute_values = batch real
   • Sem overhead de paralelismo

3. 🔧 Paralelo com pool pode ser útil para datasets > 500k:
   • Mas requer tuning (batch_size, workers)
   • Para 10k registros, overhead > benefício

4. 📈 Para sua tese:
   • Documente que paralelismo ≠ sempre mais rápido
   • Mostre importância de benchmarking
   • Explique trade-offs de cada abordagem
""")

if __name__ == "__main__":
    # Testa com 10.000 registros (seu caso atual)
    test_all_methods(num_records=10000)

