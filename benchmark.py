import time
import matplotlib.pyplot as plt
from fetch_db import ZipFileAnalyzer
import seaborn as sns


class BenchmarkExecutor:

    def __init__(self, files_to_process, offset, pipeline, batch_size):
        self.files_to_process = files_to_process
        self.offset = offset
        self.zip_path = "/Users/raphaelportela/datasetcovid.zip"
        self.pipeline = pipeline
        self.batch_size = batch_size

    
    def processamento(self):
        sns.set(style="whitegrid")
        number_of_files = [5000, 7000, 10000]
        plt.figure(figsize=(8, 5))
        # sns.lineplot(x=tamanhos, y=tempos, marker="o")
        [files for files in number_of_files ]
        tempos = []
        for n in number_of_files:
            inicio = time.perf_counter()
            self.pipeline.execute_batch_insert(
                batch_size=self.batch_size,
                number_of_files=n,
                offset=self.offset
            )
            fim = time.perf_counter()
            tempo_execucao = fim - inicio
            tempos.append(tempo_execucao)
            plt.figure(figsize=(8, 5))
            sns.lineplot(x=number_of_files, y=tempos, marker="o")
            plt.title("Desempenho do pipeline de inserção (tempo vs número de arquivos)")
            plt.xlabel("Número de arquivos processados")
            plt.ylabel("Tempo de execução (segundos)")
            plt.tight_layout()
            plt.savefig("benchmark_insert.png")
            print("📈 Gráfico salvo como benchmark_insert.png")
            
            



    

