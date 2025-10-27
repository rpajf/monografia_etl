# Guia Rápido: Escolher Método de Inserção PostgreSQL

## 🎯 Árvore de Decisão

```
Quantos registros você tem?
│
├─ < 100k registros
│  └─ ✅ Use: insert_optimized_single_transaction()
│     Por quê? Overhead de paralelismo > benefício
│
├─ 100k - 500k registros
│  ├─ É carga única (batch job)?
│  │  └─ ✅ Use: insert_optimized_single_transaction()
│  │
│  └─ É API com múltiplas requisições concorrentes?
│     └─ ✅ Use: batch_process_with_pool()
│        Configuração: batch_size=10000, max_workers=3-4
│
└─ > 500k registros
   └─ ✅ Use: batch_process_with_pool()
      Configuração: batch_size=20000, max_workers=4-6
      OU considere PostgreSQL COPY FROM stdin
```

---

## 📋 Comparação Rápida

| Método | Melhor Para | Vantagens | Desvantagens |
|--------|-------------|-----------|--------------|
| **insert_optimized_single_transaction()** | < 100k registros | ⚡ Mais rápido<br>🔧 Simples<br>💾 Baixo overhead | ❌ Não escala para milhões |
| **batch_process_with_pool()** | > 500k registros<br>APIs concorrentes | 🔄 Reutiliza conexões<br>⚡ Paralelo real | ⚙️ Requer tuning<br>🐌 Lento para poucos dados |
| **batch_process_rows()** | ❌ NUNCA | Nenhuma | ❌ Cria conexões novas<br>❌ Muito lento |
| **insert_into_table_typed()** | Testes/Debug | 🔧 Simples | 🐌 Lento (executemany) |

---

## 🚀 Exemplos de Uso

### Exemplo 1: Dataset Pequeno (seu caso - 10k registros)

```python
from etl_psycopg3 import DatabaseConnector
from schemas import Artigo

# Carrega dados
models = [Artigo(**row) for row in df.to_dict(orient="records")]

# Inserção otimizada
connector = DatabaseConnector()
connector.insert_optimized_single_transaction(
    table_name="artigos",
    data_model_list=models
)
```

**Resultado esperado:** ~2-3 segundos para 10k registros

---

### Exemplo 2: Dataset Grande (> 500k registros)

```python
connector = DatabaseConnector()
connector.batch_process_with_pool(
    table_name="artigos",
    data_model_list=models,
    batch_size=20000,    # Lotes grandes
    max_workers=4        # 4 threads paralelas
)
```

**Resultado esperado:** ~15-20 segundos para 500k registros

---

### Exemplo 3: API com Requisições Concorrentes

```python
# Cria pool uma vez no startup da aplicação
connector = DatabaseConnector()  # Pool criado no __init__

# Em cada endpoint, use:
@app.post("/artigos")
def create_artigos(artigos: list[Artigo]):
    connector.batch_process_with_pool(
        table_name="artigos",
        data_model_list=artigos,
        batch_size=5000,
        max_workers=3
    )
```

---

## ⚙️ Configurações Recomendadas

### Para dataset pequeno (< 100k)
```python
connector.insert_optimized_single_transaction(
    table_name="tabela",
    data_model_list=models
)
# Sem configuração necessária - já otimizado!
```

### Para dataset médio (100k-500k)
```python
connector.batch_process_with_pool(
    table_name="tabela",
    data_model_list=models,
    batch_size=10000,    # Lotes médios
    max_workers=3        # Poucos workers
)
```

### Para dataset grande (> 500k)
```python
connector.batch_process_with_pool(
    table_name="tabela",
    data_model_list=models,
    batch_size=20000,    # Lotes grandes
    max_workers=6        # Mais workers
)
```

---

## 🔧 Tuning Avançado

### 1. Batch Size (tamanho do lote)

