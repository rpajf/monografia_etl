"""
Script para gerar gráfico sync com dados já coletados
Execute: python generate_sync_graph.py
"""
import matplotlib.pyplot as plt
import seaborn as sns

# Configure os dados do seu benchmark sync aqui
# Baseado no seu output, ajuste os valores se necessário

# ============================================================================
# DADOS DO BENCHMARK SYNC
# Ajuste estes valores com os dados reais do seu benchmark
# ============================================================================

sync_data = {
    "batch_sizes": [10000, 20000, 30000],
    
    # Tempos de execução (segundos) - DO SEU OUTPUT
    "tempos": [
        1320.36,  # Batch 10K - do gráfico que você mostrou
        1199.67,  # Batch 20K - do gráfico que você mostrou
        1794.47,  # Batch 30K - do seu output: "716,956 registros em 1794.47s"
    ],
    
    # Registros processados - todos devem ser ~716,956 (mesmo dataset)
    "registros": [
        716956,  # Batch 10K - mesmo número de arquivos processados
        716956,  # Batch 20K - mesmo número de arquivos processados
        716956,  # Batch 30K - do seu output
    ],
    
    # Memória pico (MB) - AJUSTE SE TIVER OS VALORES REAIS
    "memoria_peak_mb": [
        2000.0,  # Batch 10K - estimado, ajuste se tiver valor real
        2200.0,  # Batch 20K - estimado, ajuste se tiver valor real
        2785.9,  # Batch 30K - do seu output: "Pico: 2785.9MB"
    ],
    
    # Taxa de throughput (registros/segundo) - calculado automaticamente
    "taxas": [
        543,  # Batch 10K - calculado: 716956/1320.36
        598,  # Batch 20K - calculado: 716956/1199.67
        400,  # Batch 30K - do seu output: "≈ 400 regs/s"
    ],
    
    # Tempos de parse - AJUSTE SE TIVER OS VALORES REAIS
    "parse_tempos": [
        800.0,  # Batch 10K - estimado, ajuste se tiver valor real
        700.0,  # Batch 20K - estimado, ajuste se tiver valor real
        1000.0, # Batch 30K - estimado, ajuste se tiver valor real
    ],
    
    # Tempos de insert - AJUSTE SE TIVER OS VALORES REAIS
    "insert_tempos": [
        520.0,  # Batch 10K - estimado, ajuste se tiver valor real
        500.0,  # Batch 20K - estimado, ajuste se tiver valor real
        794.0,  # Batch 30K - estimado, ajuste se tiver valor real
    ],
}

