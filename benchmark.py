import inspect
import time
import matplotlib.pyplot as plt
import seaborn as sns
import psutil
import os
import asyncio
import threading

from etl_psycopg3 import DatabaseConnector


class BenchmarkExecutor:
    def __init__(self, files_to_process, offset, pipeline, max_tasks: int = 4):
        self.files_to_process = files_to_process
        self.offset = offset
        self.zip_path = "/Users/raphaelportela/datasetcovid.zip"
        self.pipeline = pipeline
        self.max_tasks = max_tasks
        self._pipeline_params = inspect.signature(pipeline).parameters
        self.process = psutil.Process(os.getpid())
        self._memory_samples = []
        self._monitoring_active = False

    def _get_memory_mb(self):
        """Get current memory usage in MB"""
        try:
            # Use RSS (Resident Set Size) - actual physical memory used
            return self.process.memory_info().rss / (1024 ** 2)
        except Exception:
            return 0.0
    
    def _get_memory_info(self):
        """Get detailed memory information"""
        try:
            mem_info = self.process.memory_info()
            return {
                "rss_mb": mem_info.rss / (1024 ** 2),  # Resident Set Size
                "vms_mb": mem_info.vms / (1024 ** 2),  # Virtual Memory Size
                "percent": self.process.memory_percent(),  # Percentage of system RAM
            }
        except Exception:
            return {"rss_mb": 0.0, "vms_mb": 0.0, "percent": 0.0}
    
    async def _monitor_memory_async(self, interval=0.5):
        """Monitor memory usage during async execution"""
        self._memory_samples = []
        while self._monitoring_active:
            mem_info = self._get_memory_info()
            mem_info["timestamp"] = time.perf_counter()
            self._memory_samples.append(mem_info)
            await asyncio.sleep(interval)
    
    def _monitor_memory_sync(self, interval=0.5):
        """Monitor memory usage during sync execution"""
        self._memory_samples = []
        while self._monitoring_active:
            mem_info = self._get_memory_info()
            mem_info["timestamp"] = time.perf_counter()
            self._memory_samples.append(mem_info)
            time.sleep(interval)

    async def processamento_async(self):
        sns.set(style="whitegrid", palette="husl")
        batch_sizes = [10000, 20000, 30000]
        tempos = []
        taxas = []
        registros_por_batch = []
        tempo_por_registro_ms = []
        parse_tempos = []
        insert_tempos = []
        memory_metrics = []  # List of dicts with memory info per batch_size
        connector = DatabaseConnector()

        for batch_size in batch_sizes:
            connector.truncate_table(table_name="artigos_stg")
            print(f"\n🚀 Rodando pipeline com batch_size={batch_size:,}")
            
            # Initial memory
            mem_start_info = self._get_memory_info()
            mem_start = mem_start_info["rss_mb"]
            inicio = time.perf_counter()
            
            # Start memory monitoring
            self._monitoring_active = True
            monitor_task = asyncio.create_task(self._monitor_memory_async(interval=0.5))

            call_kwargs = dict(
                batch_size=batch_size,
                num_of_files=self.files_to_process,
                offset=self.offset,
            )
            if "max_tasks" in self._pipeline_params:
                call_kwargs["max_tasks"] = self.max_tasks

            pipeline_result = await self.pipeline(**call_kwargs)

            # Stop monitoring
            self._monitoring_active = False
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            
            fim = time.perf_counter()
            mem_end_info = self._get_memory_info()
            mem_end = mem_end_info["rss_mb"]
            tempo_execucao = fim - inicio
            
            # Calculate peak memory from samples
            if self._memory_samples:
                mem_peak = max(s["rss_mb"] for s in self._memory_samples)
                mem_avg_samples = sum(s["rss_mb"] for s in self._memory_samples) / len(self._memory_samples)
            else:
                mem_peak = max(mem_start, mem_end)
                mem_avg_samples = (mem_start + mem_end) / 2
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
            
            # Calculate memory metrics
            mem_avg = mem_avg_samples
            mem_delta = mem_end - mem_start
            memory_rate = mem_delta / tempo_execucao if tempo_execucao > 0 else 0
            
            # Get system memory info for context
            try:
                system_mem = psutil.virtual_memory()
                mem_percent_of_system = (mem_peak / (system_mem.total / (1024 ** 2))) * 100
            except:
                mem_percent_of_system = 0
            
            memory_metrics.append({
                "batch_size": batch_size,
                "mem_start_mb": mem_start,
                "mem_end_mb": mem_end,
                "mem_peak_mb": mem_peak,
                "mem_avg_mb": mem_avg,
                "mem_delta_mb": mem_delta,
                "memory_rate_mb_per_s": memory_rate,
                "mem_percent_of_system": mem_percent_of_system,
                "memory_samples": self._memory_samples.copy(),  # Store samples for time-series
                "batch_metrics": batch_metrics, 
            })

            print(
                f"✅ Batch size {batch_size:,}: {registros_processados:,} registros em "
                f"{tempo_execucao:.2f}s (≈ {taxa_media:,.0f} regs/s)"
            )
            print(
                f"   💾 Memória: {mem_start:.1f}MB → {mem_end:.1f}MB "
                f"(Pico: {mem_peak:.1f}MB, Δ{mem_delta:+.1f}MB, "
                f"{mem_percent_of_system:.2f}% do sistema)"
            )

        self._plot_metrics(
            batch_sizes,
            tempos,
            taxas,
            tempo_por_registro_ms,
            registros_por_batch,
            parse_tempos,
            insert_tempos,
            memory_metrics,
            prefix="async_",
        )

    def processamento(self):
        sns.set(style="whitegrid", palette="husl")
        batch_sizes = [10000, 20000, 30000]
        tempos = []
        taxas = []
        registros_por_batch = []
        tempo_por_registro_ms = []
        parse_tempos = []
        insert_tempos = []
        memory_metrics = []
        connector = DatabaseConnector()

        for batch_size in batch_sizes:
            connector.truncate_table(table_name="artigos_stg")
            print(f"\n🚀 Rodando pipeline com batch_size={batch_size:,}")
            
            mem_start_info = self._get_memory_info()
            mem_start = mem_start_info["rss_mb"]
            inicio = time.perf_counter()
            
            # Start memory monitoring in background thread
            self._monitoring_active = True
            monitor_thread = threading.Thread(
                target=self._monitor_memory_sync, args=(0.5,), daemon=True
            )
            monitor_thread.start()

            call_kwargs = dict(
                batch_size=batch_size,
                num_of_files=self.files_to_process,
                offset=self.offset,
            )
            if "max_tasks" in self._pipeline_params:
                call_kwargs["max_tasks"] = self.max_tasks

            pipeline_result = self.pipeline(**call_kwargs)

            # Stop monitoring
            self._monitoring_active = False
            monitor_thread.join(timeout=1.0)
            
            fim = time.perf_counter()
            mem_end_info = self._get_memory_info()
            mem_end = mem_end_info["rss_mb"]
            tempo_execucao = fim - inicio
            
            # Calculate peak memory from samples
            if self._memory_samples:
                mem_peak = max(s["rss_mb"] for s in self._memory_samples)
                mem_avg_samples = sum(s["rss_mb"] for s in self._memory_samples) / len(self._memory_samples)
            else:
                mem_peak = max(mem_start, mem_end)
                mem_avg_samples = (mem_start + mem_end) / 2
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
            
            mem_avg = mem_avg_samples
            mem_delta = mem_end - mem_start
            memory_rate = mem_delta / tempo_execucao if tempo_execucao > 0 else 0
            
            # Get system memory info for context
            try:
                system_mem = psutil.virtual_memory()
                mem_percent_of_system = (mem_peak / (system_mem.total / (1024 ** 2))) * 100
            except:
                mem_percent_of_system = 0
            
            memory_metrics.append({
                "batch_size": batch_size,
                "mem_start_mb": mem_start,
                "mem_end_mb": mem_end,
                "mem_peak_mb": mem_peak,
                "mem_avg_mb": mem_avg,
                "mem_delta_mb": mem_delta,
                "memory_rate_mb_per_s": memory_rate,
                "mem_percent_of_system": mem_percent_of_system,
                "memory_samples": self._memory_samples.copy(),
                "batch_metrics": batch_metrics,
            })

            print(
                f"✅ Batch size {batch_size:,}: {registros_processados:,} registros em "
                f"{tempo_execucao:.2f}s (≈ {taxa_media:,.0f} regs/s)"
            )
            print(
                f"   💾 Memória: {mem_start:.1f}MB → {mem_end:.1f}MB "
                f"(Pico: {mem_peak:.1f}MB, Δ{mem_delta:+.1f}MB, "
                f"{mem_percent_of_system:.2f}% do sistema)"
            )

        self._plot_metrics(
            batch_sizes,
            tempos,
            taxas,
            tempo_por_registro_ms,
            registros_por_batch,
            parse_tempos,
            insert_tempos,
            memory_metrics,
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
        memory_metrics,
        prefix: str,
    ):
        tempo_total = sum(tempos)
        x_vals = batch_sizes[: len(tempos)]

        def annotate(ax, xs, ys, fmt):
            for x, y in zip(xs, ys):
                ax.annotate(
                    fmt(y), (x, y), textcoords="offset points", xytext=(0, 8), ha="center"
                )

        # ========== GRAPH 1: Time Elapsed vs Rows Inserted ==========
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Use scatter plot with different colors/markers for each batch size
        colors = ["#2E86AB", "#06A77D", "#E63946"]
        markers = ["o", "s", "^"]
        
        for i, (rows, time_val, batch_size) in enumerate(
            zip(registros_por_batch, tempos, x_vals)
        ):
            ax.scatter(
                rows, 
                time_val,
                s=200,
                c=colors[i % len(colors)],
                marker=markers[i % len(markers)],
                edgecolors="black",
                linewidths=2,
                alpha=0.7,
                label=f"Batch {batch_size:,}",
                zorder=5
            )
            # Annotate with batch size and time
            ax.annotate(
                f"batch={batch_size:,}\n{time_val:.2f}s\n({time_val/60:.1f} min)",
                (rows, time_val),
                textcoords="offset points",
                xytext=(15, 15),
                ha="left",
                fontsize=10,
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.5", 
                    facecolor=colors[i % len(colors)], 
                    alpha=0.7,
                    edgecolor="black",
                    linewidth=1.5
                ),
                arrowprops=dict(
                    arrowstyle="->",
                    connectionstyle="arc3,rad=0.2",
                    color="black",
                    lw=1.5
                ),
            )
        
        # Add a line connecting points if they're close together (same records processed)
        if len(set(registros_por_batch)) == 1:
            # All points have same X value - add vertical line to show they're comparable
            common_x = registros_por_batch[0]
            ax.axvline(
                x=common_x, 
                color="gray", 
                linestyle="--", 
                alpha=0.3, 
                linewidth=2,
                label="Mesmo número de registros"
            )
            # Add text explaining this
            ax.text(
                common_x, 
                max(tempos) * 0.95,
                f"Todos processaram\n{common_x:,} registros",
                ha="center",
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7),
                rotation=0
            )
        else:
            # Connect points with line if X values differ
            ax.plot(
                registros_por_batch,
                tempos,
                linestyle="--",
                color="gray",
                alpha=0.3,
                linewidth=1,
                zorder=1
            )
        
        ax.set_title(
            f"Tempo de Execução vs Registros Processados ({prefix.rstrip('_').upper()})\n"
            f"Comparação de Diferentes Tamanhos de Batch",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("Registros Processados", fontsize=12)
        ax.set_ylabel("Tempo de Execução (segundos)", fontsize=12)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend(loc="best", fontsize=10, framealpha=0.9)
        
        # Format x-axis to show numbers clearly
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        
        fig.tight_layout()
        time_rows_path = f"{prefix}benchmark_time_vs_rows.png"
        fig.savefig(time_rows_path, dpi=300, bbox_inches="tight")
        print(f"📈 Gráfico tempo vs registros salvo como {time_rows_path}")

        # ========== GRAPH 2: Memory Usage Rate and Performance Metrics ==========
        fig = plt.figure(figsize=(14, 8))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # 2.1 Memory Usage Rate vs Batch Size
        ax1 = fig.add_subplot(gs[0, 0])
        mem_rates = [m["memory_rate_mb_per_s"] for m in memory_metrics]
        mem_peaks = [m["mem_peak_mb"] for m in memory_metrics]
        
        ax1_twin = ax1.twinx()
        line1 = ax1.plot(
            x_vals, mem_rates, marker="o", linewidth=2.5, color="#E63946", label="Taxa (MB/s)"
        )
        line2 = ax1_twin.plot(
            x_vals, mem_peaks, marker="s", linewidth=2.5, color="#F77F00", label="Pico (MB)"
        )
        
        ax1.set_xlabel("Tamanho do Batch", fontsize=11)
        ax1.set_ylabel("Taxa de Uso de Memória (MB/s)", fontsize=11, color="#E63946")
        ax1_twin.set_ylabel("Memória Pico (MB)", fontsize=11, color="#F77F00")
        ax1.set_title("Uso de Memória por Configuração", fontsize=12, fontweight="bold")
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis="y", labelcolor="#E63946")
        ax1_twin.tick_params(axis="y", labelcolor="#F77F00")
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc="upper left")

        # 2.2 Throughput vs Batch Size
        ax2 = fig.add_subplot(gs[0, 1])
        sns.lineplot(x=x_vals, y=taxas, marker="o", linewidth=2.5, color="#06A77D", ax=ax2)
        ax2.set_title("Throughput (Registros/segundo)", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Tamanho do Batch", fontsize=11)
        ax2.set_ylabel("Registros por Segundo", fontsize=11)
        ax2.grid(True, alpha=0.3)
        annotate(ax2, x_vals, taxas, lambda v: f"{v:,.0f}/s")

        # 2.3 Memory Efficiency (Rows per MB)
        ax3 = fig.add_subplot(gs[1, 0])
        efficiency = [
            rows / mem["mem_peak_mb"] if mem["mem_peak_mb"] > 0 else 0
            for rows, mem in zip(registros_por_batch, memory_metrics)
        ]
        sns.barplot(x=[f"{bs:,}" for bs in x_vals], y=efficiency, ax=ax3, color="#7209B7")
        ax3.set_title("Eficiência de Memória (Registros/MB)", fontsize=12, fontweight="bold")
        ax3.set_xlabel("Tamanho do Batch", fontsize=11)
        ax3.set_ylabel("Registros por MB", fontsize=11)
        ax3.grid(True, alpha=0.3, axis="y")
        for i, (x, eff) in enumerate(zip(x_vals, efficiency)):
            ax3.text(
                i,
                eff,
                f"{eff:,.0f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        # 2.4 Stage Breakdown (Parse vs Insert)
        ax4 = fig.add_subplot(gs[1, 1])
        parse_vals = parse_tempos[: len(x_vals)] if parse_tempos else [0] * len(x_vals)
        insert_vals = (
            insert_tempos[: len(x_vals)] if insert_tempos else [0] * len(x_vals)
        )
        x_pos = range(len(x_vals))
        width = 0.35
        
        bars1 = ax4.bar(
            [p - width / 2 for p in x_pos],
            parse_vals,
            width,
            label="Parsing / Transformação",
            color="#1f77b4",
        )
        bars2 = ax4.bar(
            [p + width / 2 for p in x_pos],
            insert_vals,
            width,
            label="Inserção DB",
            color="#2ca02c",
        )
        
        ax4.set_title("Composição do Tempo por Etapa", fontsize=12, fontweight="bold")
        ax4.set_xlabel("Tamanho do Batch", fontsize=11)
        ax4.set_ylabel("Tempo (s)", fontsize=11)
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels([f"{bs:,}" for bs in x_vals])
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis="y")
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax4.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f"{height:.1f}s",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

        fig.suptitle(
            f"Métricas de Performance e Recursos - {prefix.rstrip('_').upper()}",
            fontsize=14,
            fontweight="bold",
            y=0.98,
        )
        memory_path = f"{prefix}benchmark_memory_and_performance.png"
        fig.savefig(memory_path, dpi=300, bbox_inches="tight")
        print(f"📈 Gráfico de memória e performance salvo como {memory_path}")

        # ========== GRAPH 3: Comprehensive Dashboard (Optional - Summary View) ==========
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            f"Dashboard Completo de Benchmark - {prefix.rstrip('_').upper()}",
            fontsize=16,
            fontweight="bold",
        )

        # 3.1 Time vs Rows (top left)
        axes[0, 0].plot(registros_por_batch, tempos, marker="o", linewidth=2, color="#2E86AB")
        axes[0, 0].set_title("Tempo vs Registros", fontweight="bold")
        axes[0, 0].set_xlabel("Registros")
        axes[0, 0].set_ylabel("Tempo (s)")
        axes[0, 0].grid(True, alpha=0.3)

        # 3.2 Memory Peak vs Batch Size (top right)
        axes[0, 1].plot(x_vals, mem_peaks, marker="s", linewidth=2, color="#E63946")
        axes[0, 1].set_title("Memória Pico vs Batch Size", fontweight="bold")
        axes[0, 1].set_xlabel("Batch Size")
        axes[0, 1].set_ylabel("Memória (MB)")
        axes[0, 1].grid(True, alpha=0.3)

        # 3.3 Throughput (bottom left)
        axes[1, 0].plot(x_vals, taxas, marker="o", linewidth=2, color="#06A77D")
        axes[1, 0].set_title("Throughput", fontweight="bold")
        axes[1, 0].set_xlabel("Batch Size")
        axes[1, 0].set_ylabel("Registros/s")
        axes[1, 0].grid(True, alpha=0.3)

        # 3.4 Latency (bottom right)
        axes[1, 1].plot(
            x_vals, tempo_por_registro_ms, marker="o", linewidth=2, color="#F77F00"
        )
        axes[1, 1].set_title("Latência Média por Registro", fontweight="bold")
        axes[1, 1].set_xlabel("Batch Size")
        axes[1, 1].set_ylabel("ms/registro")
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        dashboard_path = f"{prefix}benchmark_dashboard.png"
        fig.savefig(dashboard_path, dpi=300, bbox_inches="tight")
        print(f"📈 Dashboard completo salvo como {dashboard_path}")

        # ========== GRAPH 4: Memory Over Time (if samples available) ==========
        # Create memory timeline graph if we have samples
        has_samples = any(m.get("memory_samples") for m in memory_metrics)
        if has_samples:
            fig, axes = plt.subplots(len(memory_metrics), 1, figsize=(12, 4 * len(memory_metrics)))
            if len(memory_metrics) == 1:
                axes = [axes]
            
            fig.suptitle(
                f"Uso de Memória ao Longo do Tempo - {prefix.rstrip('_').upper()}",
                fontsize=14,
                fontweight="bold",
            )
            
            for idx, (mem_metric, batch_size) in enumerate(zip(memory_metrics, x_vals)):
                samples = mem_metric.get("memory_samples", [])
                if samples:
                    times = [(s["timestamp"] - samples[0]["timestamp"]) for s in samples]
                    mem_values = [s["rss_mb"] for s in samples]
                    
                    axes[idx].plot(times, mem_values, linewidth=2, color="#E63946", alpha=0.7)
                    axes[idx].fill_between(times, mem_values, alpha=0.3, color="#E63946")
                    axes[idx].axhline(
                        y=mem_metric["mem_peak_mb"],
                        color="red",
                        linestyle="--",
                        linewidth=1.5,
                        label=f"Pico: {mem_metric['mem_peak_mb']:.1f}MB",
                    )
                    axes[idx].axhline(
                        y=mem_metric["mem_start_mb"],
                        color="green",
                        linestyle="--",
                        linewidth=1,
                        label=f"Início: {mem_metric['mem_start_mb']:.1f}MB",
                    )
                    axes[idx].axhline(
                        y=mem_metric["mem_end_mb"],
                        color="blue",
                        linestyle="--",
                        linewidth=1,
                        label=f"Fim: {mem_metric['mem_end_mb']:.1f}MB",
                    )
                    
                    # Get system memory for reference
                    try:
                        system_mem = psutil.virtual_memory()
                        system_total_mb = system_mem.total / (1024 ** 2)
                        axes[idx].axhline(
                            y=system_total_mb,
                            color="gray",
                            linestyle=":",
                            linewidth=1,
                            alpha=0.5,
                            label=f"Sistema Total: {system_total_mb:.0f}MB",
                        )
                    except:
                        pass
                    
                    axes[idx].set_title(
                        f"Batch Size: {batch_size:,} | "
                        f"Pico: {mem_metric['mem_peak_mb']:.1f}MB "
                        f"({mem_metric.get('mem_percent_of_system', 0):.2f}% do sistema)",
                        fontweight="bold",
                    )
                    axes[idx].set_xlabel("Tempo (segundos)", fontsize=11)
                    axes[idx].set_ylabel("Memória RSS (MB)", fontsize=11)
                    axes[idx].grid(True, alpha=0.3)
                    axes[idx].legend(loc="upper left", fontsize=9)
            
            plt.tight_layout()
            memory_timeline_path = f"{prefix}benchmark_memory_timeline.png"
            fig.savefig(memory_timeline_path, dpi=300, bbox_inches="tight")
            print(f"📈 Gráfico de memória ao longo do tempo salvo como {memory_timeline_path}")

        # Print summary
        print(f"\n📊 Resumo do Benchmark ({prefix.rstrip('_')}):")
        print(f"   Tempo total: {tempo_total:.2f}s")
        print(f"   Total de registros: {sum(registros_por_batch):,}")
        if memory_metrics:
            avg_mem = sum(m["mem_peak_mb"] for m in memory_metrics) / len(memory_metrics)
            max_mem = max(m["mem_peak_mb"] for m in memory_metrics)
            try:
                system_mem = psutil.virtual_memory()
                system_total_mb = system_mem.total / (1024 ** 2)
                print(f"   Memória média pico: {avg_mem:.1f}MB")
                print(f"   Memória máxima pico: {max_mem:.1f}MB")
                print(f"   Memória do sistema: {system_total_mb:.0f}MB")
                print(f"   Uso máximo do sistema: {(max_mem/system_total_mb)*100:.2f}%")
            except:
                print(f"   Memória média pico: {avg_mem:.1f}MB")
                print(f"   Memória máxima pico: {max_mem:.1f}MB")
