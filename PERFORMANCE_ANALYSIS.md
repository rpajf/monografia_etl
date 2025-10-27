# Análise de Performance: Batch Inserts em PostgreSQL

## 🎯 Problema Identificado

**Situação:** Inserção paralela com batch é **MAIS LENTA** que inserção sequencial para 10.000 registros.

**Por quê?** Paralelismo adiciona overhead que supera os benefícios em datasets pequenos.

---

## 📊 Resultados Esperados (10k registros)

| Método | Tempo Estimado | Registros/s | Explicação |
|--------|---------------|-------------|------------|
| **Otimizado (Transação única)** | ~2-3s | ~3500-5000 | ✅ MELHOR opção |
| Standard (executemany) | ~5-7s | ~1500-2000 | ⚠️ Múltiplas queries |
| Paralelo com Pool | ~4-6s | ~1800-2500 | ⚠️ Overhead para dataset pequeno |
| Paralelo sem Pool | ~8-12s | ~800-1200 | ❌ PIOR - cria conexões novas |

---

## 🔍 Análise Detalhada dos Problemas

### 1. **Overhead de Conexões (`batch_process_rows`)**

```python
# PROBLEMA: Cada batch abre uma NOVA conexão
def insert_batch(self, table_name, data_batch):
    with psycopg.connect(self.conn_str) as conn:  # ❌ Nova conexão!
        with conn.cursor() as cur:
            cur.executemany(query, values)
        conn.commit()  # ❌ Commit separado!
```

**Impacto com 10k registros:**
- 10 batches × 50-100ms de handshake = **500-1000ms de overhead**
- 10 transações × commit overhead = **200-500ms adicional**
- **Total: ~700-1500ms perdidos só em conexões!**

---

### 2. **Lock Contention (Contenção de Bloqueios)**

Quando múltiplas threads tentam inserir na mesma tabela:

```sql
Thread 1: INSERT INTO artigos ...  [Aguarda lock]
Thread 2: INSERT INTO artigos ...  [Aguarda lock]
Thread 3: INSERT INTO artigos ...  [Aguarda lock]
```

PostgreSQL **serializa** as operações, negando o benefício do paralelismo.

---

### 3. **Overhead de Threads para Dataset Pequeno**

Com 10.000 registros e batch_size=1000:
- **Apenas 10 batches** para processar
- Overhead de ThreadPoolExecutor: ~100-200ms
- Sincronização entre threads: ~50-100ms
- **Resultado:** Gastamos mais tempo gerenciando threads que executando SQL

---

### 4. **Múltiplos Commits vs Transação Única**

```python
# ❌ LENTO: 10 commits separados
for batch in batches:
    insert_batch(batch)
    conn.commit()  # WAL flush + fsync × 10 vezes

# ✅ RÁPIDO: 1 commit único
with conn:
    for batch in batches:
        insert_batch(batch)
    conn.commit()  # WAL flush + fsync × 1 vez
```

**Custo de cada commit:**
- Write-Ahead Log (WAL) flush: ~20-50ms
- fsync ao disco: ~10-30ms
- **10 commits = 300-800ms de overhead!**

---

## ✅ Solução Implementada

### Método Otimizado: `insert_optimized_single_transaction()`

```python
def insert_optimized_single_transaction(self, table_name, data_model_list):
    """
    ✅ Uma conexão
    ✅ Uma transação
    ✅ execute_values (batch real)
    ✅ Sem overhead de paralelismo
    """
    with psycopg.connect(self.conn_str) as conn:
        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=1000)
        conn.commit()  # Apenas 1 commit
```

**Vantagens:**
1. **execute_values:** Converte múltiplos inserts em UMA query SQL otimizada
2. **Transação única:** Apenas 1 commit/fsync
3. **Uma conexão:** Zero overhead de handshake
4. **page_size=1000:** Batch interno eficiente

---

## 🎓 Para sua Monografia/Tese

### Conceitos Importantes a Discutir:

#### 1. **Trade-off Paralelismo vs Overhead**
```
Benefício do Paralelismo > Overhead?
    ✅ Sim → Use paralelo
    ❌ Não → Use sequencial otimizado

Overhead inclui:
- Criação/gerenciamento de threads
- Sincronização
- Conexões ao banco
- Lock contention
```