def generate_sync_graphs():
    """Gera todos os gráficos sync com os dados fornecidos"""
    sns.set(style="whitegrid", palette="husl")
    
    batch_sizes = sync_data["batch_sizes"]
    tempos = sync_data["tempos"]
    registros = sync_data["registros"]
    memoria_peak = sync_data["memoria_peak_mb"]
    taxas = sync_data["taxas"]
    parse_tempos = sync_data["parse_tempos"]
    insert_tempos = sync_data["insert_tempos"]
    
    prefix = "sync_"
    
    # ========== GRAPH 1: Time Elapsed vs Rows Inserted ==========
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = ["#2E86AB", "#06A77D", "#E63946"]
    markers = ["o", "s", "^"]
    
    for i, (rows, time_val, batch_size) in enumerate(
        zip(registros, tempos, batch_sizes)
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
    
    # Add vertical line if all points have same X value
    if len(set(registros)) == 1:
        common_x = registros[0]
        ax.axvline(
            x=common_x, 
            color="gray", 
            linestyle="--", 
            alpha=0.3, 
            linewidth=2,
            label="Mesmo número de registros"
        )
        ax.text(
            common_x, 
            max(tempos) * 0.95,
            f"Todos processaram\n{common_x:,} registros",
            ha="center",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7),
        )
    
    ax.set_title(
        f"Tempo de Execução vs Registros Processados (SYNC)\n"
        f"Comparação de Diferentes Tamanhos de Batch",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Registros Processados", fontsize=12)
    ax.set_ylabel("Tempo de Execução (segundos)", fontsize=12)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="best", fontsize=10, framealpha=0.9)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
    
    fig.tight_layout()
    time_rows_path = f"{prefix}benchmark_time_vs_rows.png"
    fig.savefig(time_rows_path, dpi=300, bbox_inches="tight")
    print(f"📈 Gráfico tempo vs registros salvo como {time_rows_path}")
    
    # ========== GRAPH 2: Memory Usage Rate and Performance Metrics ==========
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # Calculate memory rates (approximate)
    memory_rates = []
    for i, (mem, time) in enumerate(zip(memoria_peak, tempos)):
        # Approximate memory rate (peak memory / time)
        rate = mem / time if time > 0 else 0
        memory_rates.append(rate)
    
    # 2.1 Memory Usage Rate vs Batch Size
    ax1 = fig.add_subplot(gs[0, 0])
    ax1_twin = ax1.twinx()
    line1 = ax1.plot(
        batch_sizes, memory_rates, marker="o", linewidth=2.5, color="#E63946", label="Taxa (MB/s)"
    )
    line2 = ax1_twin.plot(
        batch_sizes, memoria_peak, marker="s", linewidth=2.5, color="#F77F00", label="Pico (MB)"
    )
    
    ax1.set_xlabel("Tamanho do Batch", fontsize=11)
    ax1.set_ylabel("Taxa de Uso de Memória (MB/s)", fontsize=11, color="#E63946")
    ax1_twin.set_ylabel("Memória Pico (MB)", fontsize=11, color="#F77F00")
    ax1.set_title("Uso de Memória por Configuração", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis="y", labelcolor="#E63946")
    ax1_twin.tick_params(axis="y", labelcolor="#F77F00")
    
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left")
    
    # 2.2 Throughput vs Batch Size
    ax2 = fig.add_subplot(gs[0, 1])
    sns.lineplot(x=batch_sizes, y=taxas, marker="o", linewidth=2.5, color="#06A77D", ax=ax2)
    ax2.set_title("Throughput (Registros/segundo)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Tamanho do Batch", fontsize=11)
    ax2.set_ylabel("Registros por Segundo", fontsize=11)
    ax2.grid(True, alpha=0.3)
    for x, y in zip(batch_sizes, taxas):
        ax2.annotate(f"{y:,.0f}/s", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")
    
    # 2.3 Memory Efficiency (Rows per MB)
    ax3 = fig.add_subplot(gs[1, 0])
    efficiency = [rows / mem if mem > 0 else 0 for rows, mem in zip(registros, memoria_peak)]
    sns.barplot(x=[f"{bs:,}" for bs in batch_sizes], y=efficiency, ax=ax3, color="#7209B7")
    ax3.set_title("Eficiência de Memória (Registros/MB)", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Tamanho do Batch", fontsize=11)
    ax3.set_ylabel("Registros por MB", fontsize=11)
    ax3.grid(True, alpha=0.3, axis="y")
    for i, (x, eff) in enumerate(zip(batch_sizes, efficiency)):
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
    x_pos = range(len(batch_sizes))
    width = 0.35
    
    bars1 = ax4.bar(
        [p - width / 2 for p in x_pos],
        parse_tempos,
        width,
        label="Parsing / Transformação",
        color="#1f77b4",
    )
    bars2 = ax4.bar(
        [p + width / 2 for p in x_pos],
        insert_tempos,
        width,
        label="Inserção DB",
        color="#2ca02c",
    )
    
    ax4.set_title("Composição do Tempo por Etapa", fontsize=12, fontweight="bold")
    ax4.set_xlabel("Tamanho do Batch", fontsize=11)
    ax4.set_ylabel("Tempo (s)", fontsize=11)
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([f"{bs:,}" for bs in batch_sizes])
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis="y")
    
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
        f"Métricas de Performance e Recursos - SYNC",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )
    memory_path = f"{prefix}benchmark_memory_and_performance.png"
    fig.savefig(memory_path, dpi=300, bbox_inches="tight")
    print(f"📈 Gráfico de memória e performance salvo como {memory_path}")
    
    # ========== GRAPH 3: Dashboard ==========
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Dashboard Completo de Benchmark - SYNC",
        fontsize=16,
        fontweight="bold",
    )
    
    # 3.1 Time vs Rows
    axes[0, 0].scatter(registros, tempos, s=100, c=colors[:len(batch_sizes)], marker="o")
    axes[0, 0].set_title("Tempo vs Registros", fontweight="bold")
    axes[0, 0].set_xlabel("Registros")
    axes[0, 0].set_ylabel("Tempo (s)")
    axes[0, 0].grid(True, alpha=0.3)
    
    # 3.2 Memory Peak vs Batch Size
    axes[0, 1].plot(batch_sizes, memoria_peak, marker="s", linewidth=2, color="#E63946")
    axes[0, 1].set_title("Memória Pico vs Batch Size", fontweight="bold")
    axes[0, 1].set_xlabel("Batch Size")
    axes[0, 1].set_ylabel("Memória (MB)")
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3.3 Throughput
    axes[1, 0].plot(batch_sizes, taxas, marker="o", linewidth=2, color="#06A77D")
    axes[1, 0].set_title("Throughput", fontweight="bold")
    axes[1, 0].set_xlabel("Batch Size")
    axes[1, 0].set_ylabel("Registros/s")
    axes[1, 0].grid(True, alpha=0.3)
    
    # 3.4 Latency
    tempo_por_registro_ms = [(t / r) * 1000 if r > 0 else 0 for t, r in zip(tempos, registros)]
    axes[1, 1].plot(batch_sizes, tempo_por_registro_ms, marker="o", linewidth=2, color="#F77F00")
    axes[1, 1].set_title("Latência Média por Registro", fontweight="bold")
    axes[1, 1].set_xlabel("Batch Size")
    axes[1, 1].set_ylabel("ms/registro")
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    dashboard_path = f"{prefix}benchmark_dashboard.png"
    fig.savefig(dashboard_path, dpi=300, bbox_inches="tight")
    print(f"📈 Dashboard completo salvo como {dashboard_path}")
    
    print(f"\n✅ Gráficos gerados com sucesso!")
    print(f"   - {time_rows_path}")
    print(f"   - {memory_path}")
    print(f"   - {dashboard_path}")

if __name__ == "__main__":
    print("📊 Gerando gráficos sync com dados fornecidos...")
    print("\n⚠️  NOTA: Ajuste os valores em sync_data se necessário")
    print("   Baseado no seu output:")
    print("   - Batch 30K: 716,956 registros em 1794.47s")
    print("   - Tempo total: 4314.49s (soma de todos)")
    print("   - Total registros: 2,150,868\n")
    
    generate_sync_graphs()

