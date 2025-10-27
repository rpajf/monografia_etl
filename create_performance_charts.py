"""
Script para gerar gráficos de performance para sua monografia
Requer: matplotlib, pandas
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def create_performance_charts():
    """Cria gráficos comparativos de performance"""
    
    # Dados de exemplo (você deve substituir pelos seus resultados reais)
    # Execute test_insert_performance.py primeiro para obter dados reais
    
    # 1. Comparação de Tempo (10k registros)
    methods = ['Optimized\nSingle\nTransaction', 
               'Standard\n(executemany)', 
               'Parallel\nwith Pool', 
               'Parallel\n(new connections)']
    times = [2.5, 5.8, 4.2, 10.5]  # segundos (exemplo)
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Gráfico 1: Tempo de Execução
    bars1 = ax1.bar(methods, times, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Tempo (segundos)', fontsize=12, fontweight='bold')
    ax1.set_title('Tempo de Inserção - 10.000 Registros', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.set_ylim(0, max(times) * 1.2)
    
    # Adiciona valores nas barras
    for bar, time in zip(bars1, times):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.1f}s',
                ha='center', va='bottom', fontweight='bold')
    
    ax1.axhline(y=min(times), color='green', linestyle='--', 
                alpha=0.5, label='Melhor Performance')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Gráfico 2: Throughput (Registros/segundo)
    throughput = [10000/t for t in times]
    bars2 = ax2.bar(methods, throughput, color=colors, alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Registros/segundo', fontsize=12, fontweight='bold')
    ax2.set_title('Taxa de Inserção (Throughput)', 
                  fontsize=14, fontweight='bold', pad=20)
    ax2.set_ylim(0, max(throughput) * 1.2)
    
    # Adiciona valores nas barras
    for bar, rate in zip(bars2, throughput):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.0f}',
                ha='center', va='bottom', fontweight='bold')
    
    ax2.axhline(y=max(throughput), color='green', linestyle='--', 
                alpha=0.5, label='Melhor Performance')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('output/performance_comparison_10k.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 1 salvo: output/performance_comparison_10k.png")
    plt.close()
    
    # 2. Performance vs Tamanho do Dataset
    fig, ax = plt.subplots(figsize=(12, 7))
    
    dataset_sizes = [1000, 5000, 10000, 50000, 100000]
    
    # Dados simulados (substitua pelos seus dados reais)
    optimized_times = [0.5, 1.2, 2.5, 12, 25]
    standard_times = [1.2, 3.5, 5.8, 35, 75]
    pool_times = [2.0, 3.0, 4.2, 15, 28]
    new_conn_times = [3.5, 6.0, 10.5, 55, 120]
    
    ax.plot(dataset_sizes, optimized_times, 'o-', linewidth=2.5, 
            markersize=8, label='Optimized Single Transaction', color='#2ecc71')
    ax.plot(dataset_sizes, standard_times, 's-', linewidth=2.5, 
            markersize=8, label='Standard (executemany)', color='#3498db')
    ax.plot(dataset_sizes, pool_times, '^-', linewidth=2.5, 
            markersize=8, label='Parallel with Pool', color='#f39c12')
    ax.plot(dataset_sizes, new_conn_times, 'v-', linewidth=2.5, 
            markersize=8, label='Parallel (new connections)', color='#e74c3c')
    
    ax.set_xlabel('Número de Registros', fontsize=13, fontweight='bold')
    ax.set_ylabel('Tempo (segundos)', fontsize=13, fontweight='bold')
    ax.set_title('Performance vs Tamanho do Dataset', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # Adiciona anotações
    ax.annotate('Seu caso\n(10k registros)', 
                xy=(10000, 2.5), xytext=(20000, 1.5),
                arrowprops=dict(arrowstyle='->', color='black', lw=2),
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('output/performance_vs_dataset_size.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 2 salvo: output/performance_vs_dataset_size.png")
    plt.close()
    
    # 3. Análise de Overhead
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Breakdown de tempo para paralelo com novas conexões
    categories = ['SQL\nExecution', 'Connection\nOverhead', 'Thread\nManagement', 
                  'Commit\nOverhead', 'Lock\nContention']
    overhead_times = [3.0, 2.5, 1.5, 2.0, 1.5]  # segundos (exemplo)
    overhead_colors = ['#2ecc71', '#e74c3c', '#e67e22', '#9b59b6', '#e84393']
    
    wedges, texts, autotexts = ax.pie(overhead_times, labels=categories, autopct='%1.1f%%',
                                        colors=overhead_colors, startangle=90,
                                        textprops={'fontsize': 12, 'fontweight': 'bold'})
    
    # Destaca o SQL real
    wedges[0].set_edgecolor('black')
    wedges[0].set_linewidth(3)
    
    ax.set_title('Análise de Overhead - Parallel (new connections)\nTotal: 10.5s para 10k registros', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Legenda com tempos absolutos
    legend_labels = [f'{cat.replace(chr(10), " ")}: {time:.1f}s' 
                     for cat, time in zip(categories, overhead_times)]
    ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize=10)
    
    plt.tight_layout()
    plt.savefig('output/overhead_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 3 salvo: output/overhead_analysis.png")
    plt.close()
    
    # 4. Speedup Comparison (vs Standard)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    speedups = [times[1]/times[0],  # Optimized vs Standard
                times[1]/times[1],  # Standard vs Standard (baseline)
                times[1]/times[2],  # Pool vs Standard
                times[1]/times[3]]  # New Conn vs Standard
    
    bars = ax.barh(methods, speedups, color=colors, alpha=0.8, edgecolor='black')
    ax.set_xlabel('Speedup (vs Standard executemany)', fontsize=12, fontweight='bold')
    ax.set_title('Fator de Aceleração Relativo', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.axvline(x=1, color='black', linestyle='--', linewidth=2, label='Baseline (1x)')
    
    # Adiciona valores
    for bar, speedup in zip(bars, speedups):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2.,
                f'{speedup:.2f}x',
                ha='left', va='center', fontweight='bold', fontsize=11,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    ax.legend()
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlim(0, max(speedups) * 1.3)
    
    plt.tight_layout()
    plt.savefig('output/speedup_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 4 salvo: output/speedup_comparison.png")
    plt.close()
    
    print("\n" + "="*60)
    print("✅ Todos os gráficos foram criados com sucesso!")
    print("="*60)
    print("\n📊 Gráficos criados:")
    print("  1. performance_comparison_10k.png - Comparação direta de tempo/throughput")
    print("  2. performance_vs_dataset_size.png - Escalabilidade dos métodos")
    print("  3. overhead_analysis.png - Breakdown de overhead")
    print("  4. speedup_comparison.png - Fator de aceleração")
    print("\n💡 Para sua tese:")
    print("  - Use esses gráficos como base")
    print("  - Substitua os dados de exemplo pelos seus resultados reais")
    print("  - Execute test_insert_performance.py para obter dados precisos")
    print("  - Adicione barras de erro se fizer múltiplas execuções")

def create_summary_table():
    """Cria tabela resumo em formato para LaTeX"""
    
    data = {
        'Método': [
            'Optimized Single Transaction',
            'Standard (executemany)',
            'Parallel with Pool',
            'Parallel (new connections)'
        ],
        'Tempo (s)': [2.5, 5.8, 4.2, 10.5],
        'Registros/s': [4000, 1724, 2381, 952],
        'Speedup': [2.32, 1.00, 1.38, 0.55],
        'Rank': [1, 2, 3, 4]
    }
    
    df = pd.DataFrame(data)
    
    print("\n" + "="*80)
    print("📋 TABELA RESUMO - Para incluir na sua monografia")
    print("="*80 + "\n")
    print(df.to_string(index=False))
    
    # Exporta para LaTeX
    latex_table = df.to_latex(index=False, float_format="%.2f",
                               caption="Comparação de Performance - Inserção de 10.000 registros",
                               label="tab:performance_comparison")
    
    with open('output/performance_table.tex', 'w') as f:
        f.write(latex_table)
    
    print("\n✅ Tabela LaTeX salva em: output/performance_table.tex")
    
    # Exporta para CSV
    df.to_csv('output/performance_results.csv', index=False)
    print("✅ Resultados CSV salvos em: output/performance_results.csv")

if __name__ == "__main__":
    import os
    
    # Cria diretório output se não existir
    os.makedirs('output', exist_ok=True)
    
    print("\n" + "="*60)
    print("📊 GERADOR DE GRÁFICOS DE PERFORMANCE")
    print("="*60 + "\n")
    print("⚠️  ATENÇÃO: Estes gráficos usam dados de EXEMPLO")
    print("   Para dados reais, execute:")
    print("   1. python test_insert_performance.py")
    print("   2. Copie os resultados para este script")
    print("   3. Execute novamente\n")
    
    create_performance_charts()
    create_summary_table()
    
    print("\n" + "="*60)
    print("🎓 PRONTO PARA SUA MONOGRAFIA!")
    print("="*60)
    print("\nPróximos passos:")
    print("  1. ✅ Execute test_insert_performance.py para dados reais")
    print("  2. ✅ Atualize os valores neste script")
    print("  3. ✅ Gere os gráficos finais")
    print("  4. ✅ Inclua na sua tese com as análises")

