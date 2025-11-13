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
        plt.figure(figsize=(8, 5))
        # sns.lineplot(x=tamanhos, y=tempos, marker="o")
        # [files for files in number_of_files]
        tempos = []
        connector = DatabaseConnector()
        for n in batch_sizes:
            connector.truncate_table(table_name="artigos_stg")
            inicio = time.perf_counter()

            self.pipeline(
                batch_size=n, num_of_files=self.files_to_process, offset=self.offset
            )
            fim = time.perf_counter()
            tempo_execucao = fim - inicio
            tempos.append(tempo_execucao)
            plt.figure(figsize=(8, 5))
            sns.lineplot(x=batch_sizes, y=tempos, marker="o")
            plt.title(
                "Desempenho do pipeline de inserção (tempo vs número de arquivos)"
            )
            plt.xlabel("Número de arquivos processados")
            plt.ylabel("Tempo de execução (segundos)")
            plt.tight_layout()
            plt.savefig("benchmark_insert.png")
            print("📈 Gráfico salvo como benchmark_insert.png")
