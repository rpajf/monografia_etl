import inspect
import time
import matplotlib.pyplot as plt
import seaborn as sns

from etl_psycopg3 import DatabaseConnector


class BenchmarkExecutor:
    def __init__(self, files_to_process, offset, pipeline, max_tasks: int = 4):
        self.files_to_process = files_to_process
        self.offset = offset
        self.zip_path = "/Users/raphaelportela/datasetcovid.zip"
        self.pipeline = pipeline
        self.max_tasks = max_tasks
        self._pipeline_params = inspect.signature(pipeline).parameters
        # self.batch_size = batch_size 

    async def processamento_async(self):
        sns.set(style="whitegrid")
        batch_sizes = [10000, 20000]
        tempos = []
        taxas = []
        registros_por_batch = []
        tempo_por_registro_ms = []
        parse_tempos = []
        insert_tempos = []
        connector = DatabaseConnector()

        for batch_size in batch_sizes:
            connector.truncate_table(table_name="artigos_stg")
            print(f"\n🚀 Rodando pipeline com batch_size={batch_size:,}")
            inicio = time.perf_counter()

            call_kwargs = dict(
                batch_size=batch_size,
                num_of_files=self.files_to_process,
                offset=self.offset,
            )
            if "max_tasks" in self._pipeline_params:
                call_kwargs["max_tasks"] = self.max_tasks

            pipeline_result = await self.pipeline(**call_kwargs)

            fim = time.perf_counter()
            tempo_execucao = fim - inicio
            tempos.append(tempo_execucao)

            registros_processados = 0
            batch_metrics = []
            if isinstance(pipeline_result, dict):
                registros_processados = pipeline_result.get("total_inserted", 0)
                batch_metrics = pipeline_result.get("batch_metrics", [])
            else:
                registros_processados = pipeline_result or 0
            registros_por_batch.append(registros_processados)
            taxa_media = (
                registros_processados / tempo_execucao if tempo_execucao > 0 else 0
            )
            taxas.append(taxa_media)
            tempo_ms = (
                (tempo_execucao / registros_processados) * 1000
                if registros_processados > 0
                else 0
            )
            tempo_por_registro_ms.append(tempo_ms)
            parse_total = sum(m.get("parse_time", 0) for m in batch_metrics)
            insert_total = sum(m.get("insert_time", 0) for m in batch_metrics)
            if parse_total == 0 and insert_total == 0:
                parse_total = tempo_execucao
            parse_tempos.append(parse_total)
            insert_tempos.append(insert_total)

            print(
                f"✅ Batch size {batch_size:,}: {registros_processados:,} registros em "
                f"{tempo_execucao:.2f}s (≈ {taxa_media:,.0f} regs/s)"
            )

        self._plot_metrics(
            batch_sizes,
            tempos,
            taxas,
            tempo_por_registro_ms,
            registros_por_batch,
            parse_tempos,
            insert_tempos,
            prefix="async_",
        )

    def processamento(self):
        sns.set(style="whitegrid")
        batch_sizes = [10000, 20000, 30000]
        tempos = []
        taxas = []
        registros_por_batch = []
        tempo_por_registro_ms = []
        parse_tempos = []
        insert_tempos = []
        connector = DatabaseConnector()

        for batch_size in batch_sizes:
            connector.truncate_table(table_name="artigos_stg")
            print(f"\n🚀 Rodando pipeline com batch_size={batch_size:,}")
            inicio = time.perf_counter()

            call_kwargs = dict(
                batch_size=batch_size,
                num_of_files=self.files_to_process,
                offset=self.offset,
            )
            if "max_tasks" in self._pipeline_params:
                call_kwargs["max_tasks"] = self.max_tasks

            pipeline_result = self.pipeline(**call_kwargs)

            fim = time.perf_counter()
            tempo_execucao = fim - inicio
            tempos.append(tempo_execucao)

            registros_processados = 0
            batch_metrics = []
            if isinstance(pipeline_result, dict):
                registros_processados = pipeline_result.get("total_inserted", 0)
                batch_metrics = pipeline_result.get("batch_metrics", [])
            else:
                registros_processados = pipeline_result or 0
            registros_por_batch.append(registros_processados)
            taxa_media = (
                registros_processados / tempo_execucao if tempo_execucao > 0 else 0
            )
            taxas.append(taxa_media)
            tempo_ms = (
                (tempo_execucao / registros_processados) * 1000
                if registros_processados > 0
                else 0
            )
            tempo_por_registro_ms.append(tempo_ms)
            parse_total = sum(m.get("parse_time", 0) for m in batch_metrics)
            insert_total = sum(m.get("insert_time", 0) for m in batch_metrics)
            if parse_total == 0 and insert_total == 0:
                parse_total = tempo_execucao
            parse_tempos.append(parse_total)
            insert_tempos.append(insert_total)

            print(
                f"✅ Batch size {batch_size:,}: {registros_processados:,} registros em "
                f"{tempo_execucao:.2f}s (≈ {taxa_media:,.0f} regs/s)"
            )

        self._plot_metrics(
            batch_sizes,
            tempos,
            taxas,
            tempo_por_registro_ms,
            registros_por_batch,
            parse_tempos,
            insert_tempos,
            prefix="sync_",
        )

    def _plot_metrics(
        self,
        batch_sizes,
        tempos,
        taxas,
        tempo_por_registro_ms,
        registros_por_batch,
        parse_tempos,
        insert_tempos,
        prefix: str,
    ):
        tempo_total = sum(tempos)
        x_vals = batch_sizes[: len(tempos)]

        def annotate(ax, xs, ys, fmt):
            for x, y in zip(xs, ys):
                ax.annotate(fmt(y), (x, y), textcoords="offset points", xytext=(0, 8), ha="center")

        # Tempo total
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(x=x_vals, y=tempos, marker="o", ax=ax)
        ax.set_title("Tempo total vs tamanho do batch")
        ax.set_xlabel("Tamanho do batch")
        ax.set_ylabel("Tempo de execução (s)")
        annotate(ax, x_vals, tempos, lambda v: f"{v:.2f}s")
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.2)
        fig.text(
            0.5,
            0.02,
            f"Duração total ({prefix.rstrip('_')}): {tempo_total:.2f}s",
            ha="center",
            fontsize=10,
        )
        time_path = f"{prefix}benchmark_insert.png"
        fig.savefig(time_path)
        print(f"📈 Gráfico de tempo salvo como {time_path}")

        # Throughput
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(x=batch_sizes[: len(taxas)], y=taxas, marker="o", color="green", ax=ax)
        ax.set_title("Taxa média vs tamanho do batch")
        ax.set_xlabel("Tamanho do batch")
        ax.set_ylabel("Registros por segundo")
        annotate(
            ax,
            batch_sizes[: len(taxas)],
            taxas,
            lambda v: f"{v:,.0f}/s",
        )
        fig.tight_layout()
        throughput_path = f"{prefix}benchmark_insert_throughput.png"
        fig.savefig(throughput_path)
        print(f"📈 Gráfico de throughput salvo como {throughput_path}")

        # Latência média por registro
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(
            x=batch_sizes[: len(tempo_por_registro_ms)],
            y=tempo_por_registro_ms,
            marker="o",
            color="orange",
            ax=ax,
        )
        ax.set_title("Tempo médio por registro")
        ax.set_xlabel("Tamanho do batch")
        ax.set_ylabel("ms por registro")
        annotate(
            ax,
            batch_sizes[: len(tempo_por_registro_ms)],
            tempo_por_registro_ms,
            lambda v: f"{v:.2f} ms",
        )
        fig.tight_layout()
        latency_path = f"{prefix}benchmark_insert_latency.png"
        fig.savefig(latency_path)
        print(f"📈 Gráfico de latência salvo como {latency_path}")

        # Composição do tempo (parse vs insert)
        parse_vals = parse_tempos[: len(x_vals)] if parse_tempos else [0] * len(x_vals)
        insert_vals = (
            insert_tempos[: len(x_vals)] if insert_tempos else [0] * len(x_vals)
        )
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(x_vals, parse_vals, label="Parsing / transformação", color="#1f77b4")
        ax.bar(
            x_vals,
            insert_vals,
            bottom=parse_vals,
            label="Inserção DB",
            color="#2ca02c",
        )
        ax.set_title("Composição do tempo do batch")
        ax.set_xlabel("Tamanho do batch")
        ax.set_ylabel("Tempo (s)")
        for x, p, i in zip(x_vals, parse_vals, insert_vals):
            if p > 0:
                ax.annotate(
                    f"{p:.1f}s",
                    (x, p / 2),
                    color="white",
                    ha="center",
                    va="center",
                    fontsize=8,
                )
            if i > 0:
                ax.annotate(
                    f"{i:.1f}s",
                    (x, p + i / 2),
                    color="white",
                    ha="center",
                    va="center",
                    fontsize=8,
                )
        ax.legend()
        fig.tight_layout()
        stage_path = f"{prefix}benchmark_insert_stage_breakdown.png"
        fig.savefig(stage_path)
        print(f"📈 Gráfico de composição salvo como {stage_path}")