| Registros | batch_size recomendado | Razão |
|-----------|----------------------|-------|
| < 10k | N/A (use transação única) | Overhead > benefício |
| 10k-50k | 5000 | Balance overhead/parallelismo |
| 50k-200k | 10000 | Lotes médios eficientes |
| 200k-1M | 20000 | Lotes grandes, menos overhead |
| > 1M | 50000 | Maximiza throughput |

### 2. Max Workers (número de threads)

```python
# Fórmula: min(num_cpu_cores, num_batches / 2)

import os
num_cores = os.cpu_count()
num_batches = len(models) / batch_size
optimal_workers = min(num_cores, num_batches // 2, 6)
```

**Por quê limitar?**
- Mais threads = mais lock contention no PostgreSQL
- Sweet spot: 3-6 workers para maioria dos casos

### 3. PostgreSQL Tuning

Para cargas massivas, otimize PostgreSQL:

```sql
-- Antes da carga
SET synchronous_commit = OFF;
SET maintenance_work_mem = '256MB';
SET work_mem = '64MB';
SET checkpoint_completion_target = 0.9;

-- Após a carga
SET synchronous_commit = ON;
```

---

## ⚠️ Armadilhas Comuns

### ❌ Armadilha 1: "Mais threads = mais rápido"
```python
# ERRADO
connector.batch_process_with_pool(
    table_name="artigos",
    data_model_list=models,  # 10k registros
    batch_size=1000,
    max_workers=20  # ❌ Muito overhead!
)
```

**Correção:** Use `insert_optimized_single_transaction()` para < 100k

---

### ❌ Armadilha 2: "Batch size pequeno é mais seguro"
```python
# ERRADO
connector.batch_process_with_pool(
    table_name="artigos",
    data_model_list=models,  # 500k registros
    batch_size=100,  # ❌ Muito pequeno!
    max_workers=5
)
```

**Problema:** 5000 batches = overhead enorme

**Correção:** Use batch_size=20000 (25 batches)

---

### ❌ Armadilha 3: "ConnectionPool sempre é melhor"
```python
# DESNECESSÁRIO
connector.batch_process_with_pool(
    table_name="artigos",
    data_model_list=models,  # 5k registros
    batch_size=1000,
    max_workers=3
)
```

**Problema:** Overhead de pool + threads para poucos dados

**Correção:** Use `insert_optimized_single_transaction()`

---

## 📊 Benchmark do Seu Sistema

Execute este script para descobrir os limites do SEU sistema:

```python
# test_your_limits.py
from test_insert_performance import test_all_methods

# Teste com diferentes tamanhos
for size in [1000, 5000, 10000, 50000, 100000]:
    print(f"\n{'='*60}")
    print(f"Testing with {size} records")
    print(f"{'='*60}")
    test_all_methods(num_records=size)
```

---

## 🎓 Para sua Monografia

### Seção: "Análise de Performance"

1. **Introdução ao Problema**
   - Paralelismo nem sempre é melhor
   - Overhead vs benefício

2. **Metodologia**
   - 4 métodos testados
   - Configuração do ambiente
   - Dataset utilizado (COVID-19, Kaggle)

3. **Resultados**
   - Gráficos comparativos
   - Tabelas de performance
   - Análise de overhead

4. **Discussão**
   - Por que paralelo é mais lento em datasets pequenos
   - Trade-offs de cada abordagem
   - Recomendações práticas

5. **Conclusão**
   - Importância de benchmarking
   - Guia de decisão criado
   - Lições aprendidas

---

## 🔗 Arquivos Relacionados

- `PERFORMANCE_ANALYSIS.md` - Análise detalhada técnica
- `test_insert_performance.py` - Script de benchmark completo
- `etl_psycopg3.py` - Implementação dos métodos
- `fetch_db.py` - Pipeline ETL completo

---

**Última atualização:** Outubro 2025  
**Status:** ✅ Pronto para uso em produção e documentação acadêmica