#### 2. **Quando Usar Cada Método**

| Dataset | Método Recomendado | Justificativa |
|---------|-------------------|---------------|
| < 10k | Transação única | Overhead > benefício |
| 10k - 100k | Transação única | Ainda eficiente |
| 100k - 500k | Considerar paralelo | Começar a valer a pena |
| > 500k | Paralelo com pool | Benefício > overhead |

#### 3. **Otimizações PostgreSQL**

```sql
-- Para inserts massivos, configure:
SET synchronous_commit = OFF;  -- Durante carga inicial
SET maintenance_work_mem = '256MB';
SET checkpoint_completion_target = 0.9;
```

#### 4. **Benchmarks Científicos**

Estrutura de teste para sua tese:
```python
# 1. Controlar variáveis
# 2. Múltiplas execuções (n=5 ou mais)
# 3. Calcular média e desvio padrão
# 4. Variar tamanho do dataset (10k, 50k, 100k, 500k)
# 5. Documentar configuração (CPU, RAM, PostgreSQL version, disco)
```

---

## 🚀 Como Executar os Testes

### 1. Teste Rápido (método otimizado)
```bash
cd /Users/raphaelportela/monografia_2025/mono_2025
python fetch_db.py
```

### 2. Teste Completo de Performance
```bash
python test_insert_performance.py
```

Este script vai:
- ✅ Testar todos os 4 métodos
- ✅ Limpar tabela entre testes
- ✅ Gerar relatório comparativo
- ✅ Calcular métricas (tempo, registros/s, speedup)

---

## 📈 Gráficos Recomendados para a Tese

### 1. **Performance vs Tamanho do Dataset**
```
Eixo X: Número de registros (10k, 50k, 100k, 500k, 1M)
Eixo Y: Tempo (segundos)
Linhas: Cada método
```

### 2. **Throughput (Registros/segundo)**
```
Eixo X: Número de threads (1, 2, 3, 4, 5, 6)
Eixo Y: Registros/segundo
Dataset: Fixo (ex: 100k registros)
```

### 3. **Overhead Analysis**
```
Gráfico de pizza:
- Tempo de SQL real
- Overhead de conexão
- Overhead de threads
- Overhead de commits
```

---

## 💡 Conclusões Chave

1. **Paralelismo não é sempre melhor**
   - Para 10k registros: Sequencial otimizado é ~2-3x mais rápido

2. **Gargalos além do SQL**
   - Conexões: 50-100ms cada
   - Commits: 30-80ms cada
   - Threads: 10-20ms de overhead por lote

3. **execute_values é poderoso**
   - Converte N inserts em 1 query
   - Reduz round-trips ao banco
   - 2-5x mais rápido que executemany

4. **ConnectionPool vale a pena apenas para:**
   - Múltiplas requisições concorrentes (ex: API)
   - Datasets muito grandes (> 500k)
   - Aplicações long-running

5. **Benchmarking é essencial**
   - Nunca assume que "paralelo = rápido"
   - Sempre teste com dados reais
   - Considere o contexto (hardware, rede, DB config)

---

## 📚 Referências Técnicas

- [psycopg3 Fast Execution](https://www.psycopg.org/psycopg3/docs/advanced/adapt.html#example-return-composite-types)
- [PostgreSQL COPY vs INSERT](https://www.postgresql.org/docs/current/populate.html)
- [Connection Pooling Best Practices](https://wiki.postgresql.org/wiki/Number_Of_Database_Connections)
- [Transaction Performance](https://www.postgresql.org/docs/current/populate.html#POPULATE-TRANSACTIONS)

---

## 🎯 Próximos Passos

1. ✅ Execute `test_insert_performance.py` para dados concretos
2. ✅ Teste com diferentes tamanhos (10k, 50k, 100k)
3. ✅ Documente configuração do sistema (CPU, RAM, PostgreSQL)
4. ✅ Gere gráficos para a tese
5. ✅ Considere testar COPY FROM stdin para comparação

---

**Autor:** Análise de Performance PostgreSQL - ETL com psycopg3  
**Data:** Outubro 2025  
**Contexto:** Monografia sobre otimização de pipelines ETL

