# Como Executar o ETL

## 📋 Pré-requisitos

```bash
pip install -r requirements.txt
```

Configurar variável de ambiente:
```bash
export DATASET_PATH="/caminho/para/datasetcovid.zip"
```

---

## 🖥️ Execução Local (Sem Limitação)

### Síncrono
```bash
python main.py
```

### Assíncrono
```bash
python main_async.py
```

**Arquivos necessários:**
- `main.py` ou `main_async.py`
- `benchmark.py`
- `fetch_db.py`
- `etl_psycopg3.py`
- `schemas.py`

---

## 🐳 Execução com Limitação (Docker 4GB)

### Síncrono (SEM Otimização)
```bash
./run_4gb_benchmark.sh
```

### Assíncrono (COM Otimização)
```bash
./run_4gb_benchmark_async.sh
```

**Arquivos necessários:**
- `run_4gb_benchmark.sh` ou `run_4gb_benchmark_async.sh`
- `docker-compose.cloud.yml`
- `Dockerfile.cloud`
- `docker-entrypoint-cloud.sh`
- Todos os arquivos Python mencionados acima

---

## 📊 Gerar Gráfico Resumido

```bash
python create_resumo_comparativo.py
```

---

## 🎯 Resumo

| Ambiente | Comando | Tempo Esperado |
|----------|---------|----------------|
| Local Síncrono | `python main.py` | ~20 min |
| Local Assíncrono | `python main_async.py` | ~16.6 min |
| Docker 4GB Síncrono | `./run_4gb_benchmark.sh` | ~60 min |
| Docker 4GB Assíncrono | `./run_4gb_benchmark_async.sh` | ~38 min |

