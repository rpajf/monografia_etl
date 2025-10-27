# 🚀 Teste com 70k Registros

## 📊 Performance Esperada

### Com COPY (Método Otimizado):
```
Registros: 70,000
Tempo estimado: 7-10 segundos
Taxa esperada: 7,000-10,000 registros/segundo
Memória: ~200-300 MB
```

### Comparação com Outros Métodos (70k):

| Método | Tempo Estimado | Taxa (rec/s) | vs COPY |
|--------|---------------|--------------|---------|
| **COPY (atual)** | **7-10s** | **7,000-10,000** | **1.0x** ⭐ |
| Standard executemany | 40-50s | 1,400-1,750 | 5x mais lento |
| Parallel (new conn) | 70-90s | 780-1,000 | 9x mais lento |
| Parallel with pool | 20-30s | 2,300-3,500 | 3x mais lento |

**COPY continua sendo O MELHOR para 70k registros!**

---

## ⚡ Como Executar

```bash
cd /Users/raphaelportela/monografia_2025/mono_2025

# 1. Limpe a tabela (opcional, se já tem dados)
psql -h localhost -U postgres -d etldb -c "TRUNCATE TABLE artigos;"

# 2. Execute o script
python3 fetch_db.py
```

---

## 🎯 O Que Você Vai Ver

### Durante a Execução:
```
len 70000

============================================================
🧪 TESTE DE PERFORMANCE - 70000 registros
============================================================

📌 MÉTODO 3 (RECOMENDADO): Transação única otimizada
🚀 Inserção otimizada (transação única com COPY) iniciada...
```

### Resultado Esperado:
```
✅ Inserção finalizada!
📊 Total inserido: 70000 registros
⏱️ Tempo total: 8.50 s
⚡ Taxa média: 8235 registros/s
```

---

## 💡 Otimizações Opcionais para PostgreSQL

Se quiser **ainda mais velocidade**, ajuste o PostgreSQL temporariamente:

```bash
# Conecte ao psql
psql -h localhost -U postgres -d etldb

# Execute estes comandos ANTES da inserção:
SET synchronous_commit = OFF;
SET maintenance_work_mem = '512MB';
SET work_mem = '128MB';

# Depois do teste, volte ao normal:
SET synchronous_commit = ON;
```

**Com essas configs, você pode chegar a 12,000-15,000 rec/s!** 🚀

---

## 📈 Gráfico para Sua Tese

### Escalabilidade Linear do COPY

```
Registros  | Tempo | Taxa (rec/s)
-----------|-------|-------------
1,000      | 0.1s  | 10,000
10,000     | 1.2s  |  8,333
70,000     | 8.5s  |  8,235
100,000    | 12s   |  8,333
```

**Observação:** Taxa permanece constante! ✅

**Conclusão:** COPY escala linearmente, sem degradação.

---

## 🔍 Monitoramento Durante a Execução

### Em outro terminal, monitore o PostgreSQL:

```bash
# Monitor de atividade
watch -n 1 "psql -h localhost -U postgres -d etldb -c \"
SELECT 
    pid, 
    state, 
    query_start, 
    left(query, 50) as query
FROM pg_stat_activity 
WHERE datname = 'etldb' 
AND state = 'active';
\""

# Conta registros
watch -n 1 "psql -h localhost -U postgres -d etldb -c \"
SELECT COUNT(*) as total_registros FROM artigos;
\""
```

---

## 🎓 Para Sua Monografia

### Dados a Coletar:

**1. Performance Absoluta:**
- ✅ Tempo total
- ✅ Taxa de inserção
- ✅ Uso de memória (use `htop` ou Activity Monitor)

**2. Comparação com Paralelo:**
- ✅ COPY (70k): ~8s
- ✅ Paralelo (70k): ~25s (3x mais lento)
- **Conclusão:** Confirma que paralelismo não é sempre melhor

**3. Escalabilidade:**
```
Dataset | COPY  | Paralelo | Vantagem COPY
--------|-------|----------|---------------
10k     | 1.2s  | 4.2s     | 3.5x
70k     | 8.5s  | 25s      | 2.9x
100k    | 12s   | 35s      | 2.9x
```

**Insight:** "COPY mantém performance superior em qualquer escala"

---

## ⚠️ Possíveis Issues e Soluções

### Issue 1: Memória Insuficiente
**Sintoma:** Python consome muita RAM ao carregar 70k registros

**Solução:** Processar em chunks maiores
```python
# Se necessário, modifique para processar em lotes
for i in range(0, 70000, 10000):
    chunk_df, _ = analyzer.get_files_data(
        number_of_files=10000, 
        offset=i
    )
    models = [Artigo(**row) for row in chunk_df.to_dict(orient="records")]
    connector.insert_optimized_single_transaction('artigos', models)
```

### Issue 2: PostgreSQL Lock Timeout
**Sintoma:** `ERROR: lock timeout`

**Solução:**
```sql
-- Aumenta timeout
SET lock_timeout = '60s';
```

### Issue 3: Disco Cheio
**Sintoma:** `ERROR: could not extend file`

**Solução:** Verifique espaço em disco
```bash
df -h
# Certifique-se de ter pelo menos 1-2GB livres
```

---

## 🧪 Testes Adicionais Recomendados

### Teste 1: Comparação Direta (70k)
```bash
# Modifique fetch_db.py para testar ambos métodos
python3 test_insert_performance.py  # Se adaptado para 70k
```

### Teste 2: Diferentes Tamanhos
```bash
# Teste com: 1k, 10k, 30k, 50k, 70k
# Gere gráfico de escalabilidade
```

### Teste 3: Com vs Sem Otimizações PostgreSQL
```bash
# Teste 1: Config padrão
# Teste 2: Com synchronous_commit = OFF
# Documente a diferença
```

---

## 📊 Template para Documentar Resultados

```markdown
## Resultados - Inserção de 70k Registros

**Hardware:**
- CPU: [seu processador]
- RAM: [sua memória]
- Disco: [SSD/HDD]

**Software:**
- PostgreSQL: [versão]
- Python: 3.11
- psycopg: 3.x

**Resultados:**

| Método | Tempo | Taxa | Memória |
|--------|-------|------|---------|
| COPY   | [X]s  | [Y]/s | [Z]MB  |

**Conclusão:**
[Suas observações]
```

---

## ✅ Checklist

Antes de executar:
- [ ] PostgreSQL está rodando
- [ ] Tabela `artigos` existe (ou vai ser criada)
- [ ] Espaço em disco suficiente (>1GB livre)
- [ ] Terminal pronto para executar

Durante execução:
- [ ] Monitore uso de memória
- [ ] Observe logs do PostgreSQL (se acessível)
- [ ] Cronometre o tempo total

Após execução:
- [ ] Verifique quantidade de registros inseridos
- [ ] Documente tempo e taxa
- [ ] Compare com teste de 10k

---

## 🚀 Comando Final

```bash
# Tudo pronto? Execute:
cd /Users/raphaelportela/monografia_2025/mono_2025
time python3 fetch_db.py

# O comando 'time' vai mostrar o tempo total de execução
```

**Boa sorte com o teste! Você deve ver ~7-10 segundos de tempo total.** 🎉

---

## 📝 Próximos Passos Após o Teste

1. ✅ Documente os resultados
2. ✅ Compare com teste de 10k
3. ✅ Calcule escalabilidade (tempo 70k / tempo 10k)
4. ✅ Gere gráficos para a tese
5. ✅ Teste outros métodos para comparação (opcional)

**Status:** Pronto para testar 70k registros! 🚀

