import time
import matplotlib.pyplot as plt
import seaborn as sns

from etl_psycopg3 import DatabaseConnector


class BenchmarkExecutor:
    def __init__(self, files_to_process, offset, pipeline):
        self.files_to_process = files_to_process
        self.offset = offset
        self.zip_path = "/Users/raphaelportela/datasetcovid.zip"
        self.pipeline = pipeline
        # self.batch_size = batch_size 

    def processamento(self):
        sns.set(style="whitegrid")
        batch_sizes = [10000, 20000, 30000]
        tempos = []
        taxas = []
        connector = DatabaseConnector()

        for batch_size in batch_sizes:
            connector.truncate_table(table_name="artigos_stg")
            print(f"\n🚀 Rodando pipeline com batch_size={batch_size:,}")
            inicio = time.perf_counter()

            registros_processados = self.pipeline(
                batch_size=batch_size,
                num_of_files=self.files_to_process,
                offset=self.offset,
            )

            fim = time.perf_counter()
            tempo_execucao = fim - inicio
            tempos.append(tempo_execucao)

            registros_processados = registros_processados or 0
            taxa_media = (
                registros_processados / tempo_execucao if tempo_execucao > 0 else 0
            )
            taxas.append(taxa_media)

            print(
                f"✅ Batch size {batch_size:,}: {registros_processados:,} registros em "
                f"{tempo_execucao:.2f}s (≈ {taxa_media:,.0f} regs/s)"
            )

        plt.figure(figsize=(8, 5))
        sns.lineplot(x=batch_sizes[: len(tempos)], y=tempos, marker="o")
        plt.title("Tempo total vs tamanho do batch")
        plt.xlabel("Tamanho do batch")
        plt.ylabel("Tempo de execução (s)")
        plt.tight_layout()
        plt.savefig("benchmark_insert.png")
        print("📈 Gráfico de tempo salvo como benchmark_insert.png")

        plt.figure(figsize=(8, 5))
        sns.lineplot(x=batch_sizes[: len(taxas)], y=taxas, marker="o", color="green")
        plt.title("Taxa média vs tamanho do batch")
        plt.xlabel("Tamanho do batch")
        plt.ylabel("Registros por segundo")
        plt.tight_layout()
        plt.savefig("benchmark_insert_throughput.png")
        print("📈 Gráfico de throughput salvo como benchmark_insert_throughput.png")
